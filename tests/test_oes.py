from omniglyph.oes import (
    OES_SCHEMA,
    RISK_LEVELS,
    STATUS_VALUES,
    risk_level_for_findings,
    source_payload,
    unknown_payload,
)


def test_oes_protocol_constants_are_stable():
    assert OES_SCHEMA == "oes:0.1"
    assert STATUS_VALUES == {"matched", "partial", "unknown", "ambiguous", "unsafe"}
    assert RISK_LEVELS == {"none", "low", "medium", "high", "critical"}


def test_unknown_payload_keeps_missing_facts_explicit():
    payload = unknown_payload("missing", "term", "No local source-backed term explanation found.", normalized="missing")

    assert payload["schema"] == OES_SCHEMA
    assert payload["input"] == {"text": "missing", "kind": "term", "normalized": "missing"}
    assert payload["status"] == "unknown"
    assert payload["canonical_id"] is None
    assert payload["basic_facts"] == {}
    assert payload["lexical"] == []
    assert payload["concept_links"] == []
    assert payload["safety"] == {"risk_level": "none", "findings": []}
    assert payload["sources"] == []
    assert payload["limits"] == ["No local source-backed term explanation found."]


def test_source_payload_preserves_required_provenance():
    source = {"id": "source:test", "source_name": "Test Source", "source_version": "fixture", "license": "Apache-2.0"}

    payload = source_payload(source, confidence=0.75)

    assert payload == {
        "source_id": "source:test",
        "source_name": "Test Source",
        "source_version": "fixture",
        "license": "Apache-2.0",
        "confidence": 0.75,
    }


def test_risk_level_for_findings_promotes_security_risk():
    assert risk_level_for_findings([]) == "none"
    assert risk_level_for_findings([{"rule_id": "unicode-confusable"}]) == "medium"
    assert risk_level_for_findings([{"rule_id": "unicode-bidi-control"}]) == "high"
