"""Strict JSON helpers shared by CLI, MCP, and API boundaries."""

import json
import math
from typing import Any


def parse_strict_json(text: str) -> Any:
    def reject_constant(value: str) -> Any:
        raise ValueError(f"non-standard JSON numeric constant: {value}")

    value = json.loads(text, parse_constant=reject_constant)
    ensure_finite_json(value)
    return value


def ensure_finite_json(value: Any, path: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{path} must be a finite number")
    if isinstance(value, dict):
        for key, child in value.items():
            ensure_finite_json(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            ensure_finite_json(child, f"{path}[{index}]")
