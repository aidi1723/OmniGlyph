import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from omniglyph.domain_pack import DomainEntry, inspect_domain_pack
from omniglyph.pack_paths import ensure_pack_path

PACK_SCHEMA = "omniglyph.lexicon_pack:0.1"
TERMS_FILENAME = "terms.csv"
PACK_FILENAME = "pack.json"
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


@dataclass(frozen=True)
class LexiconPack:
    metadata: dict[str, Any]
    entries: list[DomainEntry]


@dataclass(frozen=True)
class PreparedLexiconSource:
    entries: list[DomainEntry]
    metadata: dict[str, Any] | None
    namespace: str
    terms_path: Path
    sha256: str
    metadata_sha256: str | None
    errors: list[str]

    def require_valid(self, *, require_entries: bool = False) -> None:
        if self.errors:
            raise ValueError("invalid lexicon source: " + "; ".join(self.errors))
        if require_entries and not self.entries:
            raise ValueError("replacement entries must not be empty")


def prepare_lexicon_source(path: Path | str, namespace: str | None = None) -> PreparedLexiconSource:
    terms_path, metadata_path = source_paths(path)
    errors: list[str] = []
    metadata = None
    metadata_sha256 = None
    if metadata_path is not None:
        metadata, metadata_errors, metadata_sha256 = _validate_metadata(metadata_path)
        errors.extend(metadata_errors)
        pack_namespace = metadata.get("namespace")
        if namespace is not None and namespace != pack_namespace:
            errors.append("replacement namespace must match pack namespace")
        namespace = pack_namespace if isinstance(pack_namespace, str) else None
    if not namespace:
        errors.append("namespace is required when importing a CSV file")
    content = b""
    try:
        content = terms_path.read_bytes()
        entries, term_errors = inspect_domain_pack(content, namespace or "", terms_path.name)
        errors.extend(term_errors)
    except OSError as exc:
        entries = []
        errors.append(f"{terms_path.name}: cannot read source: {exc.strerror}")
    if not errors and metadata is not None:
        entries = [_with_pack_metadata(entry, metadata) for entry in entries]
    return PreparedLexiconSource(
        [] if errors else entries, metadata, namespace or "", terms_path,
        hashlib.sha256(content).hexdigest(), metadata_sha256, errors,
    )


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
    if not Path(path).is_dir():
        raise ValueError("pack path must be a directory")
    prepared = prepare_lexicon_source(path)
    prepared.require_valid()
    assert prepared.metadata is not None
    return LexiconPack(metadata=prepared.metadata, entries=prepared.entries)


def validate_lexicon_pack(path: Path | str) -> dict:
    pack_dir = Path(path)
    errors = []
    metadata: dict[str, Any] = {}
    if not pack_dir.exists():
        errors.append(f"pack directory not found: {pack_dir}")
    elif not pack_dir.is_dir():
        errors.append(f"pack path must be a directory: {pack_dir}")
    entries = []
    if not errors:
        prepared = prepare_lexicon_source(pack_dir)
        errors = prepared.errors
        metadata = prepared.metadata or {}
        entries = prepared.entries
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


def ensure_allowed_pack_path(path: str, root: Path | None) -> None:
    try:
        ensure_pack_path(path, root, (PACK_FILENAME, TERMS_FILENAME))
    except ValueError as exc:
        raise ValueError(str(exc).replace("configured pack root", "OMNIGLYPH_LEXICON_PACK_ROOT")) from exc


def source_paths(path: Path | str) -> tuple[Path, Path | None]:
    source = Path(path)
    if source.is_dir():
        return source / TERMS_FILENAME, source / PACK_FILENAME
    return source, None


def entries_from_source(path: Path | str, namespace: str | None = None) -> tuple[list[DomainEntry], dict | None]:
    prepared = prepare_lexicon_source(path, namespace)
    prepared.require_valid()
    return prepared.entries, prepared.metadata


def _validate_metadata(metadata_path: Path) -> tuple[dict, list[str], str | None]:
    digest = None
    try:
        content = metadata_path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        metadata = json.loads(content.decode("utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        return {}, [f"{PACK_FILENAME}: cannot read UTF-8 metadata: {exc}"], digest
    except json.JSONDecodeError as exc:
        return {}, [f"{PACK_FILENAME}: invalid JSON at line {exc.lineno} column {exc.colno}"], digest
    if not isinstance(metadata, dict):
        return {}, [f"{PACK_FILENAME}: metadata must be a JSON object"], digest
    errors = []
    missing = sorted(field for field in REQUIRED_PACK_FIELDS if not isinstance(metadata.get(field), str) or not metadata[field].strip())
    for field in missing:
        errors.append(f"{PACK_FILENAME}: missing required field {field}")
    if metadata.get("schema") != PACK_SCHEMA:
        errors.append(f"{PACK_FILENAME}: schema must be {PACK_SCHEMA}")
    if metadata.get("namespace") and not str(metadata["namespace"]).startswith("private_"):
        errors.append(f"{PACK_FILENAME}: namespace should start with private_ for user lexicon packs")
    return metadata, errors, digest


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
