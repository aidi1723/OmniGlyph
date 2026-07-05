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


def test_enforce_grounded_output_can_review_unknown_terms_by_policy(tmp_path):
    repository = seeded_repository(tmp_path)

    result = enforce_grounded_output(repository, ["FOB", "HS 7604.99X"], policy={"unknown_action": "review"})

    assert result["decision"] == "review"
    assert result["severity"] == "medium"
    assert result["limits"] == ["Unknown terms require review before output is trusted."]


def test_enforce_grounded_output_can_allow_unknown_terms_by_policy(tmp_path):
    repository = seeded_repository(tmp_path)

    result = enforce_grounded_output(repository, ["HS 7604.99X"], policy={"unknown_action": "allow"})

    assert result["decision"] == "allow"
    assert result["status"] == "warn"
    assert result["severity"] == "low"
    assert result["limits"] == ["Unknown terms were allowed by output policy."]


def test_enforce_grounded_output_allows_fully_known_terms(tmp_path):
    repository = seeded_repository(tmp_path)

    result = enforce_grounded_output(repository, ["FOB", "tempered glass"])

    assert result["decision"] == "allow"
    assert result["status"] == "pass"
    assert result["severity"] == "none"
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


def test_enforce_grounded_output_can_review_unapproved_terms_by_policy(tmp_path):
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

    result = enforce_grounded_output(repository, ["Draft Spec"], policy={"unapproved_action": "review"})

    assert result["decision"] == "review"
    assert result["severity"] == "medium"
    assert result["details"][0]["status"] == "unapproved"


def test_enforce_grounded_output_blocks_secret_terms_by_default(tmp_path):
    source = tmp_path / "terms.csv"
    source.write_text(
        "term,canonical_id,entry_type,language,aliases,definition,traits,sensitivity,review_status\n"
        'Floor Price,company:floor_price,confidential_term,en,,Internal floor price,"{}",secret,approved\n',
        encoding="utf-8",
    )
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    source_id = repository.add_source_snapshot(SourceSnapshot("Private Domain Pack", "file://domain", "fixture", "sha-secret", "private", "domain"))
    repository.insert_lexical_entries(list(parse_domain_pack(source, "private_acme")), source_id)

    result = enforce_grounded_output(repository, ["Floor Price"])

    assert result["decision"] == "block"
    assert result["severity"] == "high"
    assert result["details"][0]["status"] == "secret"


def test_enforce_grounded_output_invalid_policy_action_falls_back_to_block(tmp_path):
    repository = seeded_repository(tmp_path)

    result = enforce_grounded_output(repository, ["HS 7604.99X"], policy={"unknown_action": "escalate"})

    assert result["decision"] == "block"
    assert result["policy_warnings"] == ["unknown_action must be one of allow, block, review; using block."]


def test_enforce_grounded_output_includes_review_packet_for_default_unknown_block(tmp_path):
    repository = seeded_repository(tmp_path)

    result = enforce_grounded_output(repository, ["FOB", "HS 7604.99X"])

    assert result["decision"] == "block"
    assert result["review_packet"] == {
        "status": "needs_review",
        "summary": {
            "term_count": 1,
            "group_count": 1,
            "actions": ["block"],
            "classes": ["unknown"],
        },
        "groups": [
            {
                "class": "unknown",
                "action": "block",
                "reason": "Term is not present in the local fact base.",
                "suggested_host_action": "Block delivery until the term is reviewed, removed, or added to an approved source.",
                "terms": [{"term": "HS 7604.99X", "canonical_id": None}],
            }
        ],
    }


def test_enforce_grounded_output_review_packet_reflects_review_policy(tmp_path):
    repository = seeded_repository(tmp_path)

    result = enforce_grounded_output(repository, ["HS 7604.99X"], policy={"unknown_action": "review"})

    assert result["decision"] == "review"
    assert result["review_packet"]["summary"]["actions"] == ["review"]
    assert result["review_packet"]["groups"][0]["action"] == "review"
    assert result["review_packet"]["groups"][0]["suggested_host_action"] == "Route to human review or regenerate with verified terms only."


def test_enforce_grounded_output_omits_review_packet_for_safe_output(tmp_path):
    repository = seeded_repository(tmp_path)

    result = enforce_grounded_output(repository, ["FOB", "tempered glass"])

    assert result["decision"] == "allow"
    assert "review_packet" not in result


def test_enforce_grounded_output_groups_mixed_unknown_and_secret_terms(tmp_path):
    source = tmp_path / "terms.csv"
    source.write_text(
        "term,canonical_id,entry_type,language,aliases,definition,traits,sensitivity,review_status\n"
        'Floor Price,company:floor_price,confidential_term,en,,Internal floor price,"{}",secret,approved\n',
        encoding="utf-8",
    )
    repository = seeded_repository(tmp_path)
    source_id = repository.add_source_snapshot(SourceSnapshot("Private Domain Pack", "file://secret", "fixture", "sha-secret", "private", "domain"))
    repository.insert_lexical_entries(list(parse_domain_pack(source, "private_acme")), source_id)

    result = enforce_grounded_output(
        repository,
        ["HS 7604.99X", "Floor Price"],
        policy={"unknown_action": "review", "secret_action": "block"},
    )

    assert result["decision"] == "block"
    assert result["review_packet"]["summary"] == {
        "term_count": 2,
        "group_count": 2,
        "actions": ["block", "review"],
        "classes": ["unknown", "secret"],
    }
    assert result["review_packet"]["groups"][0]["class"] == "unknown"
    assert result["review_packet"]["groups"][0]["action"] == "review"
    assert result["review_packet"]["groups"][0]["terms"] == [{"term": "HS 7604.99X", "canonical_id": None}]
    assert result["review_packet"]["groups"][1]["class"] == "secret"
    assert result["review_packet"]["groups"][1]["action"] == "block"
    assert result["review_packet"]["groups"][1]["terms"][0]["term"] == "Floor Price"
    assert result["review_packet"]["groups"][1]["terms"][0]["canonical_id"] == "company:floor_price"
    assert result["review_packet"]["groups"][1]["terms"][0]["sensitivity"] == "secret"
    assert result["review_packet"]["groups"][1]["terms"][0]["source_name"] == "Private Domain Pack"


def test_enforce_grounded_output_deduplicates_repeated_risky_terms_in_review_packet(tmp_path):
    repository = seeded_repository(tmp_path)

    result = enforce_grounded_output(repository, ["HS 7604.99X", "HS 7604.99X"])

    assert result["unknown"] == ["HS 7604.99X", "HS 7604.99X"]
    assert result["review_packet"]["summary"]["term_count"] == 1
    assert result["review_packet"]["groups"][0]["terms"] == [{"term": "HS 7604.99X", "canonical_id": None}]


def test_enforce_grounded_output_review_packet_includes_unapproved_terms(tmp_path):
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

    result = enforce_grounded_output(repository, ["Draft Spec"], policy={"unapproved_action": "review"})

    assert result["decision"] == "review"
    assert result["review_packet"]["summary"] == {
        "term_count": 1,
        "group_count": 1,
        "actions": ["review"],
        "classes": ["unapproved"],
    }
    assert result["review_packet"]["groups"][0] == {
        "class": "unapproved",
        "action": "review",
        "reason": "Term exists in the local fact base but is not approved.",
        "suggested_host_action": "Route to the source owner or reviewer before delivery.",
        "terms": [
            {
                "term": "Draft Spec",
                "canonical_id": "company:draft_spec",
                "entry_type": "product_spec",
                "sensitivity": "normal",
                "review_status": "draft",
                "source_id": source_id,
                "source_name": "Private Domain Pack",
            }
        ],
    }


def test_enforce_grounded_output_review_packet_records_allowed_unknown_terms(tmp_path):
    repository = seeded_repository(tmp_path)

    result = enforce_grounded_output(repository, ["HS 7604.99X"], policy={"unknown_action": "allow"})

    assert result["decision"] == "allow"
    assert result["severity"] == "low"
    assert result["review_packet"]["summary"] == {
        "term_count": 1,
        "group_count": 1,
        "actions": ["allow"],
        "classes": ["unknown"],
    }
    assert result["review_packet"]["groups"][0] == {
        "class": "unknown",
        "action": "allow",
        "reason": "Term is not present in the local fact base.",
        "suggested_host_action": "Deliver only if the host policy accepts unsupported terms.",
        "terms": [{"term": "HS 7604.99X", "canonical_id": None}],
    }
