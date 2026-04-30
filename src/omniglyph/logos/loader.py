from __future__ import annotations

import json
from pathlib import Path

from omniglyph.logos.models import LogosPolicy


def load_policy_file(path: Path | str) -> LogosPolicy:
    policy_path = Path(path)
    if policy_path.suffix.lower() != ".json":
        raise ValueError("LogosGate MVP supports JSON policy files only")
    data = json.loads(policy_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("policy file must contain a JSON object")
    return LogosPolicy.from_mapping(data)


def load_policy_files(path: Path | str) -> list[LogosPolicy]:
    policy_path = Path(path)
    if policy_path.is_file():
        return [load_policy_file(policy_path)]
    if not policy_path.is_dir():
        raise FileNotFoundError(policy_path)
    json_files = sorted(policy_path.glob("*.json"), key=lambda item: item.name)
    return [load_policy_file(item) for item in json_files]
