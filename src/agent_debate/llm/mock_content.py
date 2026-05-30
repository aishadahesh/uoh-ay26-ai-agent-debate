"""Topic-aware content helpers for the mock LLM provider."""

from __future__ import annotations

import re


def stance_options(stance: str) -> tuple[str, str]:
    """Return the favored and alternative sides implied by a stance."""

    match = re.search(r"Argue that (.+?) is better than (.+?)\.", stance)
    if match:
        return match.group(1), match.group(2)
    if "oppose" in stance.lower():
        return "the opposition side", "the proposition"
    return "the proposition", "the opposition side"


def points_for(side: str, favored: str, alternative: str, topic: str) -> list[str]:
    """Return round-specific mock argument points."""

    lower = favored.lower()
    other = alternative.lower()
    topic_lower = topic.lower()
    if "ai agent" in topic_lower and "universit" in topic_lower:
        return _ai_course_points(side)
    if "pilates" in lower and "yoga" in other:
        return _pilates_points()
    if "yoga" in lower and "pilates" in other:
        return _yoga_points()
    return [
        f"{favored} better satisfies the main criteria than {alternative}",
        f"{favored} has clearer practical benefits for the audience",
        f"{favored} is easier to defend when comparing costs, risks, and outcomes",
        f"{favored} gives a stronger answer to the opponent's central concern",
        f"{favored} remains the better choice after weighing trade-offs",
    ]


def rebuttal_for(side: str, favored: str, alternative: str, topic: str) -> str:
    """Return a concise mock rebuttal for the selected side."""

    topic_lower = topic.lower()
    if "ai agent" in topic_lower and "universit" in topic_lower:
        if side == "Pro":
            return (
                "Con is right that dependency is a risk, but a course requirement can "
                "teach students how to control that risk."
            )
        return (
            "Pro is right about workplace relevance, but a university requirement must "
            "protect learning outcomes and fair access first."
        )
    if side == "Pro":
        return (
            f"Con may value {alternative}, but that does not outweigh "
            f"{_possessive(favored)} strongest advantages."
        )
    return (
        f"Pro makes a reasonable case for {alternative}, but {favored} answers the "
        "comparison more completely."
    )


def _ai_course_points(side: str) -> list[str]:
    if side == "Pro":
        return [
            "students will meet AI agents in real software teams, so guided practice is "
            "better than pretending the tools do not exist",
            "a requirement lets the course teach verification, attribution, testing, and "
            "prompt documentation explicitly",
            "using agents inside a controlled assignment makes the work auditable through "
            "logs, transcripts, and tests",
            "students who struggle can get planning and review support while still being "
            "graded on understanding",
            "the best policy is supervised use with limits, not blind dependence or an "
            "unenforceable ban",
        ]
    return [
        "a requirement can reward access to tools and prompt fluency before core "
        "programming fundamentals are secure",
        "students may accept generated code without enough skill to evaluate architecture, "
        "bugs, or security risks",
        "billing, privacy, and account access make mandatory AI use unequal across a class",
        "logs show what happened, but they do not prove the student understood each design "
        "choice",
        "AI agents should be permitted after fundamentals are assessed, not made mandatory "
        "from the beginning",
    ]


def _pilates_points() -> list[str]:
    return [
        "Pilates gives more measurable progression through core strength, control, and "
        "alignment",
        "Pilates is especially strong for posture, rehabilitation-style movement, and "
        "controlled resistance",
        "Pilates classes often make technical progress visible through repetitions, form "
        "cues, and equipment levels",
        "Pilates can be easier to grade as a sport-like practice because strength and "
        "control targets are concrete",
        "Pilates offers a focused physical-training goal rather than a broad wellness "
        "practice",
    ]


def _yoga_points() -> list[str]:
    return [
        "Yoga combines flexibility, balance, breathing, and mental focus in one broader "
        "discipline",
        "Yoga is more accessible because it usually needs less equipment and has many "
        "beginner-friendly styles",
        "Yoga develops mobility and stress regulation, not only muscular control",
        "Yoga has a wider cultural and competitive ecosystem, from studio practice to "
        "advanced athletic forms",
        "Yoga is the better all-around practice when the criteria include body, mind, "
        "recovery, and consistency",
    ]


def _possessive(value: str) -> str:
    return f"{value}'" if value.endswith("s") else f"{value}'s"
