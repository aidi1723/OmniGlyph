from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class UnihanProperty:
    glyph: str
    unicode_hex: str
    property_name: str
    property_value: str
    property_namespace: str = "unihan"
    source_name: str = "Unihan Database"
    source_file: str = "Unihan.txt"


def parse_unihan_data(path: Path) -> Iterator[UnihanProperty]:
    with path.open("r", encoding="utf-8") as source:
        for line in source:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            fields = stripped.split("\t", 2)
            if len(fields) != 3:
                continue

            codepoint, property_name, property_value = fields
            if not codepoint.startswith("U+") or not property_name or not property_value:
                continue

            try:
                glyph = chr(int(codepoint[2:], 16))
            except ValueError:
                continue

            yield UnihanProperty(
                glyph=glyph,
                unicode_hex=f"U+{codepoint[2:].upper().zfill(4)}",
                property_name=property_name,
                property_value=property_value,
            )
