import json
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


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
    pending: tuple[int, str, list[str], str] | None = None
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            fields = line.rstrip("\n").split(";")
            if len(fields) < 2:
                continue

            codepoint_hex, character_name = fields[0], fields[1]
            try:
                codepoint = int(codepoint_hex, 16)
            except ValueError:
                continue
            if not 0 <= codepoint <= 0x10FFFF:
                raise ValueError(f"Unicode code point out of range at line {line_number}: {codepoint_hex}")

            range_match = re.fullmatch(r"<(.+), (First|Last)>", character_name)
            if range_match is not None:
                label, marker = range_match.groups()
                if marker == "First":
                    if pending is not None:
                        raise ValueError(f"Unicode range missing Last row before line {line_number}")
                    pending = (codepoint, label, fields, line.rstrip("\n"))
                    continue
                if pending is None:
                    raise ValueError(f"Unicode range has Last without First at line {line_number}")
                start, pending_label, first_fields, first_line = pending
                if label != pending_label or codepoint < start or fields[2:] != first_fields[2:]:
                    raise ValueError(f"Unicode range First/Last mismatch at line {line_number}")
                pending = None
                provenance = json.dumps(
                    {"first": first_line, "last": line.rstrip("\n"), "label": label},
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                for value in range(start, codepoint + 1):
                    if 0xD800 <= value <= 0xDFFF:
                        continue
                    yield GlyphRecord(
                        glyph=chr(value),
                        unicode_hex=f"U+{value:04X}",
                        basic_definition=None,
                        source_file=path.name,
                        source_field="Range",
                        source_value=provenance,
                    )
                continue

            if pending is not None:
                raise ValueError(f"Unicode range missing Last row before line {line_number}")
            if 0xD800 <= codepoint <= 0xDFFF:
                continue
            yield GlyphRecord(
                glyph=chr(codepoint),
                unicode_hex=f"U+{codepoint:04X}",
                basic_definition=character_name or None,
                source_file=path.name,
                source_field="Name",
                source_value=character_name or None,
            )
    if pending is not None:
        raise ValueError("Unicode range is missing a Last row")
