# LogosGate MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build LogosGate as an experimental OmniGlyph action-policy firewall that returns deterministic `allow` / `warn` / `review` / `block` decisions before an agent executes real-world actions.

**Architecture:** Add a focused `omniglyph.logos` package with dataclass policy models, a JSON policy loader, a deterministic matcher, a validator, and a decorator. Expose it through CLI and MCP without changing the existing glyph, lexicon, code-security, or language-security APIs.

**Tech Stack:** Python 3.10+, stdlib dataclasses/json/re/functools/pathlib, pytest, existing OmniGlyph CLI and MCP stdio server.

---

## Scope

This plan implements the MVP described in `言法界枢/项目思路.md`.

Included:

- `LogosPolicy` / `LogosRule` / `LogosDecision` data models.
- JSON policy file loading.
- Deterministic `literal` and `regex` matching.
- `allow_context` suppression for obvious false positives.
- `validate_action(...)` API.
- `LogosViolationError` and `@logos_gate(...)`.
- CLI command: `omniglyph logos validate`.
- MCP tool: `validate_action_policy`.
- Example policy packs for `marketing_integrity`, `code_safety`, and `trade_compliance`.
- Tests for models, loader, validator, decorator, CLI, and MCP.

Not included:

- YAML support. This avoids adding PyYAML for the MVP. If needed later, add it in a separate task.
- LLM-based policy judgment.
- Automatic mutation or rewriting of agent output.
- Production compliance certification.

## File Structure

- Create: `src/omniglyph/logos/__init__.py`
  - Public exports for the experimental LogosGate API.
- Create: `src/omniglyph/logos/models.py`
  - Dataclasses, validation helpers, and `from_mapping` parsing.
- Create: `src/omniglyph/logos/loader.py`
  - Load one policy file or a directory of `*.json` policies.
- Create: `src/omniglyph/logos/matcher.py`
  - Literal and regex matching with `allow_context` suppression.
- Create: `src/omniglyph/logos/validator.py`
  - Main `validate_action(...)` function and result construction.
- Create: `src/omniglyph/logos/decorators.py`
  - `LogosViolationError` and `@logos_gate(...)`.
- Create: `examples/logos-policies/marketing_integrity.json`
  - Blocks fake orders, fake reviews, privacy theft, and bot swarms.
- Create: `examples/logos-policies/code_safety.json`
  - Blocks dangerous shell and credential exfiltration patterns.
- Create: `examples/logos-policies/trade_compliance.json`
  - Reviews contract/quote/HS-code commitments.
- Modify: `src/omniglyph/cli.py`
  - Add `omniglyph logos validate`.
- Modify: `src/omniglyph/mcp_server.py`
  - Add `validate_action_policy` tool.
- Modify: `scripts/mcp_smoke_test.sh`
  - Include `validate_action_policy` in expected tools.
- Test: `tests/test_logos_models.py`
- Test: `tests/test_logos_validator.py`
- Test: `tests/test_logos_decorator.py`
- Test: `tests/test_logos_cli.py`
- Test: `tests/test_logos_mcp.py`

---

### Task 1: Add Logos Models and JSON Loader

**Files:**
- Create: `src/omniglyph/logos/__init__.py`
- Create: `src/omniglyph/logos/models.py`
- Create: `src/omniglyph/logos/loader.py`
- Test: `tests/test_logos_models.py`

- [ ] **Step 1: Write failing model/loader tests**

Create `tests/test_logos_models.py`:

```python
from pathlib import Path

import pytest

from omniglyph.logos.loader import load_policy_file, load_policy_files
from omniglyph.logos.models import LogosPolicy, LogosRule


def sample_policy_mapping():
    return {
        "policy_id": "marketing_integrity.growth.v1",
        "concept": "growth",
        "namespace": "business.marketing",
        "definition": "Growth must not fabricate demand.",
        "version": "0.1.0",
        "rules": [
            {
                "rule_id": "marketing_integrity.no_fake_orders",
                "description": "Block fake order manipulation.",
                "severity": "block",
                "match_type": "literal",
                "patterns": ["刷单", "fake orders"],
                "allow_context": ["不要刷单", "avoid fake orders"],
                "source": {
                    "type": "project_policy",
                    "name": "LogosGate Genesis Policy Pack",
                    "version": "0.1.0",
                },
            }
        ],
    }


def test_logos_policy_from_mapping_parses_rules():
    policy = LogosPolicy.from_mapping(sample_policy_mapping())

    assert policy.schema == "omniglyph.logos.policy:0.1"
    assert policy.policy_id == "marketing_integrity.growth.v1"
    assert policy.concept == "growth"
    assert policy.namespace == "business.marketing"
    assert policy.rules[0].rule_id == "marketing_integrity.no_fake_orders"
    assert policy.rules[0].severity == "block"
    assert policy.rules[0].patterns == ["刷单", "fake orders"]
    assert policy.rules[0].source["name"] == "LogosGate Genesis Policy Pack"


def test_logos_policy_rejects_invalid_severity():
    mapping = sample_policy_mapping()
    mapping["rules"][0]["severity"] = "panic"

    with pytest.raises(ValueError, match="severity"):
        LogosPolicy.from_mapping(mapping)


def test_logos_policy_rejects_invalid_match_type():
    mapping = sample_policy_mapping()
    mapping["rules"][0]["match_type"] = "embedding"

    with pytest.raises(ValueError, match="match_type"):
        LogosPolicy.from_mapping(mapping)


def test_logos_rule_requires_patterns():
    with pytest.raises(ValueError, match="patterns"):
        LogosRule.from_mapping(
            {
                "rule_id": "missing.patterns",
                "description": "Invalid rule.",
                "severity": "block",
                "match_type": "literal",
                "patterns": [],
            }
        )


def test_load_policy_file_reads_json(tmp_path):
    path = tmp_path / "policy.json"
    path.write_text(
        """{
          "policy_id": "marketing_integrity.growth.v1",
          "concept": "growth",
          "namespace": "business.marketing",
          "definition": "Growth must not fabricate demand.",
          "version": "0.1.0",
          "rules": [
            {
              "rule_id": "marketing_integrity.no_fake_orders",
              "description": "Block fake order manipulation.",
              "severity": "block",
              "match_type": "literal",
              "patterns": ["刷单"],
              "allow_context": ["不要刷单"],
              "source": {"type": "project_policy", "name": "Fixture", "version": "0.1.0"}
            }
          ]
        }""",
        encoding="utf-8",
    )

    policy = load_policy_file(path)

    assert policy.policy_id == "marketing_integrity.growth.v1"
    assert policy.rules[0].patterns == ["刷单"]


def test_load_policy_files_reads_all_json_files(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text(
        """{
          "policy_id": "policy.one",
          "concept": "growth",
          "namespace": "business.marketing",
          "definition": "One.",
          "version": "0.1.0",
          "rules": [{"rule_id": "one.rule", "description": "One.", "severity": "warn", "match_type": "literal", "patterns": ["one"]}]
        }""",
        encoding="utf-8",
    )
    second.write_text(
        """{
          "policy_id": "policy.two",
          "concept": "safety",
          "namespace": "code.execution",
          "definition": "Two.",
          "version": "0.1.0",
          "rules": [{"rule_id": "two.rule", "description": "Two.", "severity": "block", "match_type": "literal", "patterns": ["two"]}]
        }""",
        encoding="utf-8",
    )

    policies = load_policy_files(tmp_path)

    assert [policy.policy_id for policy in policies] == ["policy.one", "policy.two"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/python -m pytest tests/test_logos_models.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'omniglyph.logos'`.

- [ ] **Step 3: Create the public package exports**

Create `src/omniglyph/logos/__init__.py`:

```python
from omniglyph.logos.loader import load_policy_file, load_policy_files
from omniglyph.logos.models import LogosPolicy, LogosRule

__all__ = [
    "LogosPolicy",
    "LogosRule",
    "load_policy_file",
    "load_policy_files",
]
```

Task 2 and Task 3 will expand these exports after `validator.py` and `decorators.py` exist.

- [ ] **Step 4: Implement models**

Create `src/omniglyph/logos/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

LOGOS_POLICY_SCHEMA = "omniglyph.logos.policy:0.1"
LOGOS_DECISION_SCHEMA = "omniglyph.logos.decision:0.1"
VALID_SEVERITIES = {"warn", "review", "block"}
VALID_MATCH_TYPES = {"literal", "regex"}
VALID_DECISIONS = {"allow", "warn", "review", "block"}


def _require_string(mapping: dict[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _string_list(mapping: dict[str, Any], key: str, required: bool = False) -> list[str]:
    value = mapping.get(key, [])
    if required and not value:
        raise ValueError(f"{key} must contain at least one value")
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{key} must be a list of non-empty strings")
    return list(value)


@dataclass(frozen=True)
class LogosRule:
    rule_id: str
    description: str
    severity: str
    match_type: str
    patterns: list[str]
    allow_context: list[str] = field(default_factory=list)
    source: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, mapping: dict[str, Any]) -> "LogosRule":
        severity = _require_string(mapping, "severity")
        if severity not in VALID_SEVERITIES:
            raise ValueError(f"severity must be one of {sorted(VALID_SEVERITIES)}")
        match_type = _require_string(mapping, "match_type")
        if match_type not in VALID_MATCH_TYPES:
            raise ValueError(f"match_type must be one of {sorted(VALID_MATCH_TYPES)}")
        source = mapping.get("source", {})
        if source is None:
            source = {}
        if not isinstance(source, dict):
            raise ValueError("source must be an object")
        return cls(
            rule_id=_require_string(mapping, "rule_id"),
            description=_require_string(mapping, "description"),
            severity=severity,
            match_type=match_type,
            patterns=_string_list(mapping, "patterns", required=True),
            allow_context=_string_list(mapping, "allow_context"),
            source=dict(source),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "description": self.description,
            "severity": self.severity,
            "match_type": self.match_type,
            "patterns": self.patterns,
            "allow_context": self.allow_context,
            "source": self.source,
        }


@dataclass(frozen=True)
class LogosPolicy:
    policy_id: str
    concept: str
    namespace: str
    definition: str
    version: str
    rules: list[LogosRule]
    schema: str = LOGOS_POLICY_SCHEMA

    @classmethod
    def from_mapping(cls, mapping: dict[str, Any]) -> "LogosPolicy":
        rules_value = mapping.get("rules")
        if not isinstance(rules_value, list) or not rules_value:
            raise ValueError("rules must contain at least one rule")
        rules = []
        for item in rules_value:
            if not isinstance(item, dict):
                raise ValueError("each rule must be an object")
            rules.append(LogosRule.from_mapping(item))
        return cls(
            policy_id=_require_string(mapping, "policy_id"),
            concept=_require_string(mapping, "concept"),
            namespace=_require_string(mapping, "namespace"),
            definition=_require_string(mapping, "definition"),
            version=_require_string(mapping, "version"),
            rules=rules,
            schema=mapping.get("schema", LOGOS_POLICY_SCHEMA),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "policy_id": self.policy_id,
            "concept": self.concept,
            "namespace": self.namespace,
            "definition": self.definition,
            "version": self.version,
            "rules": [rule.to_dict() for rule in self.rules],
        }


@dataclass(frozen=True)
class LogosFinding:
    rule_id: str
    severity: str
    match_type: str
    matched: str
    pattern: str
    evidence: str
    description: str
    source: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "match_type": self.match_type,
            "matched": self.matched,
            "pattern": self.pattern,
            "evidence": self.evidence,
            "description": self.description,
            "source": self.source,
        }


@dataclass(frozen=True)
class LogosDecision:
    decision: str
    status: str
    namespace: str
    concept: str
    policy_id: str
    policy_version: str
    findings: list[LogosFinding]
    limits: list[str] = field(default_factory=list)
    schema: str = LOGOS_DECISION_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        if self.decision not in VALID_DECISIONS:
            raise ValueError(f"decision must be one of {sorted(VALID_DECISIONS)}")
        return {
            "schema": self.schema,
            "decision": self.decision,
            "status": self.status,
            "namespace": self.namespace,
            "concept": self.concept,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "findings": [finding.to_dict() for finding in self.findings],
            "limits": self.limits,
            "message": self.message,
        }

    @property
    def message(self) -> str:
        if self.decision == "allow":
            return f"Action allowed by {self.namespace} {self.concept} policy."
        return f"Action {self.decision} by {self.namespace} {self.concept} policy."
```

- [ ] **Step 5: Implement JSON loader**

Create `src/omniglyph/logos/loader.py`:

```python
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
    return [load_policy_file(item) for item in sorted(policy_path.glob("*.json"))]
```

- [ ] **Step 6: Run model/loader tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_logos_models.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/omniglyph/logos/__init__.py src/omniglyph/logos/models.py src/omniglyph/logos/loader.py tests/test_logos_models.py
git commit -m "feat: add LogosGate policy models"
```

---

### Task 2: Add Matcher and Validator

**Files:**
- Create: `src/omniglyph/logos/matcher.py`
- Create: `src/omniglyph/logos/validator.py`
- Test: `tests/test_logos_validator.py`

- [ ] **Step 1: Write failing validator tests**

Create `tests/test_logos_validator.py`:

```python
from omniglyph.logos.models import LogosPolicy
from omniglyph.logos.validator import validate_action


def marketing_policy():
    return LogosPolicy.from_mapping(
        {
            "policy_id": "marketing_integrity.growth.v1",
            "concept": "growth",
            "namespace": "business.marketing",
            "definition": "Growth must not fabricate demand.",
            "version": "0.1.0",
            "rules": [
                {
                    "rule_id": "marketing_integrity.no_fake_orders",
                    "description": "Block fake order manipulation.",
                    "severity": "block",
                    "match_type": "literal",
                    "patterns": ["刷单", "fake orders"],
                    "allow_context": ["不要刷单", "avoid fake orders"],
                    "source": {"type": "project_policy", "name": "Fixture", "version": "0.1.0"},
                },
                {
                    "rule_id": "marketing_integrity.review_private_data",
                    "description": "Review plans that collect private data.",
                    "severity": "review",
                    "match_type": "regex",
                    "patterns": ["抓取.{0,8}隐私", "scrape.{0,16}private"],
                    "source": {"type": "project_policy", "name": "Fixture", "version": "0.1.0"},
                },
                {
                    "rule_id": "marketing_integrity.warn_bot_traffic",
                    "description": "Warn on bot traffic language.",
                    "severity": "warn",
                    "match_type": "literal",
                    "patterns": ["机器人流量"],
                },
            ],
        }
    )


def test_validate_action_allows_clean_plan():
    result = validate_action(
        text="通过高质量文章和 SEO 获取自然流量。",
        policy=marketing_policy(),
    )

    assert result["decision"] == "allow"
    assert result["status"] == "pass"
    assert result["findings"] == []


def test_validate_action_blocks_literal_fatal_match():
    result = validate_action(
        text="为了快速增长，我们计划雇佣水军刷单。",
        policy=marketing_policy(),
    )

    assert result["decision"] == "block"
    assert result["status"] == "unsafe"
    assert result["findings"][0]["rule_id"] == "marketing_integrity.no_fake_orders"
    assert result["findings"][0]["matched"] == "刷单"
    assert result["limits"] == ["Blocked by one or more LogosGate policy rules."]


def test_validate_action_respects_allow_context():
    result = validate_action(
        text="本次增长计划明确要求不要刷单，只做自然流量。",
        policy=marketing_policy(),
    )

    assert result["decision"] == "allow"
    assert result["findings"] == []


def test_validate_action_returns_review_for_regex_match():
    result = validate_action(
        text="系统计划抓取用户隐私数据后做精准营销。",
        policy=marketing_policy(),
    )

    assert result["decision"] == "review"
    assert result["status"] == "needs_review"
    assert result["findings"][0]["rule_id"] == "marketing_integrity.review_private_data"
    assert result["limits"] == ["Human review is required before execution."]


def test_validate_action_warns_without_blocking():
    result = validate_action(
        text="分析机器人流量占比，不执行购买。",
        policy=marketing_policy(),
    )

    assert result["decision"] == "warn"
    assert result["status"] == "warn"
    assert result["findings"][0]["severity"] == "warn"
    assert result["limits"] == ["Policy warning should be logged before execution."]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/python -m pytest tests/test_logos_validator.py -v
```

Expected: FAIL with `ModuleNotFoundError` or missing `validate_action`.

- [ ] **Step 3: Implement matcher**

Create `src/omniglyph/logos/matcher.py`:

```python
from __future__ import annotations

import re

from omniglyph.logos.models import LogosFinding, LogosRule


def find_rule_matches(text: str, rule: LogosRule) -> list[LogosFinding]:
    if _is_allowed_context(text, rule.allow_context):
        return []
    if rule.match_type == "literal":
        return _literal_matches(text, rule)
    if rule.match_type == "regex":
        return _regex_matches(text, rule)
    raise ValueError(f"Unsupported match_type: {rule.match_type}")


def _is_allowed_context(text: str, allow_context: list[str]) -> bool:
    normalized_text = text.casefold()
    return any(allowed.casefold() in normalized_text for allowed in allow_context)


def _literal_matches(text: str, rule: LogosRule) -> list[LogosFinding]:
    normalized_text = text.casefold()
    findings = []
    for pattern in rule.patterns:
        if pattern.casefold() not in normalized_text:
            continue
        findings.append(
            LogosFinding(
                rule_id=rule.rule_id,
                severity=rule.severity,
                match_type=rule.match_type,
                matched=pattern,
                pattern=pattern,
                evidence=text,
                description=rule.description,
                source=rule.source,
            )
        )
    return findings


def _regex_matches(text: str, rule: LogosRule) -> list[LogosFinding]:
    findings = []
    for pattern in rule.patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match is None:
            continue
        findings.append(
            LogosFinding(
                rule_id=rule.rule_id,
                severity=rule.severity,
                match_type=rule.match_type,
                matched=match.group(0),
                pattern=pattern,
                evidence=text,
                description=rule.description,
                source=rule.source,
            )
        )
    return findings
```

- [ ] **Step 4: Implement validator**

Create `src/omniglyph/logos/validator.py`:

```python
from __future__ import annotations

from omniglyph.logos.matcher import find_rule_matches
from omniglyph.logos.models import LogosDecision, LogosFinding, LogosPolicy


def validate_action(text: str, policy: LogosPolicy) -> dict:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")
    findings: list[LogosFinding] = []
    for rule in policy.rules:
        findings.extend(find_rule_matches(text, rule))
    decision, status, limits = _decision_from_findings(findings)
    result = LogosDecision(
        decision=decision,
        status=status,
        namespace=policy.namespace,
        concept=policy.concept,
        policy_id=policy.policy_id,
        policy_version=policy.version,
        findings=findings,
        limits=limits,
    )
    return result.to_dict()


def _decision_from_findings(findings: list[LogosFinding]) -> tuple[str, str, list[str]]:
    severities = {finding.severity for finding in findings}
    if "block" in severities:
        return "block", "unsafe", ["Blocked by one or more LogosGate policy rules."]
    if "review" in severities:
        return "review", "needs_review", ["Human review is required before execution."]
    if "warn" in severities:
        return "warn", "warn", ["Policy warning should be logged before execution."]
    return "allow", "pass", []
```

- [ ] **Step 5: Fix public exports if Task 1 used temporary stubs**

Ensure `src/omniglyph/logos/__init__.py` imports from the correct future decorator path:

```python
from omniglyph.logos.decorators import LogosViolationError, logos_gate
from omniglyph.logos.loader import load_policy_file, load_policy_files
from omniglyph.logos.models import LogosDecision, LogosFinding, LogosPolicy, LogosRule
from omniglyph.logos.validator import validate_action

__all__ = [
    "LogosDecision",
    "LogosFinding",
    "LogosPolicy",
    "LogosRule",
    "LogosViolationError",
    "load_policy_file",
    "load_policy_files",
    "logos_gate",
    "validate_action",
]
```

- [ ] **Step 6: Run validator tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_logos_validator.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/omniglyph/logos/__init__.py src/omniglyph/logos/matcher.py src/omniglyph/logos/validator.py tests/test_logos_validator.py
git commit -m "feat: add LogosGate action validator"
```

---

### Task 3: Add Decorator Runtime

**Files:**
- Create: `src/omniglyph/logos/decorators.py`
- Test: `tests/test_logos_decorator.py`

- [ ] **Step 1: Write failing decorator tests**

Create `tests/test_logos_decorator.py`:

```python
from pathlib import Path

import pytest

from omniglyph.logos.decorators import LogosViolationError, logos_gate


def write_policy(path: Path) -> Path:
    path.write_text(
        """{
          "policy_id": "marketing_integrity.growth.v1",
          "concept": "growth",
          "namespace": "business.marketing",
          "definition": "Growth must not fabricate demand.",
          "version": "0.1.0",
          "rules": [
            {
              "rule_id": "marketing_integrity.no_fake_orders",
              "description": "Block fake order manipulation.",
              "severity": "block",
              "match_type": "literal",
              "patterns": ["刷单"],
              "allow_context": ["不要刷单"]
            },
            {
              "rule_id": "marketing_integrity.review_private_data",
              "description": "Review privacy collection.",
              "severity": "review",
              "match_type": "literal",
              "patterns": ["隐私数据"]
            }
          ]
        }""",
        encoding="utf-8",
    )
    return path


def test_logos_gate_allows_safe_plan(tmp_path):
    policy_path = write_policy(tmp_path / "policy.json")
    calls = []

    @logos_gate(policy_path=policy_path)
    def execute(action_plan: str):
        calls.append(action_plan)
        return "executed"

    assert execute("通过自然流量增长") == "executed"
    assert calls == ["通过自然流量增长"]


def test_logos_gate_blocks_unsafe_plan(tmp_path):
    policy_path = write_policy(tmp_path / "policy.json")

    @logos_gate(policy_path=policy_path)
    def execute(action_plan: str):
        return "executed"

    with pytest.raises(LogosViolationError) as error:
        execute("计划雇佣水军刷单")

    assert error.value.result["decision"] == "block"
    assert error.value.result["findings"][0]["matched"] == "刷单"


def test_logos_gate_allows_review_decision_by_default(tmp_path):
    policy_path = write_policy(tmp_path / "policy.json")

    @logos_gate(policy_path=policy_path)
    def execute(action_plan: str):
        return "executed"

    assert execute("需要处理隐私数据") == "executed"


def test_logos_gate_can_block_review_decision(tmp_path):
    policy_path = write_policy(tmp_path / "policy.json")

    @logos_gate(policy_path=policy_path, block_on=("block", "review"))
    def execute(action_plan: str):
        return "executed"

    with pytest.raises(LogosViolationError) as error:
        execute("需要处理隐私数据")

    assert error.value.result["decision"] == "review"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/python -m pytest tests/test_logos_decorator.py -v
```

Expected: FAIL with missing `omniglyph.logos.decorators`.

- [ ] **Step 3: Implement decorators**

Create `src/omniglyph/logos/decorators.py`:

```python
from __future__ import annotations

import functools
from pathlib import Path
from typing import Callable

from omniglyph.logos.loader import load_policy_file
from omniglyph.logos.validator import validate_action


class LogosViolationError(Exception):
    def __init__(self, result: dict):
        super().__init__(result.get("message", "LogosGate policy violation"))
        self.result = result


def logos_gate(policy_path: Path | str, block_on: tuple[str, ...] = ("block",)) -> Callable:
    policy = load_policy_file(policy_path)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(action_plan: str, *args, **kwargs):
            result = validate_action(action_plan, policy)
            if result["decision"] in block_on:
                raise LogosViolationError(result)
            return func(action_plan, *args, **kwargs)

        return wrapper

    return decorator
```

- [ ] **Step 4: Run decorator tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_logos_decorator.py -v
```

Expected: PASS.

- [ ] **Step 5: Run package import check**

Run:

```bash
.venv/bin/python - <<'PY'
from omniglyph.logos import LogosViolationError, logos_gate, validate_action
print(LogosViolationError.__name__, callable(logos_gate), callable(validate_action))
PY
```

Expected:

```text
LogosViolationError True True
```

- [ ] **Step 6: Commit**

```bash
git add src/omniglyph/logos/__init__.py src/omniglyph/logos/decorators.py tests/test_logos_decorator.py
git commit -m "feat: add LogosGate decorator"
```

---

### Task 4: Add Example Policy Packs

**Files:**
- Create: `examples/logos-policies/marketing_integrity.json`
- Create: `examples/logos-policies/code_safety.json`
- Create: `examples/logos-policies/trade_compliance.json`
- Test: `tests/test_logos_policy_examples.py`

- [ ] **Step 1: Write failing example-policy tests**

Create `tests/test_logos_policy_examples.py`:

```python
from pathlib import Path

from omniglyph.logos.loader import load_policy_files
from omniglyph.logos.validator import validate_action


def policies_by_id():
    return {policy.policy_id: policy for policy in load_policy_files(Path("examples/logos-policies"))}


def test_example_policy_files_are_valid():
    policies = load_policy_files(Path("examples/logos-policies"))

    assert {policy.policy_id for policy in policies} == {
        "code_safety.execution.v1",
        "marketing_integrity.growth.v1",
        "trade_compliance.commitment.v1",
    }


def test_marketing_policy_blocks_fake_growth():
    policy = policies_by_id()["marketing_integrity.growth.v1"]

    result = validate_action("计划雇佣水军刷单并制造虚假评价。", policy)

    assert result["decision"] == "block"
    assert result["findings"][0]["rule_id"] == "marketing_integrity.no_fake_orders"


def test_code_safety_policy_blocks_rm_root():
    policy = policies_by_id()["code_safety.execution.v1"]

    result = validate_action("Run rm -rf / to reset the machine.", policy)

    assert result["decision"] == "block"
    assert result["findings"][0]["rule_id"] == "code_safety.no_recursive_root_delete"


def test_trade_policy_requires_review_for_contract_commitment():
    policy = policies_by_id()["trade_compliance.commitment.v1"]

    result = validate_action("向客户承诺最终合同价格和 HS code。", policy)

    assert result["decision"] == "review"
    assert result["findings"][0]["rule_id"] == "trade_compliance.review_contract_commitment"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/python -m pytest tests/test_logos_policy_examples.py -v
```

Expected: FAIL because `examples/logos-policies` does not exist.

- [ ] **Step 3: Add marketing policy**

Create `examples/logos-policies/marketing_integrity.json`:

```json
{
  "policy_id": "marketing_integrity.growth.v1",
  "concept": "growth",
  "namespace": "business.marketing",
  "definition": "Growth must increase durable user value or real profit without fabricating demand, violating consent, or creating hidden systemic debt.",
  "version": "0.1.0",
  "rules": [
    {
      "rule_id": "marketing_integrity.no_fake_orders",
      "description": "Block fake orders, fake reviews, and paid manipulation.",
      "severity": "block",
      "match_type": "literal",
      "patterns": ["刷单", "虚假订单", "虚假评价", "fake orders", "paid fake reviews"],
      "allow_context": ["不要刷单", "禁止刷单", "avoid fake orders"],
      "source": {"type": "project_policy", "name": "LogosGate Genesis Policy Pack", "version": "0.1.0"}
    },
    {
      "rule_id": "marketing_integrity.no_privacy_theft",
      "description": "Block unauthorized privacy theft for growth campaigns.",
      "severity": "block",
      "match_type": "regex",
      "patterns": ["窃取.{0,8}隐私", "steal.{0,16}private"],
      "allow_context": ["禁止窃取隐私", "do not steal private"],
      "source": {"type": "project_policy", "name": "LogosGate Genesis Policy Pack", "version": "0.1.0"}
    },
    {
      "rule_id": "marketing_integrity.review_bot_swarms",
      "description": "Require review before using bot-like traffic tactics.",
      "severity": "review",
      "match_type": "literal",
      "patterns": ["水军", "bot traffic", "机器人流量"],
      "allow_context": ["识别水军", "detect bot traffic"],
      "source": {"type": "project_policy", "name": "LogosGate Genesis Policy Pack", "version": "0.1.0"}
    }
  ]
}
```

- [ ] **Step 4: Add code safety policy**

Create `examples/logos-policies/code_safety.json`:

```json
{
  "policy_id": "code_safety.execution.v1",
  "concept": "safe_execution",
  "namespace": "code.execution",
  "definition": "Code agents must not execute destructive or credential-exfiltrating actions without explicit human approval.",
  "version": "0.1.0",
  "rules": [
    {
      "rule_id": "code_safety.no_recursive_root_delete",
      "description": "Block recursive deletion of root or home paths.",
      "severity": "block",
      "match_type": "regex",
      "patterns": ["rm\\s+-rf\\s+/", "rm\\s+-rf\\s+~"],
      "allow_context": ["do not run rm -rf /", "never run rm -rf /"],
      "source": {"type": "project_policy", "name": "LogosGate Genesis Policy Pack", "version": "0.1.0"}
    },
    {
      "rule_id": "code_safety.no_secret_exfiltration",
      "description": "Block attempts to print or transmit common secret environment variables.",
      "severity": "block",
      "match_type": "regex",
      "patterns": ["printenv\\s+.*(API_KEY|TOKEN|SECRET)", "curl\\s+.*(API_KEY|TOKEN|SECRET)"],
      "allow_context": ["redact API_KEY", "mask TOKEN", "do not printenv"],
      "source": {"type": "project_policy", "name": "LogosGate Genesis Policy Pack", "version": "0.1.0"}
    },
    {
      "rule_id": "code_safety.review_destructive_git",
      "description": "Require review before destructive git reset commands.",
      "severity": "review",
      "match_type": "literal",
      "patterns": ["git reset --hard", "git clean -fd"],
      "allow_context": ["avoid git reset --hard", "explain git reset --hard"],
      "source": {"type": "project_policy", "name": "LogosGate Genesis Policy Pack", "version": "0.1.0"}
    }
  ]
}
```

- [ ] **Step 5: Add trade compliance policy**

Create `examples/logos-policies/trade_compliance.json`:

```json
{
  "policy_id": "trade_compliance.commitment.v1",
  "concept": "commitment",
  "namespace": "trade.compliance",
  "definition": "Trade agents must distinguish drafts from binding commitments and require review for regulated classification, contract promises, or final quotation commitments.",
  "version": "0.1.0",
  "rules": [
    {
      "rule_id": "trade_compliance.review_contract_commitment",
      "description": "Require review before contract, final price, or HS-code commitments.",
      "severity": "review",
      "match_type": "regex",
      "patterns": ["承诺.{0,12}(合同|价格|HS code|海关编码)", "guarantee.{0,24}(contract|final price|HS code)"],
      "allow_context": ["不能承诺", "do not guarantee"],
      "source": {"type": "project_policy", "name": "LogosGate Genesis Policy Pack", "version": "0.1.0"}
    },
    {
      "rule_id": "trade_compliance.warn_draft_quote",
      "description": "Warn when quote language may be mistaken as final.",
      "severity": "warn",
      "match_type": "literal",
      "patterns": ["final quotation", "最终报价"],
      "allow_context": ["not final quotation", "非最终报价"],
      "source": {"type": "project_policy", "name": "LogosGate Genesis Policy Pack", "version": "0.1.0"}
    }
  ]
}
```

- [ ] **Step 6: Run example-policy tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_logos_policy_examples.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add examples/logos-policies tests/test_logos_policy_examples.py
git commit -m "feat: add LogosGate example policies"
```

---

### Task 5: Add CLI Command

**Files:**
- Modify: `src/omniglyph/cli.py`
- Test: `tests/test_logos_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/test_logos_cli.py`:

```python
import json
import subprocess
import sys


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "omniglyph.cli", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_logos_validate_cli_blocks_policy_violation():
    result = run_cli(
        "logos",
        "validate",
        "--policy",
        "examples/logos-policies/marketing_integrity.json",
        "--text",
        "计划雇佣水军刷单。",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["decision"] == "block"
    assert payload["findings"][0]["matched"] == "刷单"


def test_logos_validate_cli_allows_clean_text():
    result = run_cli(
        "logos",
        "validate",
        "--policy",
        "examples/logos-policies/marketing_integrity.json",
        "--text",
        "通过 SEO 和内容增长。",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["decision"] == "allow"


def test_logos_validate_cli_can_read_text_file(tmp_path):
    text_file = tmp_path / "plan.txt"
    text_file.write_text("Run rm -rf / to reset.", encoding="utf-8")

    result = run_cli(
        "logos",
        "validate",
        "--policy",
        "examples/logos-policies/code_safety.json",
        "--text-file",
        str(text_file),
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["decision"] == "block"
    assert payload["findings"][0]["rule_id"] == "code_safety.no_recursive_root_delete"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/python -m pytest tests/test_logos_cli.py -v
```

Expected: FAIL because `logos` command does not exist.

- [ ] **Step 3: Add CLI imports**

Modify top of `src/omniglyph/cli.py` to include:

```python
from omniglyph.logos.loader import load_policy_file
from omniglyph.logos.validator import validate_action
```

- [ ] **Step 4: Add parser commands**

Inside `main()` in `src/omniglyph/cli.py`, after the `scan-code` parser, add:

```python
    logos = subcommands.add_parser("logos")
    logos_subcommands = logos.add_subparsers(dest="logos_command", required=True)
    logos_validate = logos_subcommands.add_parser("validate")
    logos_validate.add_argument("--policy", type=Path, required=True)
    logos_validate.add_argument("--text")
    logos_validate.add_argument("--text-file", type=Path)
    logos_validate.add_argument("--format", choices=["json"], default="json")
```

- [ ] **Step 5: Add command handling**

Inside the command handling chain in `src/omniglyph/cli.py`, after the `scan-code` branch, add:

```python
    elif args.command == "logos":
        if args.logos_command == "validate":
            if bool(args.text) == bool(args.text_file):
                raise SystemExit("Provide exactly one of --text or --text-file")
            text = args.text if args.text is not None else args.text_file.read_text(encoding="utf-8")
            policy = load_policy_file(args.policy)
            result = validate_action(text, policy)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            if result["decision"] == "block":
                raise SystemExit(1)
```

- [ ] **Step 6: Run CLI tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_logos_cli.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/omniglyph/cli.py tests/test_logos_cli.py
git commit -m "feat: add LogosGate CLI validation"
```

---

### Task 6: Add MCP Tool

**Files:**
- Modify: `src/omniglyph/mcp_server.py`
- Modify: `scripts/mcp_smoke_test.sh`
- Test: `tests/test_logos_mcp.py`

- [ ] **Step 1: Write failing MCP tests**

Create `tests/test_logos_mcp.py`:

```python
from omniglyph.mcp_server import build_tools_list, handle_mcp_request


def test_mcp_tools_list_includes_validate_action_policy():
    names = {tool["name"] for tool in build_tools_list()}

    assert "validate_action_policy" in names


def test_mcp_validate_action_policy_blocks_bad_plan():
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 101,
            "method": "tools/call",
            "params": {
                "name": "validate_action_policy",
                "arguments": {
                    "policy_path": "examples/logos-policies/marketing_integrity.json",
                    "text": "计划雇佣水军刷单。",
                },
            },
        }
    )

    payload = response["result"]["content"][0]["json"]
    assert payload["decision"] == "block"
    assert payload["findings"][0]["matched"] == "刷单"


def test_mcp_validate_action_policy_rejects_missing_text():
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 102,
            "method": "tools/call",
            "params": {
                "name": "validate_action_policy",
                "arguments": {"policy_path": "examples/logos-policies/marketing_integrity.json"},
            },
        }
    )

    assert response["error"]["code"] == -32602
    assert "text" in response["error"]["message"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/python -m pytest tests/test_logos_mcp.py -v
```

Expected: FAIL because `validate_action_policy` is not registered.

- [ ] **Step 3: Add MCP imports**

Modify top of `src/omniglyph/mcp_server.py`:

```python
from pathlib import Path

from omniglyph.logos.loader import load_policy_file
from omniglyph.logos.validator import validate_action
```

If `Path` import already exists, do not duplicate it.

- [ ] **Step 4: Add MCP tool descriptor**

Inside `build_tools_list()` in `src/omniglyph/mcp_server.py`, add this tool object before `audit_explain`:

```python
        {
            "name": "validate_action_policy",
            "description": "Validate an agent action plan against a local LogosGate JSON policy file and return allow, warn, review, or block.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "policy_path": {"type": "string", "description": "Path to a local LogosGate JSON policy file."},
                    "text": {"type": "string", "description": "Agent action plan text to validate."},
                },
                "required": ["policy_path", "text"],
            },
        },
```

- [ ] **Step 5: Add MCP tool handler**

Inside `handle_mcp_request()` in `src/omniglyph/mcp_server.py`, before the final unknown-tool error branch, add:

```python
        if tool_name == "validate_action_policy":
            policy_path = arguments.get("policy_path")
            text = arguments.get("text")
            if not isinstance(policy_path, str) or not policy_path.strip():
                return _error(request_id, -32602, "validate_action_policy requires policy_path")
            if not isinstance(text, str) or not text.strip():
                return _error(request_id, -32602, "validate_action_policy requires text")
            policy = load_policy_file(Path(policy_path))
            return _result(request_id, {"content": [{"type": "json", "json": validate_action(text, policy)}]})
```

- [ ] **Step 6: Update MCP smoke script**

Modify `scripts/mcp_smoke_test.sh` so the expected tool set includes `validate_action_policy`.

If the script contains a Python set literal, update it to include:

```python
"validate_action_policy",
```

- [ ] **Step 7: Run MCP tests and smoke test**

Run:

```bash
.venv/bin/python -m pytest tests/test_logos_mcp.py tests/test_mcp.py -v
PYTHON=.venv/bin/python scripts/mcp_smoke_test.sh .venv/bin/omniglyph-mcp
```

Expected: PASS and smoke output includes `validate_action_policy`.

- [ ] **Step 8: Commit**

```bash
git add src/omniglyph/mcp_server.py scripts/mcp_smoke_test.sh tests/test_logos_mcp.py
git commit -m "feat: expose LogosGate MCP tool"
```

---

### Task 7: Add Docs and Final Verification

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `ROADMAP.md`
- Modify: `docs/product/project-status.md`
- Optional create: `docs/use-cases/logosgate.md`

- [ ] **Step 1: Add English README section**

Modify `README.md` and add this section near the existing guardrail / language-security sections:

```markdown
## Experimental: LogosGate Action Policy Firewall

LogosGate is an experimental OmniGlyph layer for deterministic agent action validation.

OmniGlyph answers: **What is this symbol or term?**  
LogosGate answers: **May this agent action proceed under the selected policy namespace?**

Example:

```bash
omniglyph logos validate \
  --policy examples/logos-policies/marketing_integrity.json \
  --text "计划雇佣水军刷单。"
```

Expected decision:

```json
{
  "decision": "block",
  "status": "unsafe"
}
```

This layer is intentionally deterministic. It does not call another LLM to judge the action. It uses source-backed policy data, literal/regex matching, allow-context suppression, and structured evidence.
```
```

If nested Markdown fences break the README, use four backticks around the outer examples.

- [ ] **Step 2: Add Chinese README section**

Modify `README.zh-CN.md` and add:

```markdown
## 实验功能：LogosGate（言法界枢）动作策略防火墙

LogosGate 是 OmniGlyph 的实验性上层模块，用于在 Agent 执行动作前做确定性策略校验。

OmniGlyph 回答：**这个符号或术语是什么？**  
LogosGate 回答：**这个 Agent 动作在当前策略命名空间下能不能执行？**

示例：

```bash
omniglyph logos validate \
  --policy examples/logos-policies/marketing_integrity.json \
  --text "计划雇佣水军刷单。"
```

预期决策：

```json
{
  "decision": "block",
  "status": "unsafe"
}
```

这一层故意保持确定性：不调用第二个大模型做伦理裁判，只使用来源可追溯的策略数据、字面/正则匹配、允许上下文和结构化证据。
```
```

- [ ] **Step 3: Update roadmap**

Modify `ROADMAP.md` and add this under the next `v0.4.x` section:

```markdown
- LogosGate experimental runtime:
  - JSON policy model
  - deterministic action validation
  - `omniglyph logos validate`
  - `validate_action_policy` MCP tool
  - example policies for code safety, marketing integrity, and trade compliance
```

- [ ] **Step 4: Update status document**

Modify `docs/product/project-status.md` and add:

```markdown
## Experimental LogosGate Status

LogosGate is incubating inside OmniGlyph as an experimental action-policy firewall. It is not a universal ethics engine. The MVP validates agent action-plan text against explicit JSON policies and returns deterministic `allow`, `warn`, `review`, or `block` decisions with evidence.
```

- [ ] **Step 5: Run full test suite**

Run:

```bash
.venv/bin/python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 6: Run CLI smoke checks**

Run:

```bash
.venv/bin/omniglyph logos validate --policy examples/logos-policies/marketing_integrity.json --text "计划雇佣水军刷单。"
```

Expected: non-zero exit code with JSON containing `"decision": "block"`.

Run:

```bash
.venv/bin/omniglyph logos validate --policy examples/logos-policies/marketing_integrity.json --text "通过 SEO 和内容增长。"
```

Expected: zero exit code with JSON containing `"decision": "allow"`.

- [ ] **Step 7: Run package and MCP verification**

Run:

```bash
PYTHON=.venv/bin/python scripts/mcp_smoke_test.sh .venv/bin/omniglyph-mcp
.venv/bin/python -m build
.venv/bin/python -m twine check dist/*
```

Expected:

- MCP smoke passes and includes `validate_action_policy`.
- Build succeeds.
- Twine check passes for wheel and sdist.

- [ ] **Step 8: Clean generated build files**

Run:

```bash
rm -rf build dist src/omniglyph.egg-info
```

Expected: generated package artifacts removed.

- [ ] **Step 9: Commit**

```bash
git add README.md README.zh-CN.md ROADMAP.md docs/product/project-status.md docs/use-cases/logosgate.md
git commit -m "docs: document LogosGate MVP"
```

If `docs/use-cases/logosgate.md` was not created, omit it from `git add`.

---

## Final Verification Checklist

After all tasks are complete, run:

```bash
git diff --check
.venv/bin/python -m pytest -q
PYTHON=.venv/bin/python scripts/mcp_smoke_test.sh .venv/bin/omniglyph-mcp
.venv/bin/python -m build
.venv/bin/python -m twine check dist/*
rm -rf build dist src/omniglyph.egg-info
git status --short
```

Expected:

- `git diff --check` reports no whitespace errors.
- Full pytest suite passes.
- MCP smoke test passes.
- Package build succeeds.
- Twine check passes.
- No generated build artifacts remain.

## Self-Review Notes

- Spec coverage: This plan implements the MVP scope in `言法界枢/项目思路.md`: models, JSON policies, validator, decorator, CLI, MCP, example policies, and docs.
- Scope choice: YAML is intentionally deferred to avoid adding dependencies and to keep the first LogosGate runtime deterministic and small.
- Type consistency: The plan uses `LogosPolicy`, `LogosRule`, `LogosFinding`, `LogosDecision`, `validate_action`, `logos_gate`, and `LogosViolationError` consistently.
- Risk note: The validator is intentionally pattern-based. It is useful as a hard gate for explicit rules, not as a universal semantic or legal judgment engine.
