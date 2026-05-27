"""Judge agent logic for final evaluation."""

from __future__ import annotations

from multiprocessing import Queue

from agent_debate.config import Config
from agent_debate.ipc.messages import Message
from agent_debate.llm.base import LLMClient, LLMProviderError
from agent_debate.llm.factory import build_llm_client
from agent_debate.llm.mock_client import MockLLMClient
from agent_debate.memory import DebateMemory, PromptBuilder


class JudgeAgent:
    """Agent that evaluates the debate and decides the winner."""

    def __init__(self, config: Config, llm: LLMClient) -> None:
        self.config = config
        self.llm = llm
        self.prompts = PromptBuilder()
        self.model = config.agent("judge")["model"]

    def decide(self, memory: DebateMemory) -> Message:
        """Create a no-tie final decision."""

        latest_pro = memory.latest_from("pro")
        latest_con = memory.latest_from("con")
        prompt = self.prompts.judge_prompt(
            topic=self.config.topic,
            rules=self.config.raw["debate_rules"],
            latest_pro=latest_pro.content if latest_pro else "",
            latest_con=latest_con.content if latest_con else "",
            summary=memory.summary,
            scoring=self.config.raw["scoring"],
            round_number=self.config.turns_per_side,
            final=True,
        )
        metadata = {}
        try:
            result = self.llm.complete(
                prompt,
                model=self.model,
                timeout=float(self.config.llm["timeout_seconds"]),
            )
        except LLMProviderError as exc:
            if not self.config.llm.get("fallback_to_mock_on_provider_error", False):
                raise
            result = MockLLMClient().complete(
                prompt,
                model="mock",
                timeout=float(self.config.llm["timeout_seconds"]),
            )
            metadata = {"provider_fallback": "mock", "provider_error": str(exc)}
        return Message(
            round=self.config.turns_per_side,
            sender="judge",
            receiver="system",
            type="decision",
            content=result.content,
            sources=result.sources,
            metadata=metadata,
        )


def run_judge_agent(
    config: Config,
    message_payloads: list[dict[str, object]],
    outbox: Queue,
) -> None:
    """Pickle-friendly multiprocessing target for the judge agent."""

    try:
        memory = DebateMemory()
        for payload in message_payloads:
            memory.write(Message.from_dict(payload))
        decision = JudgeAgent(config, build_llm_client(config, "judge")).decide(memory)
    except Exception as exc:
        decision = Message(
            round=config.turns_per_side,
            sender="judge",
            receiver="system",
            type="error",
            content=str(exc),
        )
    outbox.put(decision.to_dict())
