from multiprocessing import Queue

import pytest

from agent_debate.agents.base import BaseAgent
from agent_debate.agents.debate_agent import DebateAgent
from agent_debate.config import load_config
from agent_debate.ipc.messages import Message
from agent_debate.llm.base import LLMProviderError
from agent_debate.llm.mock_client import MockLLMClient
from agent_debate.tools.web_search import WebSearchTool
from tests.helpers import write_test_config


def test_base_agent_receive_timeout() -> None:
    agent = BaseAgent("pro", Queue(), Queue())
    with pytest.raises(TimeoutError, match="timed out"):
        agent.receive(0.01)


def test_debate_agent_processes_instruction_and_stop(tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    inbox = Queue()
    outbox = Queue()
    agent = DebateAgent(
        role="pro",
        stance="Support the topic",
        model="mock-model",
        inbox=inbox,
        outbox=outbox,
        config=config,
        llm=MockLLMClient(),
        search=WebSearchTool(enabled=False, timeout=0.1, max_results=1),
        timeout=1,
    )
    inbox.put(
        Message(
            1,
            "judge",
            "pro",
            "instruction",
            "Speak",
            metadata={
                "topic": config.topic,
                "rules": config.raw["debate_rules"],
                "previous_argument": "Previous",
                "summary": "Summary",
            },
        ).to_dict()
    )
    inbox.put(Message(1, "judge", "pro", "stop", "Stop").to_dict())
    agent.run()
    assert outbox.get(timeout=1)["sender"] == "pro"


def test_debate_agent_falls_back_to_mock_on_provider_error(tmp_path) -> None:
    class FailingLLM:
        def complete(self, prompt, *, model, timeout):
            raise LLMProviderError("quota exhausted")

    config = load_config(write_test_config(tmp_path)).with_topic("pilates or yoga")
    inbox = Queue()
    outbox = Queue()
    agent = DebateAgent(
        role="pro",
        stance=config.agent("pro")["stance"],
        model="mock-model",
        inbox=inbox,
        outbox=outbox,
        config=config,
        llm=FailingLLM(),
        search=WebSearchTool(enabled=False, timeout=0.1, max_results=1),
        timeout=1,
    )
    inbox.put(
        Message(
            1,
            "judge",
            "pro",
            "instruction",
            "Speak",
            metadata={
                "topic": config.topic,
                "rules": config.raw["debate_rules"],
                "previous_argument": "",
                "summary": "Summary",
            },
        ).to_dict()
    )
    inbox.put(Message(1, "judge", "pro", "stop", "Stop").to_dict())
    agent.run()
    response = outbox.get(timeout=1)
    assert response["metadata"]["provider_fallback"] == "mock"
    assert "Pilates" in response["content"]
