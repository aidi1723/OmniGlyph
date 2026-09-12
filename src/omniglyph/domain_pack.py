import csv
import io
import json
from collections.abc import Iterator
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

REQUIRED_TERM_FIELDS = {"term", "canonical_id", "entry_type"}
ALLOWED_SENSITIVITY = {"normal", "internal", "secret"}
ALLOWED_REVIEW_STATUS = {"draft", "approved", "deprecated"}


@dataclass(frozen=True)
class DomainEntry:
    term: str
    canonical_id: str
    entry_type: str
    language: str
    aliases: list[str]
    definition: str | None
    traits: dict
    namespace: str
    sensitivity: str = "normal"
    review_status: str = "approved"
    pack_id: str | None = None
    pack_version: str | None = None


def parse_domain_pack(path: Path, namespace: str) -> Iterator[DomainEntry]:
    entries, errors = inspect_domain_pack(path.read_bytes(), namespace, path.name)
    if errors:
        raise ValueError("invalid domain pack: " + "; ".join(errors))
    yield from entries


def inspect_domain_pack(content: bytes, namespace: str, filename: str = "terms.csv") -> tuple[list[DomainEntry], list[str]]:
    errors: list[str] = []
    entries: list[DomainEntry] = []
    if not isinstance(namespace, str) or not namespace.strip():
        return [], ["namespace must be a non-empty string"]
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return [], [f"{filename}: must be UTF-8"]
    reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
    try:
        headers = reader.fieldnames
        if not headers:
            return [], [f"{filename}: missing header row"]
        duplicates = sorted({field for field in headers if headers.count(field) > 1})
        if duplicates:
            return [], [f"{filename}: duplicate column {field}" for field in duplicates]
        missing = sorted(REQUIRED_TERM_FIELDS - set(headers))
        if missing:
            return [], [f"{filename}: missing required column {field}" for field in missing]
        for row_number, row in enumerate(reader, 2):
            prefix = f"{filename} row {row_number}"
            if None in row:
                errors.append(f"{prefix}: unexpected extra column values")
                continue
            if not any((value or "").strip() for value in row.values()):
                continue
            row_errors = []
            for field in sorted(REQUIRED_TERM_FIELDS):
                if not (row.get(field) or "").strip():
                    row_errors.append(f"{prefix}: missing required field {field}")
            term = (row.get("term") or "").strip()
            canonical_id = (row.get("canonical_id") or "").strip()
            entry_type = (row.get("entry_type") or "").strip()
            language = (row.get("language") or "").strip() or "und"
            aliases = [item.strip() for item in (row.get("aliases") or "").split(";") if item.strip()]
            definition = (row.get("definition") or "").strip() or None
            traits_raw = (row.get("traits") or "{}").strip() or "{}"
            try:
                traits = json.loads(traits_raw)
            except json.JSONDecodeError:
                traits = None
            if not isinstance(traits, dict):
                row_errors.append(f"{prefix}: traits must be a JSON object")
                traits = {}
            sensitivity = (row.get("sensitivity") or "normal").strip() or "normal"
            review_status = (row.get("review_status") or "approved").strip() or "approved"
            if sensitivity not in ALLOWED_SENSITIVITY:
                row_errors.append(f"{prefix}: sensitivity must be one of internal, normal, secret")
            if review_status not in ALLOWED_REVIEW_STATUS:
                row_errors.append(f"{prefix}: review_status must be one of approved, deprecated, draft")
            errors.extend(row_errors)
            if row_errors:
                continue
            pack_id = (row.get("pack_id") or "").strip() or None
            pack_version = (row.get("pack_version") or "").strip() or None
            entries.append(DomainEntry(
                term=term,
                canonical_id=canonical_id,
                entry_type=entry_type,
                language=language,
                aliases=aliases,
                definition=definition,
                traits=traits,
                namespace=namespace,
                sensitivity=sensitivity,
                review_status=review_status,
                pack_id=pack_id,
                pack_version=pack_version,
            ))
    except csv.Error as exc:
        errors.append(f"{filename}: invalid CSV: {exc}")
    return ([] if errors else entries), errors


def bundled_domain_pack(name: str):
    if name != "software_development":
        raise ValueError(f"unknown bundled domain pack: {name}")
    return files("omniglyph.domain_packs").joinpath("software_development.csv")
