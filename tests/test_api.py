from pathlib import Path

from fastapi.testclient import TestClient

import omniglyph.api as api_module
from omniglyph import __version__
import omniglyph.api as api_module
from omniglyph.api import create_app
from omniglyph.config import Settings
from omniglyph.domain_pack import parse_domain_pack
from omniglyph.normalizer import GlyphRecord
from omniglyph.repository import GlyphRepository, SourceSnapshot
from omniglyph.unihan import parse_unihan_data


def seeded_repository(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    source_id = repository.add_source_snapshot(SourceSnapshot("Unicode Character Database", "file://fixture", "fixture", "sha", "Unicode Terms of Use", "fixture"))
    unihan_id = repository.add_source_snapshot(SourceSnapshot("Unihan Database", "file://unihan", "fixture", "sha-unihan", "Unicode Terms of Use", "unihan"))
    repository.insert_glyph_records([
        GlyphRecord(glyph="铝", unicode_hex="U+94DD", basic_definition="CJK UNIFIED IDEOGRAPH-94DD", source_value="CJK UNIFIED IDEOGRAPH-94DD")
    ], source_id=source_id)
    repository.insert_unihan_properties(list(parse_unihan_data(Path("tests/fixtures/Unihan.sample.txt"))), unihan_id)
    return repository


def seeded_domain_repository(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    source_id = repository.add_source_snapshot(SourceSnapshot("Private Domain Pack", "file://domain", "fixture", "sha-domain", "private", "domain"))
    repository.insert_lexical_entries(list(parse_domain_pack(Path("tests/fixtures/domain_pack.csv"), "private_building_materials")), source_id)
    return repository


def write_api_policy_pack(path: Path) -> None:
    path.mkdir()
    (path / "policy.json").write_text(
        '{"schema":"omniglyph.policy_pack:0.1","policy_id":"company.acme.agent_policy","namespace":"private_acme","name":"ACME Agent Policy","version":"2026.07.05","owner_type":"enterprise","license":"private","visibility":"private"}',
        encoding="utf-8",
    )
    (path / "intents.csv").write_text(
        "intent_id,canonical_phrase,decision,risk_level,requires_approval,allowed_roles,audit_required,parameters_schema\n"
        'network.restart,restart network service,review,high,true,admin,true,"{""type"":""object"",""required"":[""service""],""properties"":{""service"":{""type"":""string"",""enum"":[""network""]}}}"\n',
        encoding="utf-8",
    )


def test_get_glyph_returns_record(tmp_path):
    client = TestClient(create_app(seeded_repository(tmp_path)))

    response = client.get("/api/v1/glyph", params={"char": "铝"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["unicode"]["hex"] == "U+94DD"
    assert payload["lexical"]["pinyin"] == "lǚ"
    assert payload["lexical"]["basic_meaning"] == "aluminum"
    assert payload["properties"][0]["confidence"] == 1.0


def test_get_glyph_rejects_empty_input(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    client = TestClient(create_app(repository))

    response = client.get("/api/v1/glyph", params={"char": ""})

    assert response.status_code == 400


def test_get_glyph_returns_404_for_missing_record(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    client = TestClient(create_app(repository))

    response = client.get("/api/v1/glyph", params={"char": "水"})

    assert response.status_code == 404


def test_get_glyph_returns_404_when_database_is_uninitialized(tmp_path):
    repository = GlyphRepository(tmp_path / "empty.sqlite3")
    client = TestClient(create_app(repository))

    response = client.get("/api/v1/glyph", params={"char": "铝"})

    assert response.status_code == 404


def test_health_check_returns_service_status(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    client = TestClient(create_app(repository))

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "omniglyph",
        "version": __version__,
        "database": {"path": str(repository.sqlite_path), "exists": True},
    }


def test_api_metadata_uses_package_version(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    app = create_app(repository)

    assert __version__ == "0.7.0b0"
    assert app.version == __version__


def test_explain_glyph_endpoint_returns_oes_payload(tmp_path):
    client = TestClient(create_app(seeded_repository(tmp_path)))

    response = client.get("/api/v1/explain/glyph", params={"char": "铝"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema"] == "oes:0.1"
    assert payload["canonical_id"] == "glyph:U+94DD"


def test_explain_term_endpoint_returns_oes_payload(tmp_path):
    client = TestClient(create_app(seeded_domain_repository(tmp_path)))

    response = client.get("/api/v1/explain/term", params={"text": "FOB"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema"] == "oes:0.1"
    assert payload["canonical_id"] == "trade:fob"


def test_security_scan_endpoint_returns_developer_friendly_finding(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    client = TestClient(create_app(repository))

    response = client.post("/api/v1/security/scan", json={"text": "v\u0430lue = 1\n", "source_name": "agent.py"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "warn"
    assert payload["summary"]["risk_level"] == "medium"
    assert payload["findings"][0]["rule_id"] == "unicode-confusable"
    assert payload["findings"][0]["confusable_with"] == "a"
    assert payload["findings"][0]["suggested_action"] == "review"


def test_explain_code_security_endpoint_returns_oes_payload(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    client = TestClient(create_app(repository))

    response = client.post("/api/v1/explain/code-security", json={"text": "v\u0430lue = 1\n", "source_name": "agent.py"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema"] == "oes:0.1"
    assert payload["status"] == "unsafe"
    assert payload["input"]["kind"] == "code"
    assert payload["safety"]["findings"][0]["source_id"] == "source:unicode-confusables:minimal"


def test_audit_explain_endpoint_records_actor_source_and_result(tmp_path):
    client = TestClient(create_app(seeded_domain_repository(tmp_path)))

    response = client.post("/api/v1/audit/explain", json={"actor_id": "user:alice", "kind": "term", "text": "FOB"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["canonical_id"] == "trade:fob"
    assert payload["audit"]["actor"] == {"id": "user:alice"}
    assert payload["audit"]["action"] == "explain_term"
    assert payload["audit"]["status"] == "matched"
    assert payload["audit"]["source_ids"]


def test_audit_explain_endpoint_records_unknown_limits(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    client = TestClient(create_app(repository))

    response = client.post("/api/v1/audit/explain", json={"actor_id": "agent:codex", "kind": "term", "text": "missing"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["status"] == "unknown"
    assert payload["audit"]["unknowns"] == ["No local source-backed term explanation found."]


def test_audit_explain_endpoint_rejects_invalid_glyph_text(tmp_path):
    client = TestClient(create_app(seeded_repository(tmp_path)))

    response = client.post("/api/v1/audit/explain", json={"actor_id": "user:alice", "kind": "glyph", "text": "ab"})

    assert response.status_code == 400
    assert response.json()["detail"] == "glyph audit text must contain exactly one Unicode character"


def test_audit_explain_endpoint_rejects_empty_term_text(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    client = TestClient(create_app(repository))

    response = client.post("/api/v1/audit/explain", json={"actor_id": "user:alice", "kind": "term", "text": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "term audit text must be non-empty"


def test_audit_security_scan_endpoint_records_findings(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    client = TestClient(create_app(repository))

    response = client.post("/api/v1/audit/security-scan", json={"actor_id": "agent:codex", "text": "v\u0430lue = 1\n", "source_name": "agent.py"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["status"] == "warn"
    assert payload["audit"]["action"] == "scan_unicode_security"
    assert payload["audit"]["source_ids"] == ["source:unicode-confusables:minimal"]


def test_guardrail_enforce_output_endpoint_blocks_unknown_terms(tmp_path):
    client = TestClient(create_app(seeded_domain_repository(tmp_path)))

    response = client.post(
        "/api/v1/guardrail/enforce-output",
        json={"terms": ["FOB", "HS 7604.99X"], "actor_id": "agent:quote"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema"] == "omniglyph.guardrail:0.1"
    assert payload["decision"] == "block"
    assert payload["unknown"] == ["HS 7604.99X"]
    assert payload["audit"]["actor"] == {"id": "agent:quote"}


def test_guardrail_enforce_output_endpoint_accepts_policy_modes(tmp_path):
    client = TestClient(create_app(seeded_domain_repository(tmp_path)))

    response = client.post(
        "/api/v1/guardrail/enforce-output",
        json={"terms": ["FOB", "HS 7604.99X"], "policy": {"unknown_action": "review"}},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "review"
    assert payload["severity"] == "medium"
    assert payload["review_packet"]["summary"] == {
        "term_count": 1,
        "group_count": 1,
        "actions": ["review"],
        "classes": ["unknown"],
    }
    assert payload["review_packet"]["groups"][0]["suggested_host_action"] == "Route to human review or regenerate with verified terms only."


def test_lexicon_namespaces_endpoint_lists_loaded_packs(tmp_path):
    client = TestClient(create_app(seeded_domain_repository(tmp_path)))

    response = client.get("/api/v1/lexicon/namespaces")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema"] == "omniglyph.lexicon_namespaces:0.1"
    assert payload["namespaces"] == [
        {
            "namespace": "private_building_materials",
            "entry_count": 4,
            "alias_count": 7,
            "pack_ids": [],
            "source_names": ["Private Domain Pack"],
        }
    ]


def test_lexicon_validate_pack_endpoint_reports_valid_example_pack(tmp_path):
    client = TestClient(create_app(GlyphRepository(tmp_path / "test.sqlite3")))

    response = client.post("/api/v1/lexicon/validate-pack", json={"path": "examples/lexicon-packs/company_trade_terms"})

    assert response.status_code == 200
    assert response.json()["status"] == "pass"
    assert response.json()["summary"]["entry_count"] == 4


def test_lexicon_validate_pack_endpoint_rejects_paths_outside_configured_root(tmp_path, monkeypatch):
    pack_root = tmp_path / "packs"
    outside_pack = tmp_path / "outside"
    pack_root.mkdir()
    outside_pack.mkdir()
    monkeypatch.setattr(
        api_module,
        "settings",
        Settings(
            data_dir=tmp_path / "data",
            raw_dir=tmp_path / "data" / "raw",
            sqlite_path=tmp_path / "data" / "omniglyph.sqlite3",
            lexicon_pack_root=pack_root,
        ),
    )
    client = TestClient(create_app(GlyphRepository(tmp_path / "test.sqlite3")))

    response = client.post("/api/v1/lexicon/validate-pack", json={"path": str(outside_pack)})

    assert response.status_code == 403


def test_policy_validate_pack_endpoint_reports_valid_pack(tmp_path):
    pack_dir = tmp_path / "policy"
    write_api_policy_pack(pack_dir)
    client = TestClient(create_app(GlyphRepository(tmp_path / "test.sqlite3")))

    response = client.post("/api/v1/policy/validate-pack", json={"path": str(pack_dir)})

    assert response.status_code == 200
    assert response.json()["status"] == "pass"
    assert response.json()["policy"]["policy_id"] == "company.acme.agent_policy"


def test_language_security_enforce_intent_can_load_policy_pack_path(tmp_path):
    pack_dir = tmp_path / "policy"
    write_api_policy_pack(pack_dir)
    client = TestClient(create_app(GlyphRepository(tmp_path / "test.sqlite3")))

    response = client.post(
        "/api/v1/language-security/enforce-intent",
        json={
            "intent_id": "network.restart",
            "policy_pack_path": str(pack_dir),
            "actor_role": "admin",
            "parameters": {"service": "network"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "review"
    assert payload["policy"]["policy_id"] == "company.acme.agent_policy"


def test_language_security_enforce_intent_blocks_invalid_policy_pack_parameters(tmp_path):
    pack_dir = tmp_path / "policy"
    write_api_policy_pack(pack_dir)
    client = TestClient(create_app(GlyphRepository(tmp_path / "test.sqlite3")))

    response = client.post(
        "/api/v1/language-security/enforce-intent",
        json={
            "intent_id": "network.restart",
            "policy_pack_path": str(pack_dir),
            "actor_role": "admin",
            "parameters": {"service": 123},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "block"
    assert payload["status"] == "invalid_parameters"


def test_language_security_enforce_intent_rejects_ambiguous_policy_sources(tmp_path):
    pack_dir = tmp_path / "policy"
    write_api_policy_pack(pack_dir)
    client = TestClient(create_app(GlyphRepository(tmp_path / "test.sqlite3")))

    response = client.post(
        "/api/v1/language-security/enforce-intent",
        json={
            "intent_id": "network.restart",
            "manifest": {"intents": []},
            "policy_pack_path": str(pack_dir),
            "actor_role": "admin",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "provide exactly one of manifest or policy_pack_path"


def test_policy_pack_endpoint_rejects_paths_outside_configured_root(tmp_path, monkeypatch):
    pack_root = tmp_path / "policy-packs"
    outside_pack = tmp_path / "outside-policy"
    pack_root.mkdir()
    outside_pack.mkdir()
    monkeypatch.setattr(
        api_module,
        "settings",
        Settings(
            data_dir=tmp_path / "data",
            raw_dir=tmp_path / "data" / "raw",
            sqlite_path=tmp_path / "data" / "omniglyph.sqlite3",
            lexicon_pack_root=None,
            policy_pack_root=pack_root,
        ),
    )
    client = TestClient(create_app(GlyphRepository(tmp_path / "test.sqlite3")))

    response = client.post("/api/v1/policy/validate-pack", json={"path": str(outside_pack)})

    assert response.status_code == 403
