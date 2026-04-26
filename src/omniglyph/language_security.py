import re
from typing import Any

from omniglyph.code_linter import scan_text
from omniglyph.oes import risk_level_for_findings

LANGUAGE_SECURITY_SCHEMA = "omniglyph.language_security:0.1"
INTENT_SANDBOX_SCHEMA = "omniglyph.intent_sandbox:0.1"
PROMPT_SECURITY_SOURCE_ID = "source:omniglyph:prompt-injection-pack:0.1"
DLP_SOURCE_ID = "source:omniglyph:dlp-pack:0.1"

PROMPT_INJECTION_PATTERNS = [
    re.compile(r"\bignore\s+(all\s+)?(previous|prior|above)\s+instructions?\b", re.IGNORECASE),
    re.compile(r"\breveal\s+(the\s+)?(system|developer)\s+prompt\b", re.IGNORECASE),
    re.compile(r"\bprint\s+(the\s+)?(system|developer)\s+prompt\b", re.IGNORECASE),
    re.compile(r"忽略.{0,8}(前置|之前|以上|所有).{0,8}(规则|指令|提示)", re.IGNORECASE),
    re.compile(r"(系统|开发者).{0,4}(提示|指令).{0,8}(发给我|告诉我|输出|打印)", re.IGNORECASE),
]

DLP_PATTERNS = [
    ("dlp-api-key", re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{15,}\b")),
    ("dlp-aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("dlp-email-address", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
]

LANGUAGE_INPUT_UNICODE_RULES = {
    "unicode-bidi-control",
    "unicode-invisible-format",
    "unicode-control-character",
    "unicode-confusable",
    "unicode-cross-script-homoglyph-risk",
}


def scan_language_input(text: str, source_name: str = "<input>") -> dict:
    unicode_report = scan_text(text, source_name=source_name)
    findings = [
        finding
        for finding in unicode_report["findings"]
        if finding["rule_id"] in LANGUAGE_INPUT_UNICODE_RULES
    ]
    findings.extend(_prompt_findings(text, source_name))
    return _language_report("input", source_name, text, findings)


def scan_output_dlp(text: str, secret_terms: list[str] | None = None, source_name: str = "<output>") -> dict:
    findings = []
    redacted_text = text
    for rule_id, pattern in DLP_PATTERNS:
        for match in list(pattern.finditer(redacted_text)):
            findings.append(_dlp_finding(rule_id, match.group(0), match.start(), match.end(), source_name))
        redacted_text = pattern.sub("[REDACTED]", redacted_text)
    for term in secret_terms or []:
        if not term:
            continue
        pattern = re.compile(re.escape(term))
        for match in list(pattern.finditer(redacted_text)):
            findings.append(_dlp_finding("dlp-secret-term", match.group(0), match.start(), match.end(), source_name))
        redacted_text = pattern.sub("[REDACTED]", redacted_text)
    report = _language_report("output", source_name, text, findings)
    report["redacted_text"] = redacted_text
    return report


def enforce_intent_manifest(
    intent_id: str,
    manifest: dict[str, Any],
    actor_role: str | None = None,
    parameters: dict[str, Any] | None = None,
) -> dict:
    intent = _find_intent(intent_id, manifest)
    if intent is None:
        return _intent_result(intent_id, "block", "unknown", None, ["Intent is not defined in the manifest."], parameters)
    allowed_roles = intent.get("allowed_roles") or []
    if allowed_roles and actor_role not in allowed_roles:
        return _intent_result(intent_id, "block", "forbidden", intent, ["Actor role is not allowed to request this intent."], parameters)
    limits = []
    decision = "allow"
    if intent.get("requires_approval"):
        decision = "review"
        limits.append("Intent requires approval before execution.")
    return _intent_result(intent_id, decision, "matched", intent, limits, parameters)


def _prompt_findings(text: str, source_name: str) -> list[dict]:
    for pattern in PROMPT_INJECTION_PATTERNS:
        match = pattern.search(text)
        if match is not None:
            return [
                {
                    "rule_id": "prompt-injection-directive",
                    "severity": "high",
                    "message": "Prompt-injection directive attempts to override trusted instructions",
                    "source": source_name,
                    "match": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "source_id": PROMPT_SECURITY_SOURCE_ID,
                    "suggested_action": "block",
                    "auto_fixable": False,
                    "why_it_matters": "Instruction-override text can hijack an agent before tool or policy checks run.",
                }
            ]
    return []


def _dlp_finding(rule_id: str, value: str, start: int, end: int, source_name: str) -> dict:
    return {
        "rule_id": rule_id,
        "severity": "high",
        "message": "Potential sensitive data in model output",
        "source": source_name,
        "match": value,
        "start": start,
        "end": end,
        "source_id": DLP_SOURCE_ID,
        "suggested_action": "redact",
        "auto_fixable": True,
        "why_it_matters": "Sensitive output can leak credentials, private contacts, or business-confidential terms.",
    }


def _language_report(surface: str, source_name: str, text: str, findings: list[dict]) -> dict:
    rule_counts = {}
    for finding in findings:
        rule_counts[finding["rule_id"]] = rule_counts.get(finding["rule_id"], 0) + 1
    decision = "allow" if not findings else "block"
    return {
        "schema": LANGUAGE_SECURITY_SCHEMA,
        "surface": surface,
        "source": source_name,
        "decision": decision,
        "status": "pass" if not findings else "unsafe",
        "summary": {
            "scanned_chars": len(text),
            "finding_count": len(findings),
            "risk_level": _language_risk_level(findings),
            "rule_counts": rule_counts,
        },
        "findings": findings,
    }


def _language_risk_level(findings: list[dict]) -> str:
    if any(finding.get("severity") in {"high", "critical"} for finding in findings):
        return "high"
    return risk_level_for_findings(findings)


def _find_intent(intent_id: str, manifest: dict[str, Any]) -> dict | None:
    for intent in manifest.get("intents") or []:
        if intent.get("intent_id") == intent_id:
            return dict(intent)
    return None


def _intent_result(
    intent_id: str,
    decision: str,
    status: str,
    intent: dict | None,
    limits: list[str],
    parameters: dict[str, Any] | None,
) -> dict:
    return {
        "schema": INTENT_SANDBOX_SCHEMA,
        "mode": "deterministic_execution_sandbox",
        "intent_id": intent_id,
        "decision": decision,
        "status": status,
        "intent": intent,
        "parameters": parameters or {},
        "limits": limits,
    }
