from omniglyph.audit import build_audit_event
from omniglyph.repository import GlyphRepository

GUARDRAIL_SCHEMA = "omniglyph.guardrail:0.1"


def validate_output_terms(repository: GlyphRepository, terms: list[str]) -> dict:
    known = {}
    details = []
    unknown = []
    for term in terms:
        record = repository.find_term(term)
        if record is None:
            unknown.append(term)
            details.append({"term": term, "status": "unknown", "canonical_id": None})
            continue
        if record.get("review_status") != "approved":
            unknown.append(term)
            details.append(
                {
                    "term": term,
                    "status": "unapproved",
                    "canonical_id": record["canonical_id"],
                    "entry_type": record["entry_type"],
                    "review_status": record.get("review_status"),
                    "source_id": record["source_id"],
                    "source_name": record["source_name"],
                }
            )
            continue
        known[term] = record["canonical_id"]
        details.append(
            {
                "term": term,
                "status": "known",
                "canonical_id": record["canonical_id"],
                "entry_type": record["entry_type"],
                "review_status": record.get("review_status"),
                "source_id": record["source_id"],
                "source_name": record["source_name"],
            }
        )
    return {"status": "pass" if not unknown else "warn", "known": known, "unknown": unknown, "details": details}


def enforce_grounded_output(repository: GlyphRepository, terms: list[str], actor_id: str | None = None) -> dict:
    validation = validate_output_terms(repository, terms)
    unknown = validation["unknown"]
    source_ids = sorted(
        {
            detail["source_id"]
            for detail in validation["details"]
            if detail["status"] == "known" and detail.get("source_id")
        }
    )
    limits = []
    if unknown:
        limits.append("Unknown terms must be reviewed or removed before model output is trusted.")
    result = {
        "schema": GUARDRAIL_SCHEMA,
        "mode": "strict_source_grounding",
        "decision": "allow" if not unknown else "block",
        "status": validation["status"],
        "known": validation["known"],
        "unknown": unknown,
        "details": validation["details"],
        "source_ids": source_ids,
        "limits": limits,
    }
    if actor_id is not None:
        result["audit"] = build_audit_event(actor_id, "enforce_grounded_output", _audit_payload(result))
    return result


def _audit_payload(result: dict) -> dict:
    checked_terms = list(result["known"]) + result["unknown"]
    return {
        "input": {"text": ", ".join(checked_terms), "kind": "term_set", "normalized": None},
        "status": result["status"],
        "canonical_id": None,
        "sources": [{"source_id": source_id} for source_id in result["source_ids"]],
        "unknowns": result["unknown"],
        "limits": result["limits"],
        "findings": [],
    }
