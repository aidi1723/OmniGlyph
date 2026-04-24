from pathlib import Path

from fastapi.testclient import TestClient

from omniglyph.api import create_app
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
    assert response.json() == {"status": "ok", "service": "omniglyph", "version": "0.2.0b0"}
