"""Deterministic mock provider for tests and API-free demos."""

from __future__ import annotations

import re

from agent_debate.llm.base import LLMResult
from agent_debate.llm.mock_content import points_for, rebuttal_for, stance_options
from agent_debate.llm.mock_scoring import score_decision


class MockLLMClient:
    """Small deterministic LLM substitute used only when configured or in tests."""

    def complete(self, prompt: str, *, model: str, timeout: float) -> LLMResult:
        topic = self._extract(prompt, r"Topic: (.+)")
        stance = self._extract(prompt, r"Stance: (.+)")
        round_number = self._extract(prompt, r"Round (\d+):") or self._extract(
            prompt,
            r"Round: (\d+)",
        )
        if "You are the pro debate agent" in prompt:
            return LLMResult(
                content=self._argument("Pro", stance, topic, round_number, prompt),
                sources=[],
            )
        if "You are the con debate agent" in prompt:
            return LLMResult(
                content=self._argument("Con", stance, topic, round_number, prompt),
                sources=[],
            )
        if "FINAL DECISION" in prompt:
            winner, pro_score, con_score, reason = score_decision(prompt)
            return LLMResult(
                content=(
                    f"Winner: {winner}. Score: Pro {pro_score}, Con {con_score}. "
                    f"{reason}"
                ),
                sources=[],
            )
        return LLMResult(content="Judge note: continue the debate.", sources=[])

    def _argument(
        self,
        side: str,
        stance: str,
        topic: str,
        round_number: str,
        prompt: str,
    ) -> str:
        previous = "the opening frame"
        if "Opponent previous argument: None yet." not in prompt:
            previous = "the opponent's last claim"
        round_key = int(round_number or "1")
        favored, alternative = stance_options(stance)
        points = points_for(side, favored, alternative, topic)
        rebuttal = rebuttal_for(side, favored, alternative, topic)
        point = points[(round_key - 1) % len(points)]
        clean_stance = stance.rstrip(".")
        return (
            f"{side} round {round_key}: Addressing {previous}, {rebuttal} "
            f"My stance is: {clean_stance}. On the topic '{topic}', my main point is "
            f"that {point}."
        )

    def _extract(self, prompt: str, pattern: str) -> str:
        match = re.search(pattern, prompt)
        return match.group(1).strip() if match else ""
