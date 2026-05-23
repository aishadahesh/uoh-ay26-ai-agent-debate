"""Factory for runtime LLM providers."""

from __future__ import annotations

import os

from agent_debate.config import Config
from agent_debate.llm.base import Gatekeeper, LLMClient
from agent_debate.llm.mock_client import MockLLMClient


def build_llm_client(config: Config) -> LLMClient:
    """Create the configured LLM client, falling back to mock only when allowed."""

    llm_config = config.llm
    provider = _resolve_provider(llm_config)
    if provider == "mock":
        return MockLLMClient()
    if provider == "gemini" and _valid_env_key("GEMINI_API_KEY"):
        from agent_debate.llm.gemini_client import GeminiClient

        return GeminiClient(
            gatekeeper=_build_gatekeeper(config),
            max_output_tokens=int(llm_config.get("max_output_tokens", 450)),
            temperature=float(llm_config.get("temperature", 0.4)),
        )
    if provider == "openai" and _valid_env_key("OPENAI_API_KEY"):
        from agent_debate.llm.openai_client import OpenAIClient

        return OpenAIClient(
            gatekeeper=_build_gatekeeper(config),
            max_output_tokens=int(llm_config.get("max_output_tokens", 450)),
            temperature=float(llm_config.get("temperature", 0.4)),
        )
    if llm_config.get("mock_when_no_api_key", False):
        return MockLLMClient()
    expected = "GEMINI_API_KEY" if provider == "gemini" else "OPENAI_API_KEY"
    raise RuntimeError(f"{expected} is missing and mock fallback is disabled")


def provider_name(config: Config) -> str:
    """Return the provider that will be selected for this environment."""

    return _resolve_provider(config.llm)


def _resolve_provider(llm_config: dict[str, object]) -> str:
    provider = str(llm_config.get("provider", "auto")).lower()
    if provider != "auto":
        return provider
    preferred = str(llm_config.get("preferred_provider", "gemini")).lower()
    if preferred == "gemini" and _valid_env_key("GEMINI_API_KEY"):
        return "gemini"
    if preferred == "openai" and _valid_env_key("OPENAI_API_KEY"):
        return "openai"
    if _valid_env_key("GEMINI_API_KEY"):
        return "gemini"
    if _valid_env_key("OPENAI_API_KEY"):
        return "openai"
    return "mock"


def _valid_env_key(name: str) -> bool:
    value = os.environ.get(name, "").strip()
    return bool(value and not value.lower().startswith(("your_", "replace_", "paste_")))


def _build_gatekeeper(config: Config) -> Gatekeeper:
    gatekeeper_config = config.raw.get("gatekeeper", {})
    return Gatekeeper(
        max_calls=int(gatekeeper_config.get("max_calls_per_debate", 30)),
        max_input_chars=int(gatekeeper_config.get("max_estimated_input_chars", 90000)),
    )
