from __future__ import annotations

from omniglyph.logos.matcher import find_rule_matches
from omniglyph.logos.models import LogosDecision, LogosPolicy


DECISION_OUTCOMES = {
    "block": ("unsafe", ["Blocked by one or more LogosGate policy rules."]),
    "review": ("needs_review", ["Human review is required before execution."]),
    "warn": ("warn", ["Policy warning should be logged before execution."]),
    "allow": ("pass", []),
}


def validate_action(text: str, policy: LogosPolicy) -> dict:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")

    findings = []
    for rule in policy.rules:
        findings.extend(find_rule_matches(text, rule))

    decision = _decision_for_findings(findings)
    status, limits = DECISION_OUTCOMES[decision]
    return LogosDecision(
        decision=decision,
        status=status,
        namespace=policy.namespace,
        concept=policy.concept,
        policy_id=policy.policy_id,
        policy_version=policy.version,
        findings=findings,
        limits=limits,
    ).to_dict()


def _decision_for_findings(findings):
    severities = {finding.severity for finding in findings}
    if "block" in severities:
        return "block"
    if "review" in severities:
        return "review"
    if "warn" in severities:
        return "warn"
    return "allow"
