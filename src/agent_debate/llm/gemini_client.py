"""Gemini implementation of the provider-neutral LLM client."""

from __future__ import annotations

import os
import re
import warnings
from concurrent.futures import ThreadPoolExecutor, TimeoutError

warnings.filterwarnings("ignore", category=FutureWarning, module=r"google\..*")

from google import genai  # noqa: E402
from google.genai import errors, types  # noqa: E402

from agent_debate.llm.base import Gatekeeper, LLMProviderError, LLMResult  # noqa: E402


class GeminiClient:
    """Google Gemini API wrapper with timeout and budget checks."""

    def __init__(self, gatekeeper: Gatekeeper, max_output_tokens: int, temperature: float) -> None:
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.gatekeeper = gatekeeper
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature

    def complete(self, prompt: str, *, model: str, timeout: float) -> LLMResult:
        self.gatekeeper.check(prompt)

        def call() -> str:
            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_output_tokens,
                ),
            )
            return response.text or ""

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(call)
            try:
                return LLMResult(content=future.result(timeout=timeout), sources=[])
            except TimeoutError as exc:
                future.cancel()
                raise LLMProviderError(f"Gemini call exceeded {timeout} seconds") from exc
            except errors.APIError as exc:
                raise LLMProviderError(_friendly_gemini_error(str(exc), model)) from exc
            except Exception as exc:
                raise LLMProviderError(_truncate_error(f"Gemini provider error: {exc}")) from exc


def _friendly_gemini_error(error: str, model: str) -> str:
    """Compress verbose Gemini API errors into a terminal-friendly message."""

    lowered = error.lower()
    if "resource_exhausted" in lowered or "quota" in lowered or "429" in lowered:
        retry = _extract_retry_delay(error)
        retry_text = f" Retry in about {retry}." if retry else ""
        return (
            f"Gemini quota/rate limit exceeded for model {model}.{retry_text} "
            "Check https://ai.dev/rate-limit or switch models/keys."
        )
    if "api_key" in lowered or "permission" in lowered or "unauthenticated" in lowered:
        return "Gemini API key was rejected. Check GEMINI_API_KEY in .env."
    return _truncate_error(f"Gemini API error: {error}")


def _extract_retry_delay(error: str) -> str:
    match = re.search(r"retry in ([0-9.]+s)", error, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(r"'retryDelay': '([^']+)'", error)
    return match.group(1) if match else ""


def _truncate_error(error: str, limit: int = 240) -> str:
    return error if len(error) <= limit else f"{error[:limit].rstrip()}..."
