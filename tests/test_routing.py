from multiprocessing import Queue

import pytest

from agent_debate.ipc.messages import Message
from agent_debate.ipc.queues import MessageRouter


def test_router_sends_judge_message_to_child_queue() -> None:
    queue = Queue()
    router = MessageRouter({"pro": queue})
    router.route(Message(1, "judge", "pro", "instruction", "Go"))
    assert queue.get(timeout=1)["receiver"] == "pro"


def test_router_rejects_unknown_receiver() -> None:
    router = MessageRouter({})
    with pytest.raises(KeyError):
        router.route(Message(1, "judge", "pro", "instruction", "Go"))
