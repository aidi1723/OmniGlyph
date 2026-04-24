from pathlib import Path

from fastapi.testclient import TestClient

from omniglyph.api import create_app
from omniglyph.domain_pack import parse_domain_pack
from omniglyph.normalizer import GlyphRecord
from omniglyph.repository import GlyphRepository, SourceSnapshot


def seeded_repository(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    unicode_source = repository.add_source_snapshot(SourceSnapshot("Unicode Character Database", "file://fixture", "fixture", "sha-u", "Unicode Terms of Use", "fixture"))
    domain_source = repository.add_source_snapshot(SourceSnapshot("Private Domain Pack", "file://domain", "fixture", "sha-d", "private", "domain"))
    repository.insert_glyph_records([
        GlyphRecord(glyph="铝", unicode_hex="U+94DD", basic_definition="CJK UNIFIED IDEOGRAPH-94DD")
    ], source_id=unicode_source)
    repository.insert_lexical_entries(list(parse_domain_pack(Path("tests/fixtures/domain_pack.csv"), "private_building_materials")), domain_source)
    return repository


def test_get_term_returns_domain_entry(tmp_path):
    client = TestClient(create_app(seeded_repository(tmp_path)))

    response = client.get("/api/v1/term", params={"text": "aluminium profile"})

    assert response.status_code == 200
    assert response.json()["canonical_id"] == "material:aluminum_profile"
    assert response.json()["matched_text"] == "aluminium profile"


def test_get_term_returns_404_for_unknown_term(tmp_path):
    client = TestClient(create_app(seeded_repository(tmp_path)))

    response = client.get("/api/v1/term", params={"text": "unknown term"})

    assert response.status_code == 404


def test_post_normalize_returns_glyph_term_and_unknown_results(tmp_path):
    client = TestClient(create_app(seeded_repository(tmp_path)))

    response = client.post("/api/v1/normalize", json={"tokens": ["铝", "FOB", "unknown"]})

    assert response.status_code == 200
    payload = response.json()
    assert payload["results"][0]["type"] == "glyph"
    assert payload["results"][0]["canonical_id"] == "glyph:U+94DD"
    assert payload["results"][1]["type"] == "trade_term"
    assert payload["results"][1]["canonical_id"] == "trade:fob"
    assert payload["results"][2]["status"] == "unknown"


def test_post_normalize_compact_mode(tmp_path):
    client = TestClient(create_app(seeded_repository(tmp_path)))

    response = client.post("/api/v1/normalize", params={"mode": "compact"}, json={"tokens": ["铝", "FOB", "unknown"]})

    assert response.status_code == 200
    assert response.json() == {"known": {"铝": "glyph:U+94DD", "FOB": "trade:fob"}, "unknown": ["unknown"]}
