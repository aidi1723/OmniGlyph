import hashlib
import re
from typing import Any

from omniglyph.code_linter import scan_text
from omniglyph.oes import risk_level_for_findings
from omniglyph.parameter_schema import validate_parameters

LANGUAGE_SECURITY_SCHEMA = "omniglyph.language_security:0.1"
INTENT_SANDBOX_SCHEMA = "omniglyph.intent_sandbox:0.1"
PROMPT_SECURITY_SOURCE_ID = "source:omniglyph:prompt-injection-pack:0.1"
DLP_SOURCE_ID = "source:omniglyph:dlp-pack:0.1"
ALLOWED_INTENT_DECISIONS = {"allow", "review", "block"}

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
    for rule_id, pattern in DLP_PATTERNS:
        for match in list(pattern.finditer(text)):
            findings.append(_dlp_finding(rule_id, match.group(0), match.start(), match.end(), source_name))
    for term in secret_terms or []:
        if not term:
            continue
        pattern = re.compile(re.escape(term))
        for match in list(pattern.finditer(text)):
            findings.append(_dlp_finding("dlp-secret-term", match.group(0), match.start(), match.end(), source_name))
    report = _language_report("output", source_name, text, findings)
    report["redacted_text"] = _redact_matches(text, findings)
    return report


def enforce_intent_manifest(
    intent_id: str,
    manifest: object,
    actor_role: str | None = None,
    parameters: dict[str, Any] | None = None,
) -> dict:
    manifest_findings = validate_intent_manifest(manifest)
    policy = manifest.get("policy") if isinstance(manifest, dict) and isinstance(manifest.get("policy"), dict) else None
    if manifest_findings:
        return _intent_result(
            intent_id,
            "block",
            "invalid_manifest",
            None,
            ["Intent manifest is invalid and cannot authorize actions."],
            parameters,
            policy,
            manifest_findings=manifest_findings,
        )
    assert isinstance(manifest, dict)
    intent = _find_intent(intent_id, manifest)
    if intent is None:
        return _intent_result(
            intent_id,
            "block",
            "unknown",
            None,
            ["Intent is not defined in the manifest."],
            parameters,
            policy,
        )
    if intent.get("decision") == "block":
        return _intent_result(
            intent_id,
            "block",
            "matched",
            intent,
            ["Intent policy blocks this request."],
            parameters,
            policy,
        )
    allowed_roles = intent.get("allowed_roles") or []
    if allowed_roles and actor_role not in allowed_roles:
        return _intent_result(
            intent_id,
            "block",
            "forbidden",
            intent,
            ["Actor role is not allowed to request this intent."],
            parameters,
            policy,
        )
    parameters_schema = intent.get("parameters_schema")
    if isinstance(parameters_schema, dict) and parameters_schema:
        parameter_findings = validate_parameters(parameters or {}, parameters_schema)
        if parameter_findings:
            return _intent_result(
                intent_id,
                "block",
                "invalid_parameters",
                intent,
                ["Intent parameters do not match parameters_schema."],
                parameters,
                policy,
                parameter_findings=parameter_findings,
            )
    limits = []
    decision = "allow"
    if intent.get("decision") == "review" or intent.get("requires_approval"):
        decision = "review"
        limits.append("Intent requires approval before execution.")
    return _intent_result(intent_id, decision, "matched", intent, limits, parameters, policy)


def validate_intent_manifest(manifest: object) -> list[dict[str, str]]:
    if not isinstance(manifest, dict):
        return [_manifest_finding("$", "type", "Intent manifest must be an object.")]

    findings = []
    policy = manifest.get("policy")
    if "policy" in manifest and not isinstance(policy, dict):
        findings.append(_manifest_finding("$.policy", "type", "Policy metadata must be an object."))

    intents = manifest.get("intents")
    if not isinstance(intents, list):
        findings.append(_manifest_finding("$.intents", "type", "Intents must be a list."))
        return findings

    seen_intents: set[str] = set()
    for index, intent in enumerate(intents):
        path = f"$.intents[{index}]"
        if not isinstance(intent, dict):
            findings.append(_manifest_finding(path, "type", "Intent must be an object."))
            continue

        intent_id = intent.get("intent_id")
        if not isinstance(intent_id, str) or not intent_id.strip():
            findings.append(_manifest_finding(f"{path}.intent_id", "required", "Intent ID must be a non-empty string."))
        elif intent_id in seen_intents:
            findings.append(_manifest_finding(f"{path}.intent_id", "unique", "Intent ID must be unique."))
        else:
            seen_intents.add(intent_id)

        if "decision" in intent and intent.get("decision") not in ALLOWED_INTENT_DECISIONS:
            findings.append(
                _manifest_finding(
                    f"{path}.decision",
                    "enum",
                    "Decision must be one of allow, block, review.",
                )
            )

        if "requires_approval" in intent and not isinstance(intent.get("requires_approval"), bool):
            findings.append(
                _manifest_finding(
                    f"{path}.requires_approval",
                    "type",
                    "requires_approval must be a boolean.",
                )
            )

        allowed_roles = intent.get("allowed_roles")
        if "allowed_roles" in intent:
            if not isinstance(allowed_roles, list):
                findings.append(_manifest_finding(f"{path}.allowed_roles", "type", "allowed_roles must be a list."))
            else:
                for role_index, role in enumerate(allowed_roles):
                    if not isinstance(role, str) or not role.strip():
                        findings.append(
                            _manifest_finding(
                                f"{path}.allowed_roles[{role_index}]",
                                "type",
                                "Role must be a non-empty string.",
                            )
                        )

        if "parameters_schema" in intent and not isinstance(intent.get("parameters_schema"), dict):
            findings.append(
                _manifest_finding(
                    f"{path}.parameters_schema",
                    "type",
                    "parameters_schema must be an object.",
                )
            )
    return findings


def _manifest_finding(path: str, rule: str, message: str) -> dict[str, str]:
    return {"path": path, "rule": rule, "message": message}


def _prompt_findings(text: str, source_name: str) -> list[dict]:
    findings = []
    for pattern in PROMPT_INJECTION_PATTERNS:
        for match in pattern.finditer(text):
            findings.append(
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
            )
    return findings


def _dlp_finding(rule_id: str, value: str, start: int, end: int, source_name: str) -> dict:
    return {
        "rule_id": rule_id,
        "severity": "high",
        "message": "Potential sensitive data in model output",
        "source": source_name,
        "match": "[REDACTED]",
        "match_length": len(value),
        "match_sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
        "start": start,
        "end": end,
        "source_id": DLP_SOURCE_ID,
        "suggested_action": "redact",
        "auto_fixable": True,
        "why_it_matters": "Sensitive output can leak credentials, private contacts, or business-confidential terms.",
    }


def _redact_matches(text: str, findings: list[dict]) -> str:
    spans = _coalesce_spans(findings)
    redacted_parts = []
    cursor = 0
    for start, end in spans:
        if end <= cursor:
            continue
        if start > cursor:
            redacted_parts.append(text[cursor:start])
        redacted_parts.append("[REDACTED]")
        cursor = max(cursor, end)
    redacted_parts.append(text[cursor:])
    return "".join(redacted_parts)


def _coalesce_spans(findings: list[dict]) -> list[tuple[int, int]]:
    spans = sorted(
        ((finding["start"], finding["end"]) for finding in findings),
        key=lambda span: (span[0], span[1]),
    )
    merged: list[tuple[int, int]] = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            previous_start, previous_end = merged[-1]
            merged[-1] = (previous_start, max(previous_end, end))
        else:
            merged.append((start, end))
    return merged


def _language_report(surface: str, source_name: str, text: str, findings: list[dict]) -> dict:
    rule_counts: dict[str, int] = {}
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
    policy: dict[str, Any] | None = None,
    parameter_findings: list[dict[str, str]] | None = None,
    manifest_findings: list[dict[str, str]] | None = None,
) -> dict:
    result: dict[str, Any] = {
        "schema": INTENT_SANDBOX_SCHEMA,
        "mode": "deterministic_execution_sandbox",
        "intent_id": intent_id,
        "decision": decision,
        "status": status,
        "intent": intent,
        "parameters": parameters or {},
        "limits": limits,
    }
    if policy:
        result["policy"] = policy
    if parameter_findings:
        result["parameter_findings"] = parameter_findings
    if manifest_findings:
        result["manifest_findings"] = manifest_findings
    return result
