"""Base process-like agent components."""

from __future__ import annotations

from multiprocessing import Queue
from queue import Empty

from agent_debate.ipc.messages import Message


class BaseAgent:
    """Common queue behavior for all agents."""

    def __init__(self, role: str, inbox: Queue, outbox: Queue) -> None:
        self.role = role
        self.inbox = inbox
        self.outbox = outbox

    def receive(self, timeout: float) -> Message:
        """Receive one structured message from the process inbox."""

        try:
            return Message.from_dict(self.inbox.get(timeout=timeout))
        except Empty as exc:
            raise TimeoutError(f"{self.role} timed out waiting for a message") from exc

    def send(self, message: Message) -> None:
        """Send one structured message to the parent queue."""

        self.outbox.put(message.to_dict())
