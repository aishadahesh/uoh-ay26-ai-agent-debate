"""Parent process orchestration for the debate."""

from __future__ import annotations

from contextlib import suppress
from multiprocessing import Process, Queue
from queue import Empty

from agent_debate.agents.debate_agent import DebateAgent, run_debate_agent
from agent_debate.agents.judge_agent import JudgeAgent
from agent_debate.config import Config
from agent_debate.ipc.messages import Message
from agent_debate.ipc.queues import MessageRouter
from agent_debate.llm.base import LLMClient
from agent_debate.logging_utils.debate_logger import DebateLogger
from agent_debate.memory import DebateMemory
from agent_debate.orchestration.watchdog import Watchdog
from agent_debate.tools.web_search import WebSearchTool


class DebateOrchestrator:
    """Creates child processes, routes messages, and asks the judge to decide."""

    def __init__(self, config: Config, llm: LLMClient) -> None:
        self.config = config
        self.llm = llm
        self.memory = DebateMemory()
        self.logger = DebateLogger(config)
        watchdog_config = config.watchdog
        self.watchdog = Watchdog(
            float(watchdog_config["response_timeout_seconds"]),
            int(watchdog_config["restart_attempts"]),
        )
        self.parent_queue: Queue = Queue()
        self.child_queues = {"pro": Queue(), "con": Queue()}
        self.router = MessageRouter(
            {"pro": self.child_queues["pro"], "con": self.child_queues["con"]}
        )
        search_config = config.raw["web_search"]
        self.search = WebSearchTool(
            bool(search_config["enabled"]),
            float(search_config["timeout_seconds"]),
            int(search_config["max_results"]),
        )
        self.processes: dict[str, Process] = {}

    def run(self) -> Message:
        """Run the full turn-taking debate and return the judge decision."""

        self.logger.reset()
        self._start_children()
        previous_argument = ""
        try:
            for round_number in range(1, self.config.turns_per_side + 1):
                previous_argument = self._take_turn("pro", round_number, previous_argument)
                previous_argument = self._take_turn("con", round_number, previous_argument)
            decision = JudgeAgent(self.config, self.llm).decide(self.memory)
            self._record(decision)
            return decision
        finally:
            self._stop_children()

    def _start_children(self) -> None:
        for role in ["pro", "con"]:
            agent_config = self.config.agent(role)
            agent = DebateAgent(
                role=role,
                stance=agent_config["stance"],
                model=agent_config["model"],
                inbox=self.child_queues[role],
                outbox=self.parent_queue,
                config=self.config,
                llm=None,
                search=self.search,
                timeout=float(self.config.llm["timeout_seconds"]),
            )
            process = Process(target=run_debate_agent, args=(agent,), name=f"{role}-agent")
            process.start()
            self.processes[role] = process

    def _take_turn(self, role: str, round_number: int, previous_argument: str) -> str:
        self.watchdog.ensure_alive(role, self.processes[role])
        request = Message(
            round=round_number,
            sender="judge",
            receiver=role,
            type="instruction",
            content=f"Round {round_number}: present your argument and rebut the prior point.",
            metadata={
                "topic": self.config.topic,
                "rules": self.config.raw["debate_rules"],
                "previous_argument": previous_argument,
                "summary": self.memory.summary,
            },
        )
        self.router.route(request)
        response = self._receive_child(role)
        self._record(response)
        return response.content

    def _receive_child(self, role: str) -> Message:
        try:
            payload = self.parent_queue.get(timeout=self.watchdog.response_timeout)
        except Empty as exc:
            raise TimeoutError(f"{role} did not respond before watchdog timeout") from exc
        message = Message.from_dict(payload)
        if message.sender != role or message.receiver != "judge":
            raise RuntimeError(f"unexpected route from child: {message.to_dict()}")
        if message.type == "error":
            raise RuntimeError(f"{role} failed: {message.content}")
        return message

    def _record(self, message: Message) -> None:
        self.memory.write(message)
        self.logger.log(message)

    def _stop_children(self) -> None:
        for role in ["pro", "con"]:
            with suppress(KeyError, ValueError):
                self.router.route(Message(0, "judge", role, "stop", "Stop."))
        for process in self.processes.values():
            process.join(timeout=2)
            if process.is_alive():
                process.terminate()
                process.join(timeout=2)
