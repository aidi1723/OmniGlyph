from pathlib import Path

import pytest

from omniglyph.normalizer import parse_unicode_data

FIXTURE = Path(__file__).parent / "fixtures" / "UnicodeData.sample.txt"


def test_parse_unicode_data_maps_codepoint_and_glyph():
    records = list(parse_unicode_data(FIXTURE))

    assert records[0].glyph == "A"
    assert records[0].unicode_hex == "U+0041"
    assert records[0].basic_definition == "LATIN CAPITAL LETTER A"


def test_parse_unicode_data_supports_cjk_without_guessing_definition():
    records = list(parse_unicode_data(FIXTURE))

    assert records[3].glyph == "铝"
    assert records[3].unicode_hex == "U+94DD"
    assert records[3].basic_definition == "CJK UNIFIED IDEOGRAPH-94DD"
    assert records[3].etymology_tree is None
    assert records[3].semantic_vector is None
    assert records[3].computable_traits is None


def test_parse_unicode_data_rejects_malformed_rows(tmp_path):
    malformed = tmp_path / "UnicodeData.malformed.txt"
    malformed.write_text("0041;LATIN CAPITAL LETTER A\nnot-hex;BROKEN\n", encoding="utf-8")

    with pytest.raises(ValueError, match="not hexadecimal"):
        list(parse_unicode_data(malformed))


def test_parse_unicode_data_covers_combining_marks_variation_selectors_and_emoji():
    records = list(parse_unicode_data(FIXTURE))

    assert records[1].glyph == "\u0301"
    assert records[2].unicode_hex == "U+FE0F"
    assert records[4].glyph == "😀"


def test_parse_unicode_data_skips_surrogate_codepoints(tmp_path):
    source = tmp_path / "UnicodeData.surrogate.txt"
    source.write_text("D800;<Non Private Use High Surrogate, First>;Cs;0;L;;;;;N;;;;;\nDB7F;<Non Private Use High Surrogate, Last>;Cs;0;L;;;;;N;;;;;\n0041;LATIN CAPITAL LETTER A;Lu;0;L;;;;;N;;;;0061;\n", encoding="utf-8")

    records = list(parse_unicode_data(source))

    assert len(records) == 1
    assert records[0].glyph == "A"


def test_unicode_ranges_include_interior_characters():
    records = list(parse_unicode_data(FIXTURE.with_name("UnicodeData.ranges.txt")))
    by_codepoint = {record.unicode_hex: record for record in records}
    assert len(records) == 32164
    assert {"U+4E00", "U+9FFF", "U+94DD", "U+AC00", "U+AC01", "U+D7A3"} <= by_codepoint.keys()
    assert all(record.basic_definition is None for record in records)
    assert by_codepoint["U+94DD"].source_field == "Range"


@pytest.mark.parametrize("rows", [
    "4E00;<CJK Ideograph, First>;Lo\n",
    "4E01;<CJK Ideograph, Last>;Lo\n",
    "4E01;<CJK Ideograph, First>;Lo\n4E00;<CJK Ideograph, Last>;Lo\n",
    "4E00;<CJK Ideograph, First>;Lo\n4E01;<Other, Last>;Lo\n",
    "4E00;<CJK Ideograph, First>;Lo\n4E01;<CJK Ideograph, Last>;Lu\n",
    "4E00;<CJK Ideograph, First>;Lo\n0041;LATIN CAPITAL LETTER A;Lu\n",
    "110000;OUT OF RANGE;Lo\n",
    "-1;OUT OF RANGE;Lo\n",
])
def test_unicode_rejects_incomplete_or_invalid_ranges(tmp_path, rows):
    path = tmp_path / "invalid.txt"
    path.write_text(rows, encoding="utf-8")
    with pytest.raises(ValueError):
        list(parse_unicode_data(path))


@pytest.mark.parametrize(("start", "end", "label"), [
    (0x20000, 0x20002, "CJK Ideograph Extension B"), (0xE000, 0xE002, "Private Use"),
])
def test_unicode_supports_extended_and_private_ranges(tmp_path, start, end, label):
    path = tmp_path / "range.txt"
    path.write_text(f"{start:X};<{label}, First>;Lo\n{end:X};<{label}, Last>;Lo\n", encoding="utf-8")
    records = list(parse_unicode_data(path))
    assert [ord(record.glyph) for record in records] == list(range(start, end + 1))
    assert all(record.basic_definition is None for record in records)
