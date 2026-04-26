import json
import subprocess
import sys
from pathlib import Path

from omniglyph.domain_pack import parse_domain_pack
from omniglyph.lexicon_pack import init_lexicon_pack, load_lexicon_pack, validate_lexicon_pack
from omniglyph.repository import GlyphRepository, SourceSnapshot


def write_pack(path: Path) -> None:
    path.mkdir()
    (path / "pack.json").write_text(
        json.dumps(
            {
                "schema": "omniglyph.lexicon_pack:0.1",
                "pack_id": "company.acme.trade_terms",
                "namespace": "private_acme",
                "name": "ACME Trade Terms",
                "version": "2026.04.26",
                "owner_type": "enterprise",
                "license": "private",
                "visibility": "private",
                "description": "Company-specific terms.",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (path / "terms.csv").write_text(
        "\n".join(
            [
                "term,canonical_id,entry_type,language,aliases,definition,traits,sensitivity,review_status",
                'FOB,trade:fob,trade_term,en,Free On Board;离岸价,Free On Board,"{""incoterm"":true}",normal,approved',
                '底价,company:floor_price,confidential_term,zh,floor price;minimum price,Internal minimum selling price,"{""dlp"":true}",secret,approved',
            ]
        ),
        encoding="utf-8",
    )


def test_validate_lexicon_pack_accepts_pack_directory(tmp_path):
    pack_dir = tmp_path / "acme-pack"
    write_pack(pack_dir)

    report = validate_lexicon_pack(pack_dir)

    assert report["status"] == "pass"
    assert report["pack"]["pack_id"] == "company.acme.trade_terms"
    assert report["pack"]["namespace"] == "private_acme"
    assert report["summary"] == {"entry_count": 2, "alias_count": 4, "secret_count": 1}
    assert report["errors"] == []


def test_validate_lexicon_pack_reports_invalid_traits_and_status(tmp_path):
    pack_dir = tmp_path / "bad-pack"
    pack_dir.mkdir()
    (pack_dir / "pack.json").write_text('{"schema":"omniglyph.lexicon_pack:0.1","pack_id":"bad","namespace":"private_bad","name":"Bad","version":"1","owner_type":"personal","license":"private","visibility":"private"}', encoding="utf-8")
    (pack_dir / "terms.csv").write_text(
        "term,canonical_id,entry_type,language,aliases,definition,traits,sensitivity,review_status\n"
        "Bad,bad:id,term,en,,,not-json,secret,pending\n",
        encoding="utf-8",
    )

    report = validate_lexicon_pack(pack_dir)

    assert report["status"] == "fail"
    assert "terms.csv row 2: traits must be a JSON object" in report["errors"]
    assert "terms.csv row 2: review_status must be one of approved, deprecated, draft" in report["errors"]


def test_load_lexicon_pack_applies_pack_metadata_to_entries(tmp_path):
    pack_dir = tmp_path / "acme-pack"
    write_pack(pack_dir)

    pack = load_lexicon_pack(pack_dir)

    assert pack.metadata["pack_id"] == "company.acme.trade_terms"
    assert pack.entries[1].term == "底价"
    assert pack.entries[1].namespace == "private_acme"
    assert pack.entries[1].sensitivity == "secret"
    assert pack.entries[1].review_status == "approved"
    assert pack.entries[1].pack_id == "company.acme.trade_terms"
    assert pack.entries[1].pack_version == "2026.04.26"


def test_init_lexicon_pack_creates_template_files(tmp_path):
    target = tmp_path / "starter"

    init_lexicon_pack(target, namespace="private_starter", pack_id="personal.starter", name="Personal Starter")

    assert (target / "pack.json").exists()
    assert (target / "terms.csv").exists()
    report = validate_lexicon_pack(target)
    assert report["status"] == "pass"
    assert report["pack"]["namespace"] == "private_starter"


def test_parse_domain_pack_reads_standard_metadata_columns(tmp_path):
    source = tmp_path / "terms.csv"
    source.write_text(
        "term,canonical_id,entry_type,language,aliases,definition,traits,sensitivity,review_status,pack_id,pack_version\n"
        '底价,company:floor_price,confidential_term,zh,floor price,Internal floor price,"{""dlp"":true}",secret,approved,company.acme,2026.04\n',
        encoding="utf-8",
    )

    entry = list(parse_domain_pack(source, namespace="private_acme"))[0]

    assert entry.sensitivity == "secret"
    assert entry.review_status == "approved"
    assert entry.pack_id == "company.acme"
    assert entry.pack_version == "2026.04"


def test_repository_returns_lexicon_pack_metadata_and_guardrail_can_filter_unapproved(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    source = tmp_path / "terms.csv"
    source.write_text(
        "term,canonical_id,entry_type,language,aliases,definition,traits,sensitivity,review_status,pack_id,pack_version\n"
        'Draft Spec,company:draft_spec,product_spec,en,,Draft only,"{}",normal,draft,company.acme,2026.04\n',
        encoding="utf-8",
    )
    source_id = repository.add_source_snapshot(SourceSnapshot("Private Domain Pack", "file://terms.csv", "fixture", "sha-pack", "private", "terms.csv"))
    repository.insert_lexical_entries(list(parse_domain_pack(source, namespace="private_acme")), source_id)

    entry = repository.find_term("Draft Spec")

    assert entry["review_status"] == "draft"
    assert entry["sensitivity"] == "normal"
    assert entry["pack_id"] == "company.acme"
    assert entry["pack_version"] == "2026.04"


def test_cli_init_and_validate_lexicon_pack(tmp_path):
    target = tmp_path / "cli-pack"

    init_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "omniglyph.cli",
            "init-lexicon-pack",
            str(target),
            "--namespace",
            "private_cli",
            "--pack-id",
            "personal.cli",
            "--name",
            "CLI Pack",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    validate_result = subprocess.run(
        [sys.executable, "-m", "omniglyph.cli", "validate-domain-pack", str(target)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert init_result.returncode == 0
    assert "Created lexicon pack" in init_result.stdout
    assert validate_result.returncode == 0
    assert '"status": "pass"' in validate_result.stdout
