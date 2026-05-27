import pytest

from agent_debate.config import load_config
from agent_debate.llm.base import Gatekeeper
from agent_debate.llm.factory import (
    _valid_env_key,
    build_llm_client,
    provider_name,
    provider_names_by_role,
)
from agent_debate.llm.mock_client import MockLLMClient
from agent_debate.tools.web_search import WebSearchTool
from tests.helpers import write_test_config


def test_factory_builds_mock_client(tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    assert isinstance(build_llm_client(config), MockLLMClient)


def test_provider_auto_prefers_gemini_key(monkeypatch, tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    config.raw["llm"]["provider"] = "auto"
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert provider_name(config) == "gemini"


def test_provider_auto_ignores_placeholder_gemini_key(monkeypatch, tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    config.raw["llm"]["provider"] = "auto"
    monkeypatch.setenv("GEMINI_API_KEY", "your_google_ai_studio_key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert provider_name(config) == "mock"
    assert not _valid_env_key("GEMINI_API_KEY")


def test_provider_auto_uses_openai_when_only_openai_key_exists(monkeypatch, tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    config.raw["llm"]["provider"] = "auto"
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    assert provider_name(config) == "openai"


def test_provider_auto_uses_groq_when_only_groq_key_exists(monkeypatch, tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    config.raw["llm"]["provider"] = "auto"
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    assert provider_name(config) == "groq"


def test_provider_auto_uses_mistral_when_only_mistral_key_exists(monkeypatch, tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    config.raw["llm"]["provider"] = "auto"
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    assert provider_name(config) == "mistral"


def test_provider_names_follow_agent_role_config(monkeypatch, tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    config.raw["agents"]["judge"]["provider"] = "gemini"
    config.raw["agents"]["pro"]["provider"] = "groq"
    config.raw["agents"]["con"]["provider"] = "mistral"
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    assert provider_names_by_role(config) == {
        "judge": "gemini",
        "pro": "groq",
        "con": "mistral",
    }


def test_role_provider_missing_key_uses_mock_when_allowed(monkeypatch, tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    config.raw["agents"]["pro"]["provider"] = "groq"
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert provider_name(config, "pro") == "mock"


def test_mock_client_generates_role_and_round_specific_text() -> None:
    client = MockLLMClient()
    pro = client.complete(
        "You are the pro debate agent. Stance: Argue that Pilates is better than Yoga.\n"
        "Topic: Pilates is better than Yoga.\nCurrent judge instruction: Round 2:",
        model="mock",
        timeout=1,
    )
    con = client.complete(
        "You are the con debate agent. Stance: Argue that Yoga is better than Pilates.\n"
        "Topic: Pilates is better than Yoga.\nCurrent judge instruction: Round 2:",
        model="mock",
        timeout=1,
    )
    assert "Pro round 2" in pro.content
    assert "Con round 2" in con.content
    assert "Pilates" in pro.content
    assert "Yoga" in con.content
    assert "software" not in pro.content.lower()
    assert pro.content != con.content


def test_mock_client_generates_default_topic_specific_text() -> None:
    client = MockLLMClient()
    pro = client.complete(
        "You are the pro debate agent. Stance: Support the proposition.\n"
        "Topic: Should universities require students to use AI agents in software "
        "engineering courses.\nCurrent judge instruction: Round 1:",
        model="mock",
        timeout=1,
    )
    con = client.complete(
        "You are the con debate agent. Stance: Oppose the proposition.\n"
        "Topic: Should universities require students to use AI agents in software "
        "engineering courses.\nCurrent judge instruction: Round 1:",
        model="mock",
        timeout=1,
    )
    assert "AI agents" in pro.content
    assert "fundamentals" in con.content
    assert "the proposition better satisfies" not in pro.content


def test_mock_judge_scores_latest_arguments_not_fixed_pro_win() -> None:
    client = MockLLMClient()
    result = client.complete(
        "FINAL DECISION: choose one winner; no tie allowed.\n"
        "Topic: Test topic\n"
        "Latest pro: brief claim.\n"
        "Latest con: Addressing the opponent directly, this argument gives specific "
        "evidence because privacy, access, testing, risk, criteria, and rebuttal all "
        "matter for the selected topic.\n"
        "Scoring criteria: {'persuasion': 35}",
        model="mock",
        timeout=1,
    )
    assert "Winner: Con Agent" in result.content
    assert "Score: Pro 62, Con" in result.content


def test_gatekeeper_blocks_call_budget() -> None:
    gatekeeper = Gatekeeper(max_calls=1, max_input_chars=100)
    gatekeeper.check("first")
    with pytest.raises(RuntimeError, match="budget"):
        gatekeeper.check("second")


def test_web_search_disabled_returns_no_sources() -> None:
    assert WebSearchTool(enabled=False, timeout=0.1, max_results=1).search("anything") == []


def test_web_search_parses_html_results(monkeypatch) -> None:
    class Response:
        text = '<a rel="nofollow" class="result__a" href="https://example.com">Example</a>'

        def raise_for_status(self) -> None:
            return None

    class Requests:
        @staticmethod
        def get(url, timeout, headers):
            return Response()

    monkeypatch.setitem(__import__("sys").modules, "requests", Requests)
    results = WebSearchTool(enabled=True, timeout=0.1, max_results=1).search("query")
    assert results[0].url == "https://example.com"
