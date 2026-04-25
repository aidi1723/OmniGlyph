OES_SCHEMA = "oes:0.1"

STATUS_VALUES = {"matched", "partial", "unknown", "ambiguous", "unsafe"}
RISK_LEVELS = {"none", "low", "medium", "high", "critical"}

HIGH_RISK_RULES = {"unicode-bidi-control", "unicode-control-character"}
MEDIUM_RISK_RULES = {
    "unicode-confusable",
    "unicode-cross-script-homoglyph-risk",
    "unicode-fullwidth-halfwidth-form",
    "unicode-invisible-format",
    "unicode-nfkc-normalization-change",
}


def empty_safety() -> dict:
    return {"risk_level": "none", "findings": []}


def source_payload(source: dict, confidence: float) -> dict:
    return {
        "source_id": source.get("source_id") or source["id"],
        "source_name": source["source_name"],
        "source_version": source["source_version"],
        "license": source["license"],
        "confidence": confidence,
    }


def unknown_payload(text: str, kind: str, message: str, normalized: str | None = None) -> dict:
    return {
        "schema": OES_SCHEMA,
        "input": {"text": text, "kind": kind, "normalized": text if normalized is None else normalized},
        "status": "unknown",
        "canonical_id": None,
        "basic_facts": {},
        "lexical": [],
        "concept_links": [],
        "safety": empty_safety(),
        "sources": [],
        "limits": [message],
    }


def risk_level_for_findings(findings: list[dict]) -> str:
    if not findings:
        return "none"
    rule_ids = {finding.get("rule_id") for finding in findings}
    if rule_ids & HIGH_RISK_RULES:
        return "high"
    if rule_ids & MEDIUM_RISK_RULES:
        return "medium"
    return "low"
