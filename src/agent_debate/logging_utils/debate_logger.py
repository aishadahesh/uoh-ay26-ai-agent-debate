"""Structured JSONL and human transcript logging."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from agent_debate.config import Config
from agent_debate.ipc.messages import Message


class DebateLogger:
    """Writes full debate logs for auditability and submission evidence."""

    def __init__(self, config: Config) -> None:
        self.config = config
        settings = config.logging
        root = config.path.parent.parent
        self.directory = root / settings["directory"]
        self.directory.mkdir(parents=True, exist_ok=True)
        self.jsonl_path = self.directory / settings["jsonl_file"]
        self.transcript_path = self.directory / settings["transcript_file"]

    def log(self, message: Message) -> None:
        """Append one message to both log formats."""

        with self.jsonl_path.open("a", encoding="utf-8") as jsonl:
            jsonl.write(json.dumps(message.to_dict(), ensure_ascii=False) + "\n")
        with self.transcript_path.open("a", encoding="utf-8") as transcript:
            transcript.write(
                f"[round {message.round}] {self._participant_label(message.sender)} "
                f"-> {self._participant_label(message.receiver)} "
                f"({message.type})\n{message.content}\nSources: {message.sources}\n\n"
            )

    def reset(self) -> None:
        """Clear previous debate logs before a new run."""

        self.jsonl_path.write_text("", encoding="utf-8")
        self.transcript_path.write_text("", encoding="utf-8")

    def last_transcript(self) -> str:
        """Return the latest human transcript, if any."""

        if not self.transcript_path.exists():
            return "No transcript exists yet."
        return self.transcript_path.read_text(encoding="utf-8")

    def export_transcript(self, output_path: Path | None = None) -> Path:
        """Save the latest transcript to a timestamped archive file."""

        transcript = self.last_transcript()
        if transcript == "No transcript exists yet." or not transcript.strip():
            raise FileNotFoundError("No transcript exists yet. Run a debate first.")
        destination = output_path or self._default_export_path()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(transcript, encoding="utf-8")
        return destination

    def _default_export_path(self) -> Path:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return self.directory / f"transcript-{stamp}.txt"

    def _participant_label(self, role: str) -> str:
        if role not in self.config.raw.get("agents", {}):
            return role
        agent = self.config.agent(role)
        name = agent.get("name", role.title())
        provider = agent.get("provider", self.config.llm.get("provider", "unknown"))
        model = agent.get("model", "unknown-model")
        return f"{role} LLM: {name} ({provider}/{model})"
