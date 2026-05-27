from multiprocessing import Queue

from agent_debate.agents.judge_agent import JudgeAgent, run_judge_agent
from agent_debate.config import load_config
from agent_debate.ipc.messages import Message
from agent_debate.llm.base import LLMProviderError
from agent_debate.llm.mock_client import MockLLMClient
from agent_debate.memory import DebateMemory
from tests.helpers import write_test_config


def _memory_with_arguments() -> DebateMemory:
    memory = DebateMemory()
    memory.write(Message(1, "pro", "judge", "argument", "brief pro claim"))
    memory.write(
        Message(
            1,
            "con",
            "judge",
            "argument",
            "Addressing the opponent with evidence because privacy and access matter.",
        )
    )
    return memory


def test_judge_agent_decides_with_mock_client(tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    decision = JudgeAgent(config, MockLLMClient()).decide(_memory_with_arguments())
    assert decision.type == "decision"
    assert "Winner: Con Agent" in decision.content


def test_judge_agent_falls_back_to_mock_on_provider_error(tmp_path) -> None:
    class FailingLLM:
        def complete(self, prompt, *, model, timeout):
            raise LLMProviderError("quota exhausted")

    config = load_config(write_test_config(tmp_path))
    decision = JudgeAgent(config, FailingLLM()).decide(_memory_with_arguments())
    assert decision.metadata["provider_fallback"] == "mock"
    assert "Winner:" in decision.content


def test_run_judge_agent_reports_error_for_bad_payload(tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    outbox = Queue()
    run_judge_agent(config, [{"sender": "bad"}], outbox)
    message = outbox.get(timeout=1)
    assert message["type"] == "error"
