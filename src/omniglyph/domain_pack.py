import csv
import json
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Iterator


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
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            term = (row.get("term") or "").strip()
            canonical_id = (row.get("canonical_id") or "").strip()
            entry_type = (row.get("entry_type") or "").strip()
            language = (row.get("language") or "").strip() or "und"
            if not term or not canonical_id or not entry_type:
                continue
            aliases = [item.strip() for item in (row.get("aliases") or "").split(";") if item.strip()]
            definition = (row.get("definition") or "").strip() or None
            traits_raw = (row.get("traits") or "{}").strip() or "{}"
            try:
                traits = json.loads(traits_raw)
            except json.JSONDecodeError:
                traits = {}
            if not isinstance(traits, dict):
                traits = {}
            sensitivity = (row.get("sensitivity") or "normal").strip() or "normal"
            review_status = (row.get("review_status") or "approved").strip() or "approved"
            pack_id = (row.get("pack_id") or "").strip() or None
            pack_version = (row.get("pack_version") or "").strip() or None
            yield DomainEntry(
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
            )


def bundled_domain_pack(name: str):
    if name != "software_development":
        raise ValueError(f"unknown bundled domain pack: {name}")
    return files("omniglyph.domain_packs").joinpath("software_development.csv")
