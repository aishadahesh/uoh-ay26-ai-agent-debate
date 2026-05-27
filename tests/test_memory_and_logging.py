from agent_debate.config import load_config
from agent_debate.ipc.messages import Message
from agent_debate.logging_utils.debate_logger import DebateLogger
from agent_debate.memory import DebateMemory, PromptBuilder
from tests.helpers import write_test_config


def test_memory_updates_compact_summary_without_losing_full_message() -> None:
    memory = DebateMemory()
    message = Message(1, "pro", "judge", "argument", "A focused argument")
    memory.write(message)
    assert memory.latest_from("pro") == message
    assert "Latest pro point" in memory.summary


def test_prompt_builder_selects_compact_child_context() -> None:
    prompt = PromptBuilder().child_prompt(
        role="pro",
        stance="Support the topic",
        topic="Topic",
        rules={"require_rebuttal": True},
        previous_argument="Previous con point",
        summary="Short summary",
        instruction="Speak now",
        evidence=["https://example.com"],
    )
    assert "Previous con point" in prompt
    assert "Short summary" in prompt


def test_logger_writes_jsonl_and_transcript(tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    logger = DebateLogger(config)
    logger.log(Message(1, "pro", "judge", "argument", "Hello", ["https://example.com"]))
    transcript = logger.last_transcript()
    assert "pro LLM: Pro Agent (mock/mock-model)" in transcript
    assert "Hello" in transcript
    assert (tmp_path / "logs" / "debate.jsonl").exists()


def test_logger_reset_clears_previous_transcript(tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    logger = DebateLogger(config)
    logger.log(Message(1, "pro", "judge", "argument", "Old"))
    logger.reset()
    assert logger.last_transcript() == ""


def test_logger_exports_transcript_to_requested_path(tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    logger = DebateLogger(config)
    logger.log(Message(1, "pro", "judge", "argument", "Saved"))
    export_path = logger.export_transcript(tmp_path / "exports" / "saved.txt")
    assert export_path.read_text(encoding="utf-8").startswith("[round 1] pro LLM")


def test_logger_export_fails_without_transcript(tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    logger = DebateLogger(config)
    logger.reset()
    try:
        logger.export_transcript()
    except FileNotFoundError as exc:
        assert "Run a debate first" in str(exc)
    else:
        raise AssertionError("export_transcript should fail without a transcript")
