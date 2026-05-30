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
from tests.helpers import write_test_config


def test_factory_builds_mock_client(tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    assert isinstance(build_llm_client(config), MockLLMClient)


def test_provider_auto_prefers_gemini_key(monkeypatch, tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    config.raw["llm"]["provider"] = "auto"
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    assert provider_name(config) == "gemini"


def test_provider_auto_ignores_placeholder_gemini_key(monkeypatch, tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    config.raw["llm"]["provider"] = "auto"
    monkeypatch.setenv("GEMINI_API_KEY", "your_google_ai_studio_key")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    assert provider_name(config) == "mock"
    assert not _valid_env_key("GEMINI_API_KEY")


def test_provider_auto_uses_openai_when_only_openai_key_exists(monkeypatch, tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    config.raw["llm"]["provider"] = "auto"
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    assert provider_name(config) == "openai"


def test_provider_auto_uses_groq_when_only_groq_key_exists(monkeypatch, tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    config.raw["llm"]["provider"] = "auto"
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    assert provider_name(config) == "groq"


def test_provider_auto_prefers_openai_over_mistral(monkeypatch, tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    config.raw["llm"]["provider"] = "auto"
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    assert provider_name(config) == "openai"


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
    config.raw["agents"]["con"]["provider"] = "openai"
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    assert provider_names_by_role(config) == {
        "judge": "gemini",
        "pro": "groq",
        "con": "openai",
    }


def test_role_provider_missing_key_uses_mock_when_allowed(monkeypatch, tmp_path) -> None:
    config = load_config(write_test_config(tmp_path))
    config.raw["agents"]["pro"]["provider"] = "groq"
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert provider_name(config, "pro") == "mock"


def test_gatekeeper_blocks_call_budget() -> None:
    gatekeeper = Gatekeeper(max_calls=1, max_input_chars=100)
    gatekeeper.check("first")
    with pytest.raises(RuntimeError, match="budget"):
        gatekeeper.check("second")
