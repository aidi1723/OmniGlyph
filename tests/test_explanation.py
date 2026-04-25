from pathlib import Path

from omniglyph.domain_pack import parse_domain_pack
from omniglyph.explanation import explain_glyph, explain_term
from omniglyph.normalizer import GlyphRecord
from omniglyph.repository import GlyphRepository, SourceSnapshot
from omniglyph.unihan import parse_unihan_data


def seeded_glyph_repository(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    unicode_source = repository.add_source_snapshot(SourceSnapshot("Unicode Character Database", "file://fixture", "fixture", "sha-u", "Unicode Terms of Use", "fixture"))
    unihan_source = repository.add_source_snapshot(SourceSnapshot("Unihan Database", "file://unihan", "fixture", "sha-unihan", "Unicode Terms of Use", "unihan"))
    repository.insert_glyph_records([
        GlyphRecord(glyph="铝", unicode_hex="U+94DD", basic_definition="CJK UNIFIED IDEOGRAPH-94DD")
    ], source_id=unicode_source)
    repository.insert_unihan_properties(list(parse_unihan_data(Path("tests/fixtures/Unihan.sample.txt"))), unihan_source)
    return repository


def seeded_domain_repository(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    source_id = repository.add_source_snapshot(SourceSnapshot("Private Domain Pack", "file://domain", "fixture", "sha-domain", "private", "domain"))
    repository.insert_lexical_entries(list(parse_domain_pack(Path("tests/fixtures/domain_pack.csv"), "private_building_materials")), source_id)
    return repository


def test_explain_glyph_returns_oes_payload(tmp_path):
    payload = explain_glyph(seeded_glyph_repository(tmp_path), "铝")

    assert payload["schema"] == "oes:0.1"
    assert payload["status"] == "matched"
    assert payload["canonical_id"] == "glyph:U+94DD"
    assert payload["input"] == {"text": "铝", "kind": "glyph", "normalized": "铝"}
    assert payload["basic_facts"]["unicode_hex"] == "U+94DD"
    assert payload["basic_facts"]["name"] == "CJK UNIFIED IDEOGRAPH-94DD"
    assert payload["lexical"][0]["language"] == "zh"
    assert payload["lexical"][0]["pronunciation"] == "lǚ"
    assert payload["lexical"][0]["definition"] == "aluminum"
    assert payload["safety"] == {"risk_level": "none", "findings": []}
    assert payload["limits"] == []
    assert {source["source_name"] for source in payload["sources"]} == {"Unicode Character Database", "Unihan Database"}


def test_explain_term_returns_oes_payload(tmp_path):
    payload = explain_term(seeded_domain_repository(tmp_path), "FOB")

    assert payload["schema"] == "oes:0.1"
    assert payload["status"] == "matched"
    assert payload["canonical_id"] == "trade:fob"
    assert payload["input"] == {"text": "FOB", "kind": "term", "normalized": "fob"}
    assert payload["basic_facts"] == {}
    assert payload["lexical"][0]["term"] == "FOB"
    assert payload["lexical"][0]["language"] == "en"
    assert payload["lexical"][0]["definition"] == "Free On Board international trade term"
    assert payload["lexical"][0]["entry_type"] == "trade_term"
    assert payload["sources"][0]["source_name"] == "Private Domain Pack"


def test_explain_unknown_values_are_explicit(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()

    glyph_payload = explain_glyph(repository, "水")
    term_payload = explain_term(repository, "missing")

    assert glyph_payload["status"] == "unknown"
    assert glyph_payload["canonical_id"] is None
    assert glyph_payload["limits"] == ["No local source-backed glyph explanation found."]
    assert term_payload["status"] == "unknown"
    assert term_payload["canonical_id"] is None
    assert term_payload["limits"] == ["No local source-backed term explanation found."]
