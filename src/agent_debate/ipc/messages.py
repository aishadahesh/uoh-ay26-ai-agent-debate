"""Structured JSON message schema for inter-process debate traffic."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

VALID_SENDERS = {"judge", "pro", "con", "system"}
VALID_RECEIVERS = {"judge", "pro", "con", "system"}
CHILD_AGENTS = {"pro", "con"}


@dataclass(frozen=True)
class Message:
    """JSON-serializable message passed through multiprocessing queues."""

    round: int
    sender: str
    receiver: str
    type: str
    content: str
    sources: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.round < 0:
            raise ValueError("round must be non-negative")
        if self.sender not in VALID_SENDERS:
            raise ValueError(f"invalid sender: {self.sender}")
        if self.receiver not in VALID_RECEIVERS:
            raise ValueError(f"invalid receiver: {self.receiver}")
        if self.sender in CHILD_AGENTS and self.receiver in CHILD_AGENTS:
            raise ValueError("child agents may not communicate directly")
        if not self.type:
            raise ValueError("type is required")
        if not isinstance(self.sources, list):
            raise TypeError("sources must be a list")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready dict."""

        return {
            "round": self.round,
            "sender": self.sender,
            "receiver": self.receiver,
            "type": self.type,
            "content": self.content,
            "sources": self.sources,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Message:
        """Create and validate a message from queue payload data."""

        return cls(
            round=int(payload["round"]),
            sender=str(payload["sender"]),
            receiver=str(payload["receiver"]),
            type=str(payload["type"]),
            content=str(payload.get("content", "")),
            sources=list(payload.get("sources", [])),
            timestamp=str(payload.get("timestamp", datetime.now(timezone.utc).isoformat())),
            metadata=dict(payload.get("metadata", {})),
        )
