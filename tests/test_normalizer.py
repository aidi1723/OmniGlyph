from pathlib import Path

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


def test_parse_unicode_data_skips_malformed_rows(tmp_path):
    malformed = tmp_path / "UnicodeData.malformed.txt"
    malformed.write_text("0041;LATIN CAPITAL LETTER A\nnot-hex;BROKEN\n", encoding="utf-8")

    records = list(parse_unicode_data(malformed))

    assert len(records) == 1
    assert records[0].glyph == "A"


def test_parse_unicode_data_covers_combining_marks_variation_selectors_and_emoji():
    records = list(parse_unicode_data(FIXTURE))

    assert records[1].glyph == "\u0301"
    assert records[2].unicode_hex == "U+FE0F"
    assert records[4].glyph == "😀"


def test_parse_unicode_data_skips_surrogate_codepoints(tmp_path):
    source = tmp_path / "UnicodeData.surrogate.txt"
    source.write_text("D800;<Non Private Use High Surrogate, First>;Cs;0;L;;;;;N;;;;;\n0041;LATIN CAPITAL LETTER A;Lu;0;L;;;;;N;;;;0061;\n", encoding="utf-8")

    records = list(parse_unicode_data(source))

    assert len(records) == 1
    assert records[0].glyph == "A"
