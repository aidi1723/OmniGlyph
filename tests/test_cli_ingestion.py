import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from omniglyph import cli
from omniglyph.config import Settings
from omniglyph.domain_pack import DomainEntry
from omniglyph.lexicon_pack import init_lexicon_pack, load_lexicon_pack, validate_lexicon_pack
from omniglyph.repository import GlyphRepository, SourceSnapshot

HEADER = "term,canonical_id,entry_type,aliases,traits\n"
SOURCE = SourceSnapshot("Old", "file://old", "1", "old", "private", "old.csv")


def database_contents(repository):
    return {
        table: [tuple(row) for row in repository.connect().execute(f"SELECT * FROM {table} ORDER BY id")]
        for table in ("lexical_entry", "lexical_alias", "source_snapshot")
    }


@pytest.fixture
def populated(tmp_path, monkeypatch):
    database = tmp_path / "data.sqlite3"
    monkeypatch.setattr(cli, "settings", Settings(sqlite_path=database))
    repository = GlyphRepository(database)
    repository.initialize()
    entry = DomainEntry("FOB", "trade:fob", "term", "und", ["Free On Board"], None, {}, "private_trade")
    repository.insert_lexical_entries([entry], repository.add_source_snapshot(SOURCE))
    yield repository, entry
    repository.close()


@pytest.mark.parametrize("content", [
    HEADER,
    HEADER + "missing,,term,,{}\n",
    HEADER + "FOB,trade:fob,term,,[]\n",
    HEADER + "FOB,trade:fob,term,,not-json\n",
    HEADER + "FOB,trade:fob,term,,{},extra\n",
    "term,canonical_id,entry_type,canonical_id\nFOB,trade:fob,term,other\n",
])
def test_invalid_replacement_preserves_all_tables(tmp_path, populated, content):
    repository, _ = populated
    before = database_contents(repository)
    source = tmp_path / "bad.csv"
    source.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        cli.ingest_domain_pack(source, "private_trade", replace_namespace=True)
    assert database_contents(repository) == before


@pytest.mark.parametrize("metadata", [[], None, "text", 7])
def test_nonobject_metadata_is_structured_failure(tmp_path, metadata):
    pack = tmp_path / "pack"
    init_lexicon_pack(pack, "private_trade", "trade", "Trade")
    (pack / "pack.json").write_text(json.dumps(metadata), encoding="utf-8")
    assert validate_lexicon_pack(pack)["status"] == "fail"
    with pytest.raises(ValueError, match="object"):
        load_lexicon_pack(pack)


def test_replacement_rejects_mixed_namespace_and_empty(populated):
    repository, entry = populated
    before = database_contents(repository)
    for entries in ([], [replace(entry, namespace="private_other")]):
        with pytest.raises(ValueError):
            repository.replace_lexical_namespace("private_trade", iter(entries), SOURCE)
        assert database_contents(repository) == before


def test_replacement_rolls_back_aliases_and_source_on_midwrite_failure(populated):
    repository, entry = populated
    before = database_contents(repository)
    with pytest.raises(TypeError):
        repository.replace_lexical_namespace(
            "private_trade", [replace(entry, term="CIF"), replace(entry, traits={"bad": object()})],
            replace(SOURCE, sha256="new", source_version="2"),
        )
    assert database_contents(repository) == before


def test_pack_namespace_override_is_rejected(tmp_path, populated):
    repository, _ = populated
    before = database_contents(repository)
    pack = tmp_path / "pack"
    init_lexicon_pack(pack, "private_other", "other", "Other")
    with pytest.raises(ValueError, match="namespace"):
        cli.ingest_domain_pack(pack, "private_trade", replace_namespace=True)
    assert database_contents(repository) == before


def test_import_reads_snapshot_once_and_hashes_the_imported_bytes(tmp_path, populated, monkeypatch):
    repository, _ = populated
    source = tmp_path / "snapshot.csv"
    content = (HEADER + "CIF,trade:cif,term,cost insurance freight,{}\n").encode()
    source.write_bytes(content)
    read_bytes = Path.read_bytes
    calls = []

    def read_once(path):
        if path == source:
            calls.append(path)
            assert len(calls) == 1, "input must not be reopened"
        return read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", read_once)
    assert cli.ingest_domain_pack(source, "private_trade", expected_sha256=hashlib.sha256(content).hexdigest()) == 1
    assert calls == [source]
    row = repository.connect().execute("SELECT sha256 FROM source_snapshot WHERE source_name='Private Domain Pack'").fetchone()
    assert row[0] == hashlib.sha256(content).hexdigest()


def test_dry_run_also_checks_expected_hash(tmp_path, populated):
    source = tmp_path / "valid.csv"
    source.write_text(HEADER + "CIF,trade:cif,term,,{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256"):
        cli.ingest_domain_pack(source, "private_trade", dry_run=True, expected_sha256="wrong")
