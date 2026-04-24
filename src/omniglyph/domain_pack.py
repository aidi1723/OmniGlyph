import csv
import json
from dataclasses import dataclass
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
            yield DomainEntry(
                term=term,
                canonical_id=canonical_id,
                entry_type=entry_type,
                language=language,
                aliases=aliases,
                definition=definition,
                traits=traits,
                namespace=namespace,
            )
