"""Deterministic scoring helpers for mock final decisions."""

from __future__ import annotations

import hashlib
import re


def score_decision(prompt: str) -> tuple[str, int, int, str]:
    """Score latest Pro and Con arguments from a judge prompt."""

    pro = _extract_block(prompt, "Latest pro:", "Latest con:")
    con = _extract_block(prompt, "Latest con:", "Scoring criteria:")
    pro_score = argument_score(pro)
    con_score = argument_score(con)
    if pro_score == con_score:
        if _tie_break(pro, con) == 0:
            pro_score += 1
        else:
            con_score += 1
    if pro_score > con_score:
        return (
            "Pro Agent",
            pro_score,
            con_score,
            "The pro side gave the stronger final argument based on specificity, direct "
            "rebuttal, and connection to the selected topic.",
        )
    return (
        "Con Agent",
        pro_score,
        con_score,
        "The con side gave the stronger final argument based on specificity, direct "
        "rebuttal, and connection to the selected topic.",
    )


def argument_score(text: str) -> int:
    """Produce a stable score from simple argument-quality signals."""

    lowered = text.lower()
    score = 62 + min(14, len(text.split()) // 9)
    score += _keyword_points(
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


def _tie_break(pro: str, con: str) -> int:
    return int(hashlib.sha256(f"{pro}|{con}".encode()).hexdigest(), 16) % 2


def _keyword_points(text: str, keywords: list[str]) -> int:
    return min(12, sum(2 for keyword in keywords if keyword in text))


def _extract_block(prompt: str, start: str, end: str) -> str:
    pattern = rf"{re.escape(start)}(.*?){re.escape(end)}"
    match = re.search(pattern, prompt, flags=re.DOTALL)
    return match.group(1).strip() if match else ""
