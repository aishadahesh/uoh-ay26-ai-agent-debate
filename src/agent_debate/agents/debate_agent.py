"""Child debate agent process implementation."""

from __future__ import annotations

import warnings
from multiprocessing import Queue

from agent_debate.agents.base import BaseAgent
from agent_debate.config import Config
from agent_debate.ipc.messages import Message
from agent_debate.llm.base import LLMClient, LLMProviderError
from agent_debate.llm.factory import build_llm_client
from agent_debate.llm.mock_client import MockLLMClient
from agent_debate.memory import PromptBuilder
from agent_debate.tools.web_search import WebSearchTool


class DebateAgent(BaseAgent):
    """Pro or con child agent. It only talks to the judge queue."""

    def __init__(
        self,
        role: str,
        stance: str,
        model: str,
        inbox: Queue,
        outbox: Queue,
        config: Config,
        llm: LLMClient | None,
        search: WebSearchTool,
        timeout: float,
    ) -> None:
        super().__init__(role, inbox, outbox)
        self.stance = stance
        self.model = model
        self.config = config
        self.llm = llm
        self.search = search
        self.timeout = timeout
        self.prompts = PromptBuilder()

    def run(self) -> None:
        """Main process loop."""

        llm = self.llm or build_llm_client(self.config)
        while True:
            request = self.receive(self.timeout)
            if request.type == "stop":
                return
            evidence = self.search.search(f"{request.metadata['topic']} {self.stance}")
            prompt = self.prompts.child_prompt(
                role=self.role,
                stance=self.stance,
                topic=request.metadata["topic"],
                rules=request.metadata["rules"],
                previous_argument=request.metadata.get("previous_argument", ""),
                summary=request.metadata.get("summary", ""),
                instruction=request.content,
                evidence=[item.url for item in evidence],
            )
            metadata = {}
            try:
                result = llm.complete(prompt, model=self.model, timeout=self.timeout)
            except LLMProviderError as exc:
                if not self.config.llm.get("fallback_to_mock_on_provider_error", False):
                    self._send_error(request, exc)
                    continue
                result = MockLLMClient().complete(prompt, model="mock", timeout=self.timeout)
                metadata = {"provider_fallback": "mock", "provider_error": str(exc)}
            sources = result.sources or [item.url for item in evidence]
            self.send(
                Message(
                    round=request.round,
                    sender=self.role,
                    receiver="judge",
                    type="argument",
                    content=result.content,
                    sources=sources,
                    metadata=metadata,
                )
            )

    def _send_error(self, request: Message, error: Exception) -> None:
        self.send(
            Message(
                round=request.round,
                sender=self.role,
                receiver="judge",
                type="error",
                content=str(error),
            )
        )


def run_debate_agent(agent: DebateAgent) -> None:
    """Pickle-friendly multiprocessing target."""

    warnings.filterwarnings("ignore", category=FutureWarning, module=r"google\..*")
    agent.run()
