"""OpenAI implementation of the provider-neutral LLM client."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from openai import APIError, OpenAI, OpenAIError, RateLimitError

from agent_debate.llm.base import Gatekeeper, LLMProviderError, LLMResult


class OpenAIClient:
    """OpenAI Responses API wrapper with explicit timeout and budget checks."""

    def __init__(self, gatekeeper: Gatekeeper, max_output_tokens: int, temperature: float) -> None:
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.gatekeeper = gatekeeper
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature

    def complete(self, prompt: str, *, model: str, timeout: float) -> LLMResult:
        self.gatekeeper.check(prompt)

        def call() -> str:
            response = self.client.responses.create(
                model=model,
                input=prompt,
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
                timeout=timeout,
            )
            return response.output_text

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(call)
            try:
                return LLMResult(content=future.result(timeout=timeout), sources=[])
            except TimeoutError as exc:
                future.cancel()
                raise LLMProviderError(f"OpenAI call exceeded {timeout} seconds") from exc
            except RateLimitError as exc:
                raise LLMProviderError(
                    "OpenAI quota/rate limit error. Check billing, credits, and usage limits."
                ) from exc
            except APIError as exc:
                raise LLMProviderError(f"OpenAI API error: {exc}") from exc
            except OpenAIError as exc:
                raise LLMProviderError(f"OpenAI provider error: {exc}") from exc
