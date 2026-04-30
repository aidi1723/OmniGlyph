from __future__ import annotations

import re
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


def _validate_regex_patterns(rule_id: str, patterns: list[str]) -> None:
    for index, pattern in enumerate(patterns):
        try:
            re.compile(pattern)
        except re.error as error:
            raise ValueError(
                f"invalid regex pattern for rule {rule_id} at index {index}: {pattern!r}: {error}"
            ) from error


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
        rule_id = _require_string(mapping, "rule_id")
        severity = _require_string(mapping, "severity")
        if severity not in VALID_SEVERITIES:
            raise ValueError(f"severity must be one of {sorted(VALID_SEVERITIES)}")
        match_type = _require_string(mapping, "match_type")
        if match_type not in VALID_MATCH_TYPES:
            raise ValueError(f"match_type must be one of {sorted(VALID_MATCH_TYPES)}")
        patterns = _string_list(mapping, "patterns", required=True)
        if match_type == "regex":
            _validate_regex_patterns(rule_id, patterns)
        source = mapping.get("source", {})
        if source is None:
            source = {}
        if not isinstance(source, dict):
            raise ValueError("source must be an object")
        return cls(
            rule_id=rule_id,
            description=_require_string(mapping, "description"),
            severity=severity,
            match_type=match_type,
            patterns=patterns,
            allow_context=_string_list(mapping, "allow_context"),
            source=dict(source),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "description": self.description,
            "severity": self.severity,
            "match_type": self.match_type,
            "patterns": list(self.patterns),
            "allow_context": list(self.allow_context),
            "source": dict(self.source),
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
        schema = mapping.get("schema", LOGOS_POLICY_SCHEMA)
        if not isinstance(schema, str) or not schema.strip():
            raise ValueError("schema must be a non-empty string")
        return cls(
            policy_id=_require_string(mapping, "policy_id"),
            concept=_require_string(mapping, "concept"),
            namespace=_require_string(mapping, "namespace"),
            definition=_require_string(mapping, "definition"),
            version=_require_string(mapping, "version"),
            rules=rules,
            schema=schema,
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
            "source": dict(self.source),
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

    @property
    def message(self) -> str:
        if self.decision == "allow":
            return f"Action allowed by {self.namespace} {self.concept} policy."
        return f"Action {self.decision} by {self.namespace} {self.concept} policy."

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
            "limits": list(self.limits),
            "message": self.message,
        }
