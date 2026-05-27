"""Factory for runtime LLM providers."""

from __future__ import annotations

import os

from agent_debate.config import Config
from agent_debate.llm.base import Gatekeeper, LLMClient
from agent_debate.llm.mock_client import MockLLMClient

PROVIDER_ENV_KEYS = {
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "openai": "OPENAI_API_KEY",
}


def build_llm_client(config: Config, role: str | None = None) -> LLMClient:
    """Create the configured LLM client, falling back to mock only when allowed."""

    llm_config = config.llm
    provider = _resolve_provider(config, role)
    if provider == "mock":
        return MockLLMClient()
    if provider == "gemini" and _valid_env_key("GEMINI_API_KEY"):
        from agent_debate.llm.gemini_client import GeminiClient

        return GeminiClient(
            gatekeeper=_build_gatekeeper(config),
            max_output_tokens=int(llm_config.get("max_output_tokens", 450)),
            temperature=float(llm_config.get("temperature", 0.4)),
        )
    if provider == "groq" and _valid_env_key("GROQ_API_KEY"):
        from agent_debate.llm.openai_compatible_client import GroqClient

        return GroqClient(
            gatekeeper=_build_gatekeeper(config),
            max_output_tokens=int(llm_config.get("max_output_tokens", 450)),
            temperature=float(llm_config.get("temperature", 0.4)),
        )
    if provider == "mistral" and _valid_env_key("MISTRAL_API_KEY"):
        from agent_debate.llm.openai_compatible_client import MistralClient

        return MistralClient(
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
    expected = PROVIDER_ENV_KEYS.get(provider, f"{provider.upper()}_API_KEY")
    raise RuntimeError(f"{expected} is missing and mock fallback is disabled")


def provider_name(config: Config, role: str | None = None) -> str:
    """Return the provider that will be selected for this environment."""

    return _resolve_provider(config, role)


def provider_names_by_role(config: Config) -> dict[str, str]:
    """Return selected provider names for judge, pro, and con."""

    return {role: provider_name(config, role) for role in ["judge", "pro", "con"]}


def _resolve_provider(config: Config, role: str | None = None) -> str:
    llm_config = config.llm
    if role:
        agent_provider = str(config.agent(role).get("provider", "")).lower()
        if agent_provider:
            if agent_provider == "auto":
                return _resolve_auto_provider(llm_config)
            if agent_provider != "mock":
                key_name = PROVIDER_ENV_KEYS.get(agent_provider)
                if key_name and not _valid_env_key(key_name) and llm_config.get(
                    "mock_when_no_api_key", False
                ):
                    return "mock"
            return agent_provider
    provider = str(llm_config.get("provider", "auto")).lower()
    if provider != "auto":
        return provider
    return _resolve_auto_provider(llm_config)


def _resolve_auto_provider(llm_config: dict[str, object]) -> str:
    preferred = str(llm_config.get("preferred_provider", "gemini")).lower()
    if preferred == "gemini" and _valid_env_key("GEMINI_API_KEY"):
        return "gemini"
    if preferred == "groq" and _valid_env_key("GROQ_API_KEY"):
        return "groq"
    if preferred == "openai" and _valid_env_key("OPENAI_API_KEY"):
        return "openai"
    if preferred == "mistral" and _valid_env_key("MISTRAL_API_KEY"):
        return "mistral"
    if _valid_env_key("GEMINI_API_KEY"):
        return "gemini"
    if _valid_env_key("GROQ_API_KEY"):
        return "groq"
    if _valid_env_key("OPENAI_API_KEY"):
        return "openai"
    if _valid_env_key("MISTRAL_API_KEY"):
        return "mistral"
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
