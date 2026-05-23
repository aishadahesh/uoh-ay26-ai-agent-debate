"""Small routing layer around process queues."""

from __future__ import annotations

from multiprocessing import Queue

from agent_debate.ipc.messages import CHILD_AGENTS, Message


class MessageRouter:
    """Enforces the rule that children only exchange messages through the judge."""

    def __init__(self, queues: dict[str, Queue]) -> None:
        self.queues = queues

    def route(self, message: Message) -> None:
        """Place a message on its receiver queue after validating the route."""

        if message.sender in CHILD_AGENTS and message.receiver in CHILD_AGENTS:
            raise ValueError("direct child-to-child routes are forbidden")
        if message.receiver not in self.queues:
            raise KeyError(f"unknown receiver queue: {message.receiver}")
        self.queues[message.receiver].put(message.to_dict())
