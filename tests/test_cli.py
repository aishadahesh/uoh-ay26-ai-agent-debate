import agent_debate.cli as cli
from agent_debate.cli import (
    main,
    run_debate,
    save_last_transcript,
    show_last_transcript,
    validate_config,
)
from tests.helpers import write_test_config


def test_cli_validate_config_outputs_ping_count(tmp_path, capsys) -> None:
    validate_config(write_test_config(tmp_path))
    assert "2 total pings" in capsys.readouterr().out


def test_cli_run_debate_and_show_transcript(tmp_path, capsys) -> None:
    config_path = write_test_config(tmp_path)
    run_debate(config_path, topic="Runtime topic")
    show_last_transcript(config_path)
    output = capsys.readouterr().out
    assert "Final decision" in output
    assert "Winner:" in output


def test_cli_save_last_transcript_outputs_saved_path(tmp_path, capsys) -> None:
    config_path = write_test_config(tmp_path)
    run_debate(config_path, topic="Runtime topic")
    saved_path = save_last_transcript(config_path)
    output = capsys.readouterr().out
    assert "Transcript saved to:" in output
    assert saved_path.exists()


def test_cli_prints_clean_failure(monkeypatch, tmp_path, capsys) -> None:
    class FailingOrchestrator:
        def __init__(self, config, llm) -> None:
            return None

        def run(self):
            raise RuntimeError("pro failed: quota")

    monkeypatch.setattr(cli, "DebateOrchestrator", FailingOrchestrator)
    run_debate(write_test_config(tmp_path), topic="Runtime topic")
    output = capsys.readouterr().out
    assert "Debate failed: pro failed: quota" in output


def test_cli_prints_single_fallback_notice(monkeypatch, tmp_path, capsys) -> None:
    class Decision:
        content = "Winner: Pro Agent"
        metadata = {"provider_fallback": "mock", "provider_error": "Gemini API error"}

    class FallbackOrchestrator:
        def __init__(self, config, llm) -> None:
            return None

        def run(self):
            return Decision()

    monkeypatch.setattr(cli, "DebateOrchestrator", FallbackOrchestrator)
    run_debate(write_test_config(tmp_path), topic="Runtime topic")
    output = capsys.readouterr().out
    assert output.count("mock fallback") == 1
    assert "Gemini failed" in output


def test_cli_truncates_long_provider_error(monkeypatch, tmp_path, capsys) -> None:
    class Decision:
        content = "Winner: Pro Agent"
        metadata = {"provider_fallback": "mock", "provider_error": f"Gemini {'x' * 500}"}

    class FallbackOrchestrator:
        def __init__(self, config, llm) -> None:
            return None

        def run(self):
            return Decision()

    monkeypatch.setattr(cli, "DebateOrchestrator", FallbackOrchestrator)
    run_debate(write_test_config(tmp_path), topic="Runtime topic")
    output = capsys.readouterr().out
    assert "..." in output
    assert len(output) < 700


def test_cli_menu_handles_validate_invalid_and_exit(monkeypatch, capsys) -> None:
    calls = []
    answers = iter(["4", "bad", "5"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    monkeypatch.setattr(cli, "validate_config", lambda: calls.append("validated"))
    main()
    output = capsys.readouterr().out
    assert calls == ["validated"]
    assert "Invalid choice." in output


def test_cli_menu_handles_save_without_transcript(monkeypatch, capsys) -> None:
    answers = iter(["3", "5"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    monkeypatch.setattr(
        cli,
        "save_last_transcript",
        lambda: (_ for _ in ()).throw(FileNotFoundError("Run a debate first.")),
    )
    main()
    assert "Run a debate first." in capsys.readouterr().out
