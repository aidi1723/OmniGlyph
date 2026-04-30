from __future__ import annotations

from functools import wraps
from pathlib import Path
from typing import Callable

from omniglyph.logos.loader import load_policy_file
from omniglyph.logos.validator import validate_action


class LogosViolationError(Exception):
    def __init__(self, result: dict):
        self.result = result
        super().__init__(result.get("message", "LogosGate policy violation"))


def logos_gate(policy_path: Path | str, block_on: tuple[str, ...] = ("block",)) -> Callable:
    policy = load_policy_file(policy_path)

    def decorator(function: Callable) -> Callable:
        @wraps(function)
        def wrapper(action_plan: str, *args, **kwargs):
            result = validate_action(action_plan, policy)
            if result["decision"] in block_on:
                raise LogosViolationError(result)
            return function(action_plan, *args, **kwargs)

        return wrapper

    return decorator
