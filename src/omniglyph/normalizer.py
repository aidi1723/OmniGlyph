from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class GlyphRecord:
    glyph: str
    unicode_hex: str
    basic_definition: str | None
    etymology_tree: dict | None = None
    semantic_vector: list[float] | None = None
    computable_traits: dict | None = None
    source_name: str = "Unicode Character Database"
    source_file: str = "UnicodeData.txt"
    source_field: str = "Name"
    source_value: str | None = None


def parse_unicode_data(path: Path) -> Iterator[GlyphRecord]:
    with path.open("r", encoding="utf-8") as source:
        for line in source:
            fields = line.rstrip("\n").split(";")
            if len(fields) < 2:
                continue

            codepoint_hex, character_name = fields[0], fields[1]
            try:
                codepoint = int(codepoint_hex, 16)
            except ValueError:
                continue
            if 0xD800 <= codepoint <= 0xDFFF:
                continue
            glyph = chr(codepoint)

            yield GlyphRecord(
                glyph=glyph,
                unicode_hex=f"U+{codepoint_hex.upper().zfill(4)}",
                basic_definition=character_name or None,
                source_value=character_name or None,
            )
