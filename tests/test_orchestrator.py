from agent_debate.config import load_config
from agent_debate.ipc.messages import Message
from agent_debate.llm.factory import build_llm_client
from agent_debate.orchestration.debate_orchestrator import DebateOrchestrator
from tests.helpers import write_test_config


def test_orchestrator_runs_mock_debate_and_logs_decision(tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    decision = DebateOrchestrator(config, build_llm_client(config)).run()
    assert decision.type == "decision"
    assert "Winner:" in decision.content
    assert (tmp_path / "logs" / "transcript.txt").exists()


def test_orchestrator_turn_error_message_becomes_runtime_error(tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    orchestrator = DebateOrchestrator(config, build_llm_client(config))
    orchestrator.parent_queue.put(Message(1, "pro", "judge", "error", "quota").to_dict())
    try:
        orchestrator._receive_child("pro")
    except RuntimeError as exc:
        assert "pro failed: quota" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")
