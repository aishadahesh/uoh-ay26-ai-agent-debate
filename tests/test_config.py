from pathlib import Path

import pytest

from agent_debate.config import frame_topic, load_config
from agent_debate.config_yaml import parse_simple_yaml


def test_load_config() -> None:
    config = load_config(Path("configs/debate_config.yaml"))
    assert config.turns_per_side == 5
    assert config.agent("pro")["stance"]


def test_config_can_override_topic_without_mutating_original() -> None:
    config = load_config(Path("configs/debate_config.yaml"))
    updated = config.with_topic("New topic")
    assert updated.topic == "New topic."
    assert config.topic != "New topic"


def test_config_frames_a_or_b_topic_into_opposing_stances() -> None:
    config = load_config(Path("configs/debate_config.yaml"))
    updated = config.with_topic("What is better sport: pilates or yoga?")
    assert updated.topic == "Pilates is better than Yoga."
    assert updated.agent("pro")["stance"] == "Argue that Pilates is better than Yoga."
    assert updated.agent("con")["stance"] == "Argue that Yoga is better than Pilates."


def test_frame_topic_keeps_yes_no_proposition() -> None:
    framed = frame_topic("Should students use AI agents?")
    assert framed["topic"] == "Should students use AI agents."
    assert framed["pro_stance"] == "Support the proposition."


def test_config_rejects_missing_required_keys(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("topic: hello\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing config keys"):
        load_config(bad)


def test_config_rejects_zero_turns(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        """
topic: hello
turns_per_side: 0
agents:
  judge: {}
  pro: {}
  con: {}
llm: {}
logging: {}
watchdog: {}
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="at least 1"):
        load_config(bad)


def test_simple_yaml_fallback_parser_handles_scalars() -> None:
    parsed = parse_simple_yaml(
        """
root:
  enabled: true
  disabled: false
  count: 3
  ratio: 1.5
  name: "agent"
"""
    )
    assert parsed["root"]["enabled"] is True
    assert parsed["root"]["disabled"] is False
    assert parsed["root"]["count"] == 3
    assert parsed["root"]["ratio"] == 1.5
    assert parsed["root"]["name"] == "agent"
