from __future__ import annotations

import re

from omniglyph.logos.models import LogosFinding, LogosRule


def find_rule_matches(text: str, rule: LogosRule) -> list[LogosFinding]:
    folded_text = text.casefold()
    findings = []
    for pattern in rule.patterns:
        if rule.match_type == "literal":
            folded_pattern = pattern.casefold()
            start = folded_text.find(folded_pattern)
            while start != -1:
                end = start + len(folded_pattern)
                if not _is_allowed_context(folded_text, rule.allow_context, start, end):
                    findings.append(_finding(rule, matched=pattern, pattern=pattern, evidence=text))
                start = folded_text.find(folded_pattern, start + 1)
        elif rule.match_type == "regex":
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                if not _is_allowed_context(folded_text, rule.allow_context, match.start(), match.end()):
                    findings.append(_finding(rule, matched=match.group(0), pattern=pattern, evidence=text))
        else:
            raise ValueError(f"unsupported match_type: {rule.match_type}")
    return findings


def _is_allowed_context(folded_text: str, allow_context: list[str], match_start: int, match_end: int) -> bool:
    for context in allow_context:
        folded_context = context.casefold()
        start = folded_text.find(folded_context)
        while start != -1:
            end = start + len(folded_context)
            if start <= match_start and end >= match_end:
                return True
            start = folded_text.find(folded_context, start + 1)
    return False


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
