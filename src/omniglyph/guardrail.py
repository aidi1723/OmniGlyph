from omniglyph.audit import build_audit_event
from omniglyph.repository import GlyphRepository

GUARDRAIL_SCHEMA = "omniglyph.guardrail:0.1"
ALLOWED_ACTIONS = {"allow", "review", "block"}
DEFAULT_POLICY = {
    "unknown_action": "block",
    "unapproved_action": "block",
    "secret_action": "block",
}


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
                    "sensitivity": record.get("sensitivity"),
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
                "sensitivity": record.get("sensitivity"),
                "review_status": record.get("review_status"),
                "source_id": record["source_id"],
                "source_name": record["source_name"],
            }
        )
    return {"status": "pass" if not unknown else "warn", "known": known, "unknown": unknown, "details": details}


def enforce_grounded_output(
    repository: GlyphRepository,
    terms: list[str],
    actor_id: str | None = None,
    policy: dict | None = None,
) -> dict:
    validation = validate_output_terms(repository, terms)
    guardrail_policy, policy_warnings = _normalize_policy(policy)
    details = [_classify_secret_detail(detail) for detail in validation["details"]]
    actions = [_action_for_detail(detail, guardrail_policy) for detail in details]
    decision = _strongest_action(actions)
    risky_count = sum(1 for action in actions if action != "allow" or decision == "allow")
    unknown = [detail["term"] for detail in details if detail["status"] in {"unknown", "unapproved"}]
    source_ids = sorted(
        {
            detail["source_id"]
            for detail in details
            if detail["status"] in {"known", "secret"} and detail.get("source_id")
        }
    )
    limits = _limits_for_details(details, actions)
    result = {
        "schema": GUARDRAIL_SCHEMA,
        "mode": "strict_source_grounding" if policy is None else "policy_source_grounding",
        "decision": decision,
        "status": validation["status"],
        "severity": _severity_for(decision, len(limits)),
        "known": validation["known"],
        "unknown": unknown,
        "details": details,
        "source_ids": source_ids,
        "limits": limits,
    }
    if policy_warnings:
        result["policy_warnings"] = policy_warnings
    if actor_id is not None:
        result["audit"] = build_audit_event(actor_id, "enforce_grounded_output", _audit_payload(result))
    return result


def _normalize_policy(policy: dict | None) -> tuple[dict[str, str], list[str]]:
    normalized = dict(DEFAULT_POLICY)
    warnings = []
    for key in DEFAULT_POLICY:
        value = (policy or {}).get(key, normalized[key])
        if value not in ALLOWED_ACTIONS:
            warnings.append(f"{key} must be one of allow, block, review; using block.")
            value = "block"
        normalized[key] = value
    return normalized, warnings


def _classify_secret_detail(detail: dict) -> dict:
    if detail["status"] == "known" and detail.get("sensitivity") == "secret":
        classified = dict(detail)
        classified["status"] = "secret"
        return classified
    return detail


def _action_for_detail(detail: dict, policy: dict[str, str]) -> str:
    if detail["status"] == "unknown":
        return policy["unknown_action"]
    if detail["status"] == "unapproved":
        return policy["unapproved_action"]
    if detail["status"] == "secret":
        return policy["secret_action"]
    return "allow"


def _strongest_action(actions: list[str]) -> str:
    if "block" in actions:
        return "block"
    if "review" in actions:
        return "review"
    return "allow"


def _severity_for(decision: str, risky_detail_count: int) -> str:
    if decision == "block":
        return "high"
    if decision == "review":
        return "medium"
    if risky_detail_count:
        return "low"
    return "none"


def _limits_for_details(details: list[dict], actions: list[str]) -> list[str]:
    limits = []
    for detail, action in zip(details, actions, strict=True):
        limit = _limit_for(action, detail)
        if limit and limit not in limits:
            limits.append(limit)
    return limits


def _limit_for(action: str, detail: dict) -> str | None:
    status = detail["status"]
    if status == "known":
        return None
    label = {
        "unknown": "Unknown terms",
        "unapproved": "Unapproved terms",
        "secret": "Secret terms",
    }.get(status)
    if label is None:
        return None
    if action == "block":
        return f"{label} must be reviewed or removed before model output is trusted."
    if action == "review":
        return f"{label} require review before output is trusted."
    return f"{label} were allowed by output policy."


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
