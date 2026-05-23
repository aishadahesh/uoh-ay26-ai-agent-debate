"""LLM client contracts and usage gatekeeping."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LLMResult:
    """Generated text plus optional source URLs."""

    content: str
    sources: list[str]


class LLMClient(Protocol):
    """Provider-neutral LLM client."""

    def complete(self, prompt: str, *, model: str, timeout: float) -> LLMResult:
        """Generate a response with a hard timeout."""


class LLMProviderError(RuntimeError):
    """Raised when an external LLM provider cannot complete a request."""


class Gatekeeper:
    """Tracks simple budget limits before provider calls are made."""

    def __init__(self, max_calls: int, max_input_chars: int) -> None:
        self.max_calls = max_calls
        self.max_input_chars = max_input_chars
        self.calls = 0
        self.input_chars = 0

    def check(self, prompt: str) -> None:
        """Raise if a debate would exceed the configured call or context budget."""

        if self.calls + 1 > self.max_calls:
            raise RuntimeError("LLM call budget exceeded")
        if self.input_chars + len(prompt) > self.max_input_chars:
            raise RuntimeError("estimated input character budget exceeded")
        self.calls += 1
        self.input_chars += len(prompt)
