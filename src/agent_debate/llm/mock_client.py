"""Deterministic mock provider for tests and API-free demos."""

from __future__ import annotations

import hashlib
import re

from agent_debate.llm.base import LLMResult


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
            winner, pro_score, con_score, reason = self._score_decision(prompt)
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
        favored, alternative = self._stance_options(stance)
        points = self._points_for(side, favored, alternative, topic)
        rebuttal = self._rebuttal_for(side, favored, alternative, topic)
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

    def _stance_options(self, stance: str) -> tuple[str, str]:
        match = re.search(r"Argue that (.+?) is better than (.+?)\.", stance)
        if match:
            return match.group(1), match.group(2)
        if "oppose" in stance.lower():
            return "the opposition side", "the proposition"
        return "the proposition", "the opposition side"

    def _points_for(
        self,
        side: str,
        favored: str,
        alternative: str,
        topic: str,
    ) -> list[str]:
        lower = favored.lower()
        other = alternative.lower()
        topic_lower = topic.lower()
        if "ai agent" in topic_lower and "universit" in topic_lower:
            if side == "Pro":
                return [
                    "students will meet AI agents in real software teams, so guided "
                    "practice is better than pretending the tools do not exist",
                    "a requirement lets the course teach verification, attribution, "
                    "testing, and prompt documentation explicitly",
                    "using agents inside a controlled assignment makes the work auditable "
                    "through logs, transcripts, and tests",
                    "students who struggle can get planning and review support while still "
                    "being graded on understanding",
                    "the best policy is supervised use with limits, not blind dependence "
                    "or an unenforceable ban",
                ]
            return [
                "a requirement can reward access to tools and prompt fluency before core "
                "programming fundamentals are secure",
                "students may accept generated code without enough skill to evaluate "
                "architecture, bugs, or security risks",
                "billing, privacy, and account access make mandatory AI use unequal "
                "across a class",
                "logs show what happened, but they do not prove the student understood "
                "each design choice",
                "AI agents should be permitted after fundamentals are assessed, not made "
                "mandatory from the beginning",
            ]
        if "pilates" in lower and "yoga" in other:
            return [
                "Pilates gives more measurable progression through core strength, control, "
                "and alignment",
                "Pilates is especially strong for posture, rehabilitation-style movement, "
                "and controlled resistance",
                "Pilates classes often make technical progress visible through repetitions, "
                "form cues, and equipment levels",
                "Pilates can be easier to grade as a sport-like practice because strength "
                "and control targets are concrete",
                "Pilates offers a focused physical-training goal rather than a broad wellness "
                "practice",
            ]
        if "yoga" in lower and "pilates" in other:
            return [
                "Yoga combines flexibility, balance, breathing, and mental focus in one "
                "broader discipline",
                "Yoga is more accessible because it usually needs less equipment and has "
                "many beginner-friendly styles",
                "Yoga develops mobility and stress regulation, not only muscular control",
                "Yoga has a wider cultural and competitive ecosystem, from studio practice "
                "to advanced athletic forms",
                "Yoga is the better all-around practice when the criteria include body, "
                "mind, recovery, and consistency",
            ]
        return [
            f"{favored} better satisfies the main criteria than {alternative}",
            f"{favored} has clearer practical benefits for the audience",
            f"{favored} is easier to defend when comparing costs, risks, and outcomes",
            f"{favored} gives a stronger answer to the opponent's central concern",
            f"{favored} remains the better choice after weighing trade-offs",
        ]

    def _rebuttal_for(self, side: str, favored: str, alternative: str, topic: str) -> str:
        topic_lower = topic.lower()
        if "ai agent" in topic_lower and "universit" in topic_lower:
            if side == "Pro":
                return (
                    "Con is right that dependency is a risk, but a course requirement can "
                    "teach students how to control that risk."
                )
            return (
                "Pro is right about workplace relevance, but a university requirement "
                "must protect learning outcomes and fair access first."
            )
        if side == "Pro":
            return (
                f"Con may value {alternative}, but that does not outweigh "
                f"{self._possessive(favored)} strongest advantages."
            )
        return (
            f"Pro makes a reasonable case for {alternative}, but {favored} answers "
            "the comparison more completely."
        )

    def _score_decision(self, prompt: str) -> tuple[str, int, int, str]:
        pro = self._extract_block(prompt, "Latest pro:", "Latest con:")
        con = self._extract_block(prompt, "Latest con:", "Scoring criteria:")
        pro_score = self._argument_score(pro)
        con_score = self._argument_score(con)
        if pro_score == con_score:
            tie_break = int(hashlib.sha256(f"{pro}|{con}".encode()).hexdigest(), 16) % 2
            if tie_break == 0:
                pro_score += 1
            else:
                con_score += 1
        if pro_score > con_score:
            return (
                "Pro Agent",
                pro_score,
                con_score,
                "The pro side gave the stronger final argument based on specificity, "
                "direct rebuttal, and connection to the selected topic.",
            )
        return (
            "Con Agent",
            pro_score,
            con_score,
            "The con side gave the stronger final argument based on specificity, "
            "direct rebuttal, and connection to the selected topic.",
        )

    def _argument_score(self, text: str) -> int:
        lowered = text.lower()
        score = 62 + min(14, len(text.split()) // 9)
        score += self._keyword_points(
            lowered,
            [
                "because",
                "risk",
                "evidence",
                "source",
                "testing",
                "privacy",
                "access",
                "specific",
                "criteria",
                "trade-off",
                "rebut",
                "stronger",
            ],
        )
        if "addressing the opponent" in lowered or "addressing the opening" in lowered:
            score += 4
        if "my main point" in lowered:
            score += 3
        return min(score, 95)

    def _keyword_points(self, text: str, keywords: list[str]) -> int:
        return min(12, sum(2 for keyword in keywords if keyword in text))

    def _extract_block(self, prompt: str, start: str, end: str) -> str:
        pattern = rf"{re.escape(start)}(.*?){re.escape(end)}"
        match = re.search(pattern, prompt, flags=re.DOTALL)
        return match.group(1).strip() if match else ""

    def _possessive(self, value: str) -> str:
        return f"{value}'" if value.endswith("s") else f"{value}'s"
