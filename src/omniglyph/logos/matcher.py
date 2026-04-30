from __future__ import annotations

import re

from omniglyph.logos.models import LogosFinding, LogosRule


def find_rule_matches(text: str, rule: LogosRule) -> list[LogosFinding]:
    folded_text = text.casefold()
    if any(context.casefold() in folded_text for context in rule.allow_context):
        return []

    findings = []
    for pattern in rule.patterns:
        if rule.match_type == "literal":
            if pattern.casefold() in folded_text:
                findings.append(_finding(rule, matched=pattern, pattern=pattern, evidence=text))
        elif rule.match_type == "regex":
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                findings.append(_finding(rule, matched=match.group(0), pattern=pattern, evidence=text))
        else:
            raise ValueError(f"unsupported match_type: {rule.match_type}")
    return findings


def _finding(rule: LogosRule, matched: str, pattern: str, evidence: str) -> LogosFinding:
    return LogosFinding(
        rule_id=rule.rule_id,
        severity=rule.severity,
        match_type=rule.match_type,
        matched=matched,
        pattern=pattern,
        evidence=evidence,
        description=rule.description,
        source=dict(rule.source),
    )
