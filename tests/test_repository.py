from omniglyph.normalizer import GlyphRecord
from omniglyph.repository import GlyphRepository, SourceSnapshot


def test_repository_inserts_source_snapshot_and_finds_glyph(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    source = SourceSnapshot(
        source_name="Unicode Character Database",
        source_url="file://UnicodeData.sample.txt",
        source_version="fixture",
        sha256="fixture-sha256",
        license="Unicode Terms of Use",
        local_path="tests/fixtures/UnicodeData.sample.txt",
    )
    source_id = repository.add_source_snapshot(source)
    repository.insert_glyph_records([
        GlyphRecord(glyph="A", unicode_hex="U+0041", basic_definition="LATIN CAPITAL LETTER A", source_value="LATIN CAPITAL LETTER A")
    ], source_id=source_id)

    record = repository.find_by_glyph("A")

    assert record is not None
    assert record["glyph"] == "A"
    assert record["unicode"]["hex"] == "U+0041"
    assert record["unicode"]["name"] == "LATIN CAPITAL LETTER A"
    assert record["properties"][0]["confidence"] == 1.0
    assert record["sources"][0]["source_name"] == "Unicode Character Database"


def test_repository_preserves_multiple_source_values_without_overwrite(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    unicode_source = repository.add_source_snapshot(SourceSnapshot("Unicode Character Database", "file://u", "fixture", "sha-u", "Unicode Terms of Use", "u"))
    private_source = repository.add_source_snapshot(SourceSnapshot("Private Domain Pack", "file://p", "fixture", "sha-p", "private", "p"))

    repository.insert_glyph_records([
        GlyphRecord(glyph="铝", unicode_hex="U+94DD", basic_definition="CJK UNIFIED IDEOGRAPH-94DD", source_value="CJK UNIFIED IDEOGRAPH-94DD")
    ], source_id=unicode_source)
    repository.insert_property(
        glyph="铝",
        namespace="private_building_materials",
        name="trade_code",
        value="HS 7604.21",
        source_id=private_source,
        confidence=0.9,
    )

    record = repository.find_by_glyph("铝")

    property_names = {(item["namespace"], item["name"], item["value"]) for item in record["properties"]}
    assert ("unicode", "name", "CJK UNIFIED IDEOGRAPH-94DD") in property_names
    assert ("private_building_materials", "trade_code", "HS 7604.21") in property_names


def test_repository_returns_none_for_unknown_glyph(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()

    assert repository.find_by_glyph("水") is None


def test_repository_imports_unihan_properties_for_existing_glyph(tmp_path):
    from pathlib import Path

    from omniglyph.unihan import parse_unihan_data

    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    unicode_source = repository.add_source_snapshot(SourceSnapshot("Unicode Character Database", "file://u", "fixture", "sha-u2", "Unicode Terms of Use", "u"))
    unihan_source = repository.add_source_snapshot(SourceSnapshot("Unihan Database", "file://unihan", "fixture", "sha-unihan", "Unicode Terms of Use", "unihan"))
    repository.insert_glyph_records([
        GlyphRecord(glyph="铝", unicode_hex="U+94DD", basic_definition="CJK UNIFIED IDEOGRAPH-94DD", source_value="CJK UNIFIED IDEOGRAPH-94DD")
    ], source_id=unicode_source)

    count = repository.insert_unihan_properties(list(parse_unihan_data(Path("tests/fixtures/Unihan.sample.txt"))), unihan_source)
    record = repository.find_by_glyph("铝")

    assert count == 5
    properties = {(item["namespace"], item["name"], item["value"]) for item in record["properties"]}
    assert ("unihan", "kMandarin", "lǚ") in properties
    assert ("unihan", "kDefinition", "aluminum") in properties


def test_repository_shapes_unihan_lexical_fields(tmp_path):
    from pathlib import Path

    from omniglyph.unihan import parse_unihan_data

    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    unicode_source = repository.add_source_snapshot(SourceSnapshot("Unicode Character Database", "file://u", "fixture", "sha-u3", "Unicode Terms of Use", "u"))
    unihan_source = repository.add_source_snapshot(SourceSnapshot("Unihan Database", "file://unihan", "fixture", "sha-unihan2", "Unicode Terms of Use", "unihan"))
    repository.insert_glyph_records([
        GlyphRecord(glyph="铝", unicode_hex="U+94DD", basic_definition="CJK UNIFIED IDEOGRAPH-94DD", source_value="CJK UNIFIED IDEOGRAPH-94DD")
    ], source_id=unicode_source)
    repository.insert_unihan_properties(list(parse_unihan_data(Path("tests/fixtures/Unihan.sample.txt"))), unihan_source)

    record = repository.find_by_glyph("铝")

    assert record["lexical"]["pinyin"] == "lǚ"
    assert record["lexical"]["basic_meaning"] == "aluminum"
    assert record["lexical"]["sources"]["pinyin"] == "Unihan Database"


def test_repository_imports_and_finds_domain_entries(tmp_path):
    from pathlib import Path

    from omniglyph.domain_pack import parse_domain_pack

    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    source_id = repository.add_source_snapshot(SourceSnapshot("Private Domain Pack", "file://domain", "fixture", "sha-domain", "private", "domain"))

    count = repository.insert_lexical_entries(list(parse_domain_pack(Path("tests/fixtures/domain_pack.csv"), "private_building_materials")), source_id)
    entry = repository.find_term("aluminium profile")

    assert count == 4
    assert entry is not None
    assert entry["canonical_id"] == "material:aluminum_profile"
    assert entry["matched_text"] == "aluminium profile"
    assert entry["term"] == "aluminum profile"
    assert entry["traits"] == {"material": "aluminum", "domain": "construction"}


def test_repository_initialization_creates_lookup_indexes(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()

    with repository.connect() as connection:
        index_names = set()
        for table in ("glyph_property", "lexical_entry", "lexical_alias"):
            rows = connection.execute(f"PRAGMA index_list({table})").fetchall()
            index_names.update(row["name"] for row in rows)

    assert "idx_glyph_property_glyph_uid" in index_names
    assert "idx_lexical_entry_normalized_term" in index_names
    assert "idx_lexical_alias_normalized_alias" in index_names
