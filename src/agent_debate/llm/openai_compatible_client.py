"""OpenAI-compatible Chat Completions clients for third-party providers."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from openai import APIError, OpenAI, OpenAIError, RateLimitError

from agent_debate.llm.base import Gatekeeper, LLMProviderError, LLMResult


class OpenAICompatibleChatClient:
    """Chat Completions wrapper for providers that expose an OpenAI-compatible API."""

    def __init__(
        self,
        *,
        provider_name: str,
        api_key_env: str,
        base_url: str,
        gatekeeper: Gatekeeper,
        max_output_tokens: int,
        temperature: float,
    ) -> None:
        self.provider_name = provider_name
        self.api_key_env = api_key_env
        self.client = OpenAI(api_key=os.environ.get(api_key_env), base_url=base_url)
        self.gatekeeper = gatekeeper
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature

    def complete(self, prompt: str, *, model: str, timeout: float) -> LLMResult:
        self.gatekeeper.check(prompt)

        def call() -> str:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_output_tokens,
                timeout=timeout,
            )
            message = response.choices[0].message.content
            return message or ""

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(call)
            try:
                return LLMResult(content=future.result(timeout=timeout), sources=[])
            except TimeoutError as exc:
                future.cancel()
                raise LLMProviderError(
                    f"{self.provider_name} call exceeded {timeout} seconds"
                ) from exc
            except RateLimitError as exc:
                raise LLMProviderError(
                    f"{self.provider_name} quota/rate limit error. "
                    "Check account limits, free-tier quota, or try a smaller model."
                ) from exc
            except APIError as exc:
                error = _truncate_error(f"{self.provider_name} API error: {exc}")
                raise LLMProviderError(error) from exc
            except OpenAIError as exc:
                raise LLMProviderError(
                    _truncate_error(f"{self.provider_name} provider error: {exc}")
                ) from exc


class GroqClient(OpenAICompatibleChatClient):
    """Groq API wrapper using the OpenAI-compatible endpoint."""

    def __init__(self, gatekeeper: Gatekeeper, max_output_tokens: int, temperature: float) -> None:
        super().__init__(
            provider_name="Groq",
            api_key_env="GROQ_API_KEY",
            base_url="https://api.groq.com/openai/v1",
            gatekeeper=gatekeeper,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )


class MistralClient(OpenAICompatibleChatClient):
    """Mistral API wrapper using the OpenAI-compatible endpoint."""

    def __init__(self, gatekeeper: Gatekeeper, max_output_tokens: int, temperature: float) -> None:
        super().__init__(
            provider_name="Mistral",
            api_key_env="MISTRAL_API_KEY",
            base_url="https://api.mistral.ai/v1",
            gatekeeper=gatekeeper,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )


def _truncate_error(error: str, limit: int = 240) -> str:
    return error if len(error) <= limit else f"{error[:limit].rstrip()}..."
