import pytest

from agent_debate.ipc.messages import Message


def test_message_schema_validates_required_route() -> None:
    message = Message(round=1, sender="pro", receiver="judge", type="argument", content="Hi")
    assert message.to_dict()["sender"] == "pro"


def test_child_agents_cannot_talk_directly() -> None:
    with pytest.raises(ValueError, match="directly"):
        Message(round=1, sender="pro", receiver="con", type="argument", content="Nope")
