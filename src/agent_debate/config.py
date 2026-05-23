"""Configuration loading and validation."""

from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Config:
    """Runtime configuration loaded from YAML."""

    raw: dict[str, Any]
    path: Path

    @property
    def topic(self) -> str:
        return str(self.raw["topic"])

    @property
    def turns_per_side(self) -> int:
        return int(self.raw["turns_per_side"])

    @property
    def llm(self) -> dict[str, Any]:
        return dict(self.raw["llm"])

    @property
    def logging(self) -> dict[str, Any]:
        return dict(self.raw["logging"])

    @property
    def watchdog(self) -> dict[str, Any]:
        return dict(self.raw["watchdog"])

    def agent(self, role: str) -> dict[str, Any]:
        return dict(self.raw["agents"][role])

    def with_topic(self, topic: str) -> Config:
        """Return a copy of the config with a runtime-selected debate topic."""

        raw = deepcopy(self.raw)
        framed = frame_topic(topic)
        raw["topic"] = framed["topic"]
        raw["agents"]["pro"]["stance"] = framed["pro_stance"]
        raw["agents"]["con"]["stance"] = framed["con_stance"]
        return Config(raw=raw, path=self.path)


def frame_topic(topic: str) -> dict[str, str]:
    """Turn a user topic into a clear proposition and two opposing stances."""

    clean_topic = topic.strip().rstrip(" ?.")
    comparison = _extract_comparison(clean_topic)
    if comparison:
        first, second = comparison
        return {
            "topic": f"{first} is better than {second}.",
            "pro_stance": f"Argue that {first} is better than {second}.",
            "con_stance": f"Argue that {second} is better than {first}.",
        }
    return {
        "topic": f"{clean_topic}.",
        "pro_stance": "Support the proposition.",
        "con_stance": "Oppose the proposition.",
    }


def _extract_comparison(topic: str) -> tuple[str, str] | None:
    """Extract A/B sides from common 'A or B' topic wording."""

    tail = topic.split(":", maxsplit=1)[-1]
    match = re.search(r"\b(.+?)\s+or\s+(.+)\b", tail, flags=re.IGNORECASE)
    if not match:
        return None
    first = _clean_option(match.group(1))
    second = _clean_option(match.group(2))
    if not first or not second:
        return None
    return first, second


def _clean_option(value: str) -> str:
    return value.strip(" .?!,;:").title()


def load_config(path: str | Path) -> Config:
    """Load and validate a YAML config file."""

    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        raw = _load_yaml(handle.read())
    required = ["topic", "turns_per_side", "agents", "llm", "logging", "watchdog"]
    missing = [key for key in required if key not in raw]
    if missing:
        raise ValueError(f"missing config keys: {missing}")
    if int(raw["turns_per_side"]) < 1:
        raise ValueError("turns_per_side must be at least 1")
    for role in ["judge", "pro", "con"]:
        if role not in raw["agents"]:
            raise ValueError(f"missing agent config: {role}")
    return Config(raw=raw, path=config_path)


def _load_yaml(text: str) -> dict[str, Any]:
    """Load YAML with PyYAML when present, otherwise parse the simple config format."""

    try:
        import yaml

        return yaml.safe_load(text) or {}
    except ModuleNotFoundError:
        return _parse_simple_yaml(text)


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse the nested key-value YAML subset used by this project."""

    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        key, _, value = raw_line.strip().partition(":")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value.strip() == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_scalar(value.strip())
    return root


def _parse_scalar(value: str) -> Any:
    """Parse strings, booleans, integers, and floats from simple YAML."""

    clean = value.strip("'\"")
    if clean.lower() == "true":
        return True
    if clean.lower() == "false":
        return False
    try:
        return int(clean)
    except ValueError:
        pass
    try:
        return float(clean)
    except ValueError:
        return clean
