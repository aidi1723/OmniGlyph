import argparse
from pathlib import Path

from omniglyph.config import settings
from omniglyph.domain_pack import parse_domain_pack
from omniglyph.normalizer import parse_unicode_data
from omniglyph.unihan import parse_unihan_data
from omniglyph.repository import GlyphRepository, SourceSnapshot
from omniglyph.sources import download_source, register_local_source

UNICODE_LICENSE = "Unicode Terms of Use"
UNIHAN_LICENSE = "Unicode Terms of Use"


def download_unicode() -> Path:
    artifact = download_source(
        settings.unicode_data_url,
        settings.raw_dir / "UnicodeData.txt",
        source_version="latest",
        license=UNICODE_LICENSE,
    )
    print(f"Downloaded {artifact.path} sha256={artifact.sha256}")
    return artifact.path


def ingest_unicode(source_path: Path, source_version: str = "local") -> int:
    artifact = register_local_source(
        source_path,
        source_url=source_path.as_uri() if source_path.is_absolute() else f"file://{source_path}",
        source_version=source_version,
        license=UNICODE_LICENSE,
    )
    records = list(parse_unicode_data(source_path))
    repository = GlyphRepository(settings.sqlite_path)
    repository.initialize()
    source_id = repository.add_source_snapshot(
        SourceSnapshot(
            source_name="Unicode Character Database",
            source_url=artifact.source_url,
            source_version=artifact.source_version,
            sha256=artifact.sha256,
            license=artifact.license,
            local_path=str(artifact.path),
        )
    )
    repository.insert_glyph_records(records, source_id=source_id)
    return len(records)


def ingest_unihan(source_path: Path, source_version: str = "local") -> int:
    artifact = register_local_source(
        source_path,
        source_url=source_path.as_uri() if source_path.is_absolute() else f"file://{source_path}",
        source_version=source_version,
        license=UNIHAN_LICENSE,
    )
    properties = list(parse_unihan_data(source_path))
    repository = GlyphRepository(settings.sqlite_path)
    repository.initialize()
    source_id = repository.add_source_snapshot(
        SourceSnapshot(
            source_name="Unihan Database",
            source_url=artifact.source_url,
            source_version=artifact.source_version,
            sha256=artifact.sha256,
            license=artifact.license,
            local_path=str(artifact.path),
        )
    )
    return repository.insert_unihan_properties(properties, source_id=source_id)


def ingest_domain_pack(source_path: Path, namespace: str, source_version: str = "local") -> int:
    artifact = register_local_source(
        source_path,
        source_url=source_path.as_uri() if source_path.is_absolute() else f"file://{source_path}",
        source_version=source_version,
        license="private",
    )
    entries = list(parse_domain_pack(source_path, namespace=namespace))
    repository = GlyphRepository(settings.sqlite_path)
    repository.initialize()
    source_id = repository.add_source_snapshot(
        SourceSnapshot(
            source_name="Private Domain Pack",
            source_url=artifact.source_url,
            source_version=artifact.source_version,
            sha256=artifact.sha256,
            license=artifact.license,
            local_path=str(artifact.path),
        )
    )
    return repository.insert_lexical_entries(entries, source_id=source_id)


def main() -> None:
    parser = argparse.ArgumentParser(prog="omniglyph")
    subcommands = parser.add_subparsers(dest="command", required=True)

    subcommands.add_parser("download-unicode")

    ingest = subcommands.add_parser("ingest-unicode")
    ingest.add_argument("--source", type=Path, required=True)
    ingest.add_argument("--source-version", default="local")

    ingest_unihan_parser = subcommands.add_parser("ingest-unihan")
    ingest_unihan_parser.add_argument("--source", type=Path, required=True)
    ingest_unihan_parser.add_argument("--source-version", default="local")

    domain = subcommands.add_parser("ingest-domain-pack")
    domain.add_argument("--source", type=Path, required=True)
    domain.add_argument("--namespace", required=True)
    domain.add_argument("--source-version", default="local")

    lookup = subcommands.add_parser("lookup")
    lookup.add_argument("text")

    args = parser.parse_args()
    if args.command == "download-unicode":
        download_unicode()
    elif args.command == "ingest-unicode":
        count = ingest_unicode(args.source, args.source_version)
        print(f"Ingested {count} glyph records")
    elif args.command == "ingest-unihan":
        count = ingest_unihan(args.source, args.source_version)
        print(f"Ingested {count} Unihan properties")
    elif args.command == "ingest-domain-pack":
        count = ingest_domain_pack(args.source, args.namespace, args.source_version)
        print(f"Ingested {count} domain entries")
    elif args.command == "lookup":
        repository = GlyphRepository(settings.sqlite_path)
        repository.initialize()
        if len(args.text) == 1:
            print(repository.find_by_glyph(args.text))
        else:
            print(repository.find_term(args.text))


if __name__ == "__main__":
    main()
