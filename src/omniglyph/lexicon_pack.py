import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from omniglyph.domain_pack import DomainEntry, parse_domain_pack

PACK_SCHEMA = "omniglyph.lexicon_pack:0.1"
TERMS_FILENAME = "terms.csv"
PACK_FILENAME = "pack.json"
ALLOWED_SENSITIVITY = {"normal", "internal", "secret"}
ALLOWED_REVIEW_STATUS = {"draft", "approved", "deprecated"}
REQUIRED_PACK_FIELDS = {
    "schema",
    "pack_id",
    "namespace",
    "name",
    "version",
    "owner_type",
    "license",
    "visibility",
}
REQUIRED_TERM_FIELDS = {"term", "canonical_id", "entry_type"}


@dataclass(frozen=True)
class LexiconPack:
    metadata: dict[str, Any]
    entries: list[DomainEntry]


def init_lexicon_pack(path: Path | str, namespace: str, pack_id: str, name: str) -> None:
    pack_dir = Path(path)
    pack_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "schema": PACK_SCHEMA,
        "pack_id": pack_id,
        "namespace": namespace,
        "name": name,
        "version": "0.1.0",
        "owner_type": "personal",
        "license": "private",
        "visibility": "private",
        "description": "Starter OmniGlyph lexicon pack.",
    }
    (pack_dir / PACK_FILENAME).write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (pack_dir / TERMS_FILENAME).write_text(
        "\n".join(
            [
                "term,canonical_id,entry_type,language,aliases,definition,traits,sensitivity,review_status",
                'example term,example:term,custom,en,example alias,Replace this row,"{}",normal,approved',
                "",
            ]
        ),
        encoding="utf-8",
    )


def load_lexicon_pack(path: Path | str) -> LexiconPack:
    pack_dir = Path(path)
    metadata = _read_metadata(pack_dir)
    namespace = metadata["namespace"]
    entries = [
        _with_pack_metadata(entry, metadata)
        for entry in parse_domain_pack(pack_dir / TERMS_FILENAME, namespace=namespace)
    ]
    return LexiconPack(metadata=metadata, entries=entries)


def validate_lexicon_pack(path: Path | str) -> dict:
    pack_dir = Path(path)
    errors = []
    metadata = {}
    if not pack_dir.exists():
        errors.append(f"pack directory not found: {pack_dir}")
    elif not pack_dir.is_dir():
        errors.append(f"pack path must be a directory: {pack_dir}")
    if not errors:
        metadata, metadata_errors = _validate_metadata(pack_dir)
        errors.extend(metadata_errors)
        errors.extend(_validate_terms(pack_dir))
    entries = []
    if not errors:
        entries = load_lexicon_pack(pack_dir).entries
    alias_count = sum(len(entry.aliases) for entry in entries)
    secret_count = sum(1 for entry in entries if entry.sensitivity == "secret")
    return {
        "schema": PACK_SCHEMA,
        "status": "pass" if not errors else "fail",
        "pack": {
            "pack_id": metadata.get("pack_id"),
            "namespace": metadata.get("namespace"),
            "name": metadata.get("name"),
            "version": metadata.get("version"),
        },
        "summary": {
            "entry_count": len(entries),
            "alias_count": alias_count,
            "secret_count": secret_count,
        },
        "errors": errors,
        "warnings": [],
    }


def source_paths(path: Path | str) -> tuple[Path, Path | None]:
    source = Path(path)
    if source.is_dir():
        return source / TERMS_FILENAME, source / PACK_FILENAME
    return source, None


def entries_from_source(path: Path | str, namespace: str | None = None) -> tuple[list[DomainEntry], dict | None]:
    source = Path(path)
    if source.is_dir():
        pack = load_lexicon_pack(source)
        return pack.entries, pack.metadata
    if namespace is None:
        raise ValueError("namespace is required when importing a CSV file")
    return list(parse_domain_pack(source, namespace=namespace)), None


def _read_metadata(pack_dir: Path) -> dict:
    metadata_path = pack_dir / PACK_FILENAME
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def _validate_metadata(pack_dir: Path) -> tuple[dict, list[str]]:
    metadata_path = pack_dir / PACK_FILENAME
    if not metadata_path.exists():
        return {}, [f"{PACK_FILENAME} is required"]
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"{PACK_FILENAME}: invalid JSON at line {exc.lineno} column {exc.colno}"]
    errors = []
    missing = sorted(field for field in REQUIRED_PACK_FIELDS if not metadata.get(field))
    for field in missing:
        errors.append(f"{PACK_FILENAME}: missing required field {field}")
    if metadata.get("schema") != PACK_SCHEMA:
        errors.append(f"{PACK_FILENAME}: schema must be {PACK_SCHEMA}")
    if metadata.get("namespace") and not str(metadata["namespace"]).startswith("private_"):
        errors.append(f"{PACK_FILENAME}: namespace should start with private_ for user lexicon packs")
    return metadata, errors


def _validate_terms(pack_dir: Path) -> list[str]:
    terms_path = pack_dir / TERMS_FILENAME
    if not terms_path.exists():
        return [f"{TERMS_FILENAME} is required"]
    errors = []
    with terms_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return [f"{TERMS_FILENAME}: missing header row"]
        missing = sorted(field for field in REQUIRED_TERM_FIELDS if field not in reader.fieldnames)
        for field in missing:
            errors.append(f"{TERMS_FILENAME}: missing required column {field}")
        for row_number, row in enumerate(reader, 2):
            if not any((value or "").strip() for value in row.values()):
                continue
            for field in REQUIRED_TERM_FIELDS:
                if not (row.get(field) or "").strip():
                    errors.append(f"{TERMS_FILENAME} row {row_number}: missing required field {field}")
            traits_raw = (row.get("traits") or "{}").strip() or "{}"
            try:
                traits = json.loads(traits_raw)
            except json.JSONDecodeError:
                errors.append(f"{TERMS_FILENAME} row {row_number}: traits must be a JSON object")
                traits = {}
            if not isinstance(traits, dict):
                errors.append(f"{TERMS_FILENAME} row {row_number}: traits must be a JSON object")
            sensitivity = (row.get("sensitivity") or "normal").strip() or "normal"
            if sensitivity not in ALLOWED_SENSITIVITY:
                errors.append(f"{TERMS_FILENAME} row {row_number}: sensitivity must be one of internal, normal, secret")
            review_status = (row.get("review_status") or "approved").strip() or "approved"
            if review_status not in ALLOWED_REVIEW_STATUS:
                errors.append(f"{TERMS_FILENAME} row {row_number}: review_status must be one of approved, deprecated, draft")
    return errors


def _with_pack_metadata(entry: DomainEntry, metadata: dict) -> DomainEntry:
    return DomainEntry(
        term=entry.term,
        canonical_id=entry.canonical_id,
        entry_type=entry.entry_type,
        language=entry.language,
        aliases=entry.aliases,
        definition=entry.definition,
        traits=entry.traits,
        namespace=metadata["namespace"],
        sensitivity=entry.sensitivity,
        review_status=entry.review_status,
        pack_id=metadata["pack_id"],
        pack_version=metadata["version"],
    )
