"""Context window engineering: write full logs, select compact prompts."""

from __future__ import annotations

from agent_debate.ipc.messages import Message


class DebateMemory:
    """Maintains full in-memory messages and a compact running summary."""

    def __init__(self) -> None:
        self.messages: list[Message] = []
        self.summary = "No previous arguments yet."

    def write(self, message: Message) -> None:
        """Store a full message and update a compact summary outside prompts."""

        self.messages.append(message)
        if message.type in {"argument", "final"}:
            clipped = message.content[:180].replace("\n", " ")
            self.summary = f"Latest {message.sender} point in round {message.round}: {clipped}"

    def latest_from(self, sender: str) -> Message | None:
        """Return the latest message from one speaker."""

        for message in reversed(self.messages):
            if message.sender == sender:
                return message
        return None


class PromptBuilder:
    """Selects only role-relevant context for each turn."""

    def child_prompt(
        self,
        *,
        role: str,
        stance: str,
        topic: str,
        rules: dict[str, object],
        previous_argument: str,
        summary: str,
        instruction: str,
        evidence: list[str],
    ) -> str:
        return (
            f"You are the {role} debate agent. Stance: {stance}.\n"
            f"Topic: {topic}\nRules: {rules}\n"
            f"Running summary: {summary}\n"
            f"Opponent previous argument: {previous_argument or 'None yet.'}\n"
            f"Current judge instruction: {instruction}\n"
            f"Web evidence candidates: {evidence}\n"
            "Write one respectful turn. Explicitly rebut the opponent if present. "
            "Include source URLs you rely on."
        )

    def judge_prompt(
        self,
        *,
        topic: str,
        rules: dict[str, object],
        latest_pro: str,
        latest_con: str,
        summary: str,
        scoring: dict[str, int],
        round_number: int,
        final: bool,
    ) -> str:
        mode = (
            "FINAL DECISION: choose exactly one winner; no tie allowed. "
            "Your answer must include these lines: "
            "Winner: <Pro Agent or Con Agent>; Score: Pro <0-100>, Con <0-100>; "
            "Reason: <one concise explanation>."
            if final
            else "Judge the round."
        )
        return (
            f"{mode}\nTopic: {topic}\nRules: {rules}\nRound: {round_number}\n"
            f"Running summary: {summary}\nLatest pro: {latest_pro}\nLatest con: {latest_con}\n"
            f"Scoring criteria: {scoring}\n"
            "Evaluate persuasion, evidence quality, factual correctness, and direct rebuttal."
        )
