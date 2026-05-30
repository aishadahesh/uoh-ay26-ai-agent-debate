"""YAML loading helpers for configuration files."""

from __future__ import annotations

from typing import Any


def load_yaml(text: str) -> dict[str, Any]:
    """Load YAML with PyYAML when present; otherwise parse this project's YAML subset."""

    try:
        import yaml

        return yaml.safe_load(text) or {}
    except ModuleNotFoundError:
        return parse_simple_yaml(text)


def parse_simple_yaml(text: str) -> dict[str, Any]:
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
            parent[key] = parse_scalar(value.strip())
    return root


def parse_scalar(value: str) -> Any:
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
