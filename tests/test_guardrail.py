from pathlib import Path

from fastapi.testclient import TestClient

from omniglyph.api import create_app
from omniglyph.domain_pack import parse_domain_pack
from omniglyph.guardrail import enforce_grounded_output, validate_output_terms
from omniglyph.repository import GlyphRepository, SourceSnapshot


def seeded_repository(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    source_id = repository.add_source_snapshot(SourceSnapshot("Private Domain Pack", "file://domain", "fixture", "sha-d", "private", "domain"))
    repository.insert_lexical_entries(list(parse_domain_pack(Path("examples/domain-packs/building_materials.csv"), "private_building_materials")), source_id)
    return repository


def test_validate_output_terms_marks_known_and_unknown_terms(tmp_path):
    repository = seeded_repository(tmp_path)

    result = validate_output_terms(repository, ["FOB", "tempered glass", "HS 7604.99X"])

    assert result["status"] == "warn"
    assert result["known"]["FOB"] == "trade:fob"
    assert result["known"]["tempered glass"] == "material:tempered_glass"
    assert result["unknown"] == ["HS 7604.99X"]


def test_validate_output_terms_passes_when_all_terms_are_known(tmp_path):
    repository = seeded_repository(tmp_path)

    result = validate_output_terms(repository, ["FOB", "tempered glass"])

    assert result["status"] == "pass"
    assert result["unknown"] == []


def test_guardrail_api_validates_candidate_terms(tmp_path):
    client = TestClient(create_app(seeded_repository(tmp_path)))

    response = client.post("/api/v1/guardrail/validate-output", json={"terms": ["FOB", "HS 7604.99X"]})

    assert response.status_code == 200
    assert response.json()["status"] == "warn"
    assert response.json()["unknown"] == ["HS 7604.99X"]


def test_enforce_grounded_output_blocks_unknown_terms_with_audit_shape(tmp_path):
    repository = seeded_repository(tmp_path)

    result = enforce_grounded_output(repository, ["FOB", "HS 7604.99X"], actor_id="agent:quote")

    assert result["schema"] == "omniglyph.guardrail:0.1"
    assert result["mode"] == "strict_source_grounding"
    assert result["decision"] == "block"
    assert result["status"] == "warn"
    assert result["known"] == {"FOB": "trade:fob"}
    assert result["unknown"] == ["HS 7604.99X"]
    assert result["source_ids"]
    assert result["limits"] == ["Unknown terms must be reviewed or removed before model output is trusted."]
    assert result["audit"]["actor"] == {"id": "agent:quote"}
    assert result["audit"]["action"] == "enforce_grounded_output"
    assert result["audit"]["unknowns"] == ["HS 7604.99X"]


def test_enforce_grounded_output_allows_fully_known_terms(tmp_path):
    repository = seeded_repository(tmp_path)

    result = enforce_grounded_output(repository, ["FOB", "tempered glass"])

    assert result["decision"] == "allow"
    assert result["status"] == "pass"
    assert result["unknown"] == []
    assert result["limits"] == []


def test_validate_output_terms_does_not_trust_unapproved_terms(tmp_path):
    source = tmp_path / "terms.csv"
    source.write_text(
        "term,canonical_id,entry_type,language,aliases,definition,traits,sensitivity,review_status\n"
        'Draft Spec,company:draft_spec,product_spec,en,,Draft only,"{}",normal,draft\n',
        encoding="utf-8",
    )
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    source_id = repository.add_source_snapshot(SourceSnapshot("Private Domain Pack", "file://domain", "fixture", "sha-draft", "private", "domain"))
    repository.insert_lexical_entries(list(parse_domain_pack(source, "private_acme")), source_id)

    result = validate_output_terms(repository, ["Draft Spec"])

    assert result["status"] == "warn"
    assert result["known"] == {}
    assert result["unknown"] == ["Draft Spec"]
    assert result["details"][0]["status"] == "unapproved"
    assert result["details"][0]["review_status"] == "draft"
