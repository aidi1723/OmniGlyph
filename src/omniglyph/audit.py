import uuid
from datetime import datetime, timezone

AUDIT_SCHEMA = "omniglyph.audit:0.1"


def build_audit_event(
    actor_id: str,
    action: str,
    payload: dict,
    event_id: str | None = None,
    created_at: str | None = None,
) -> dict:
    findings = _extract_findings(payload)
    return {
        "schema": AUDIT_SCHEMA,
        "event_id": event_id or str(uuid.uuid4()),
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "actor": {"id": actor_id},
        "action": action,
        "input": _extract_input(payload),
        "status": payload.get("status"),
        "canonical_id": payload.get("canonical_id"),
        "source_ids": _extract_source_ids(payload, findings),
        "unknowns": _extract_unknowns(payload),
        "findings": findings,
    }


def _extract_input(payload: dict) -> dict:
    if isinstance(payload.get("input"), dict):
        return payload["input"]
    source = payload.get("source", "<unknown>")
    return {"text": source, "kind": "code", "normalized": source}


def _extract_findings(payload: dict) -> list[dict]:
    if isinstance(payload.get("safety"), dict):
        return list(payload["safety"].get("findings") or [])
    return list(payload.get("findings") or [])


def _extract_source_ids(payload: dict, findings: list[dict]) -> list[str]:
    source_ids = {source.get("source_id") for source in payload.get("sources", []) if source.get("source_id")}
    source_ids.update(finding.get("source_id") for finding in findings if finding.get("source_id"))
    return sorted(source_ids)


def _extract_unknowns(payload: dict) -> list[str]:
    if isinstance(payload.get("unknowns"), list):
        return list(payload["unknowns"])
    limits = list(payload.get("limits") or [])
    if payload.get("status") == "unknown" and not limits:
        limits.append("No source-backed result found.")
    return limits
