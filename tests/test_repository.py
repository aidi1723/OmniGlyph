import threading
from pathlib import Path

import pytest

from omniglyph.domain_pack import DomainEntry
from omniglyph.normalizer import GlyphRecord
from omniglyph.repository import GlyphRepository, SourceSnapshot
from omniglyph.unihan import parse_unihan_data


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


def test_repository_lists_lexicon_namespaces(tmp_path):
    from pathlib import Path

    from omniglyph.domain_pack import parse_domain_pack

    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    first_source = repository.add_source_snapshot(SourceSnapshot("ACME Pack", "file://acme", "2026.04", "sha-acme", "private", "acme"))
    second_source = repository.add_source_snapshot(SourceSnapshot("Beta Pack", "file://beta", "2026.05", "sha-beta", "private", "beta"))
    repository.insert_lexical_entries(list(parse_domain_pack(Path("tests/fixtures/domain_pack.csv"), "private_acme")), first_source)
    repository.insert_lexical_entries(list(parse_domain_pack(Path("examples/domain-packs/building_materials.csv"), "private_beta")), second_source)

    result = repository.list_lexical_namespaces()

    assert result == [
        {"namespace": "private_acme", "entry_count": 4, "alias_count": 7, "pack_ids": [], "source_names": ["ACME Pack"]},
        {"namespace": "private_beta", "entry_count": 9, "alias_count": 23, "pack_ids": [], "source_names": ["Beta Pack"]},
    ]


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


def test_repository_reuses_connections_per_thread(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    main_connection = repository.connect()
    worker_connections = []

    def capture_connection() -> None:
        worker_connections.append(repository.connect())

    thread = threading.Thread(target=capture_connection)
    thread.start()
    thread.join()

    assert repository.connect() is main_connection
    assert worker_connections[0] is not main_connection


def test_repository_repeated_unihan_import_is_idempotent(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    source_id = repository.add_source_snapshot(
        SourceSnapshot(
            "Unihan Database",
            "file://unihan",
            "fixture",
            "sha-unihan-idempotent",
            "Unicode Terms of Use",
            "Unihan.txt",
        )
    )
    properties = list(parse_unihan_data(Path("tests/fixtures/Unihan.sample.txt")))[:1]

    repository.insert_unihan_properties(properties, source_id)
    repository.insert_unihan_properties(properties, source_id)

    with repository.connect() as connection:
        count = connection.execute("SELECT COUNT(*) FROM glyph_property").fetchone()[0]
    assert count == 1


def test_repository_unicode_import_fills_name_after_unihan_import(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    unihan_source = repository.add_source_snapshot(
        SourceSnapshot(
            "Unihan Database",
            "file://unihan",
            "fixture",
            "sha-unihan-order",
            "Unicode Terms of Use",
            "Unihan.txt",
        )
    )
    unicode_source = repository.add_source_snapshot(
        SourceSnapshot(
            "Unicode Character Database",
            "file://unicode",
            "fixture",
            "sha-unicode-order",
            "Unicode Terms of Use",
            "UnicodeData.txt",
        )
    )
    properties = list(parse_unihan_data(Path("tests/fixtures/Unihan.sample.txt")))[:1]
    repository.insert_unihan_properties(properties, unihan_source)
    repository.insert_glyph_records(
        [GlyphRecord("铝", "U+94DD", "CJK UNIFIED IDEOGRAPH-94DD")],
        unicode_source,
    )

    record = repository.find_by_glyph("铝")

    assert record is not None
    assert record["unicode"]["name"] == "CJK UNIFIED IDEOGRAPH-94DD"


def test_repository_namespace_replacement_rolls_back_on_insert_failure(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    old_source = SourceSnapshot("Old Pack", "file://old", "1", "sha-old", "private", "old.csv")
    old_source_id = repository.add_source_snapshot(old_source)
    old_entry = DomainEntry(
        term="FOB",
        canonical_id="trade:fob",
        entry_type="trade_term",
        language="en",
        aliases=[],
        definition=None,
        traits={},
        namespace="private_trade",
    )
    repository.insert_lexical_entries([old_entry], old_source_id)
    invalid_entry = DomainEntry(
        term="CIF",
        canonical_id="trade:cif",
        entry_type="trade_term",
        language="en",
        aliases=[],
        definition=None,
        traits={"bad": object()},
        namespace="private_trade",
    )

    with pytest.raises(TypeError):
        repository.replace_lexical_namespace(
            "private_trade",
            [invalid_entry],
            SourceSnapshot("New Pack", "file://new", "2", "sha-new", "private", "new.csv"),
        )

    assert repository.find_term("FOB") is not None
    with repository.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM source_snapshot").fetchone()[0] == 1
