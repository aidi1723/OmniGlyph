from omniglyph.audit import build_audit_event
from omniglyph.code_linter import scan_text
from omniglyph.oes import unknown_payload


def test_audit_event_from_matched_oes_explanation_records_actor_sources_and_input():
    payload = {
        "schema": "oes:0.1",
        "input": {"text": "API", "kind": "term", "normalized": "api"},
        "status": "matched",
        "canonical_id": "software:api",
        "basic_facts": {},
        "lexical": [],
        "concept_links": [],
        "safety": {"risk_level": "none", "findings": []},
        "sources": [{"source_id": "source:software-dev:0.1.0", "source_name": "Software Development Domain Pack"}],
        "limits": [],
    }

    event = build_audit_event(
        actor_id="user:alice",
        action="explain_term",
        payload=payload,
        event_id="evt-test",
        created_at="2026-04-25T00:00:00+00:00",
    )

    assert event["schema"] == "omniglyph.audit:0.1"
    assert event["event_id"] == "evt-test"
    assert event["actor"] == {"id": "user:alice"}
    assert event["action"] == "explain_term"
    assert event["input"] == {"text": "API", "kind": "term", "normalized": "api"}
    assert event["status"] == "matched"
    assert event["canonical_id"] == "software:api"
    assert event["source_ids"] == ["source:software-dev:0.1.0"]
    assert event["unknowns"] == []
    assert event["findings"] == []


def test_audit_event_records_unknown_limits():
    payload = unknown_payload("missing", "term", "No local source-backed term explanation found.", normalized="missing")

    event = build_audit_event(
        actor_id="agent:codex",
        action="explain_term",
        payload=payload,
        event_id="evt-unknown",
        created_at="2026-04-25T00:00:00+00:00",
    )

    assert event["status"] == "unknown"
    assert event["canonical_id"] is None
    assert event["source_ids"] == []
    assert event["unknowns"] == ["No local source-backed term explanation found."]


def test_audit_event_prefers_explicit_unknowns_over_limits():
    payload = {
        "input": {"text": "FOB, HS 7604.99X", "kind": "term_set", "normalized": None},
        "status": "warn",
        "canonical_id": None,
        "sources": [],
        "unknowns": ["HS 7604.99X"],
        "limits": ["Unknown terms must be reviewed or removed before model output is trusted."],
        "findings": [],
    }

    event = build_audit_event(
        actor_id="agent:quote",
        action="enforce_grounded_output",
        payload=payload,
        event_id="evt-guardrail",
        created_at="2026-04-25T00:00:00+00:00",
    )

    assert event["unknowns"] == ["HS 7604.99X"]


def test_audit_event_from_security_scan_records_findings_and_sources():
    report = scan_text("v\u0430lue = 1\n", source_name="agent.py")

    event = build_audit_event(
        actor_id="agent:codex",
        action="scan_unicode_security",
        payload=report,
        event_id="evt-scan",
        created_at="2026-04-25T00:00:00+00:00",
    )

    assert event["input"] == {"text": "agent.py", "kind": "code", "normalized": "agent.py"}
    assert event["status"] == "warn"
    assert event["canonical_id"] is None
    assert event["source_ids"] == ["source:unicode-confusables:minimal"]
    assert event["findings"][0]["rule_id"] == "unicode-confusable"
    assert event["unknowns"] == []
