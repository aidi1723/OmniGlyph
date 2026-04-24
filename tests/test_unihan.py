from pathlib import Path

from omniglyph.unihan import parse_unihan_data


FIXTURE = Path(__file__).parent / "fixtures" / "Unihan.sample.txt"


def test_parse_unihan_data_maps_codepoint_to_properties():
    properties = list(parse_unihan_data(FIXTURE))

    first = properties[0]
    assert first.glyph == "铝"
    assert first.unicode_hex == "U+94DD"
    assert first.property_name == "kMandarin"
    assert first.property_value == "lǚ"


def test_parse_unihan_data_skips_comments_and_malformed_rows():
    properties = list(parse_unihan_data(FIXTURE))

    assert len(properties) == 5
    assert all(item.property_name != "bad-row" for item in properties)


def test_parse_unihan_data_keeps_multiple_fields_for_same_glyph():
    properties = list(parse_unihan_data(FIXTURE))

    aluminum = [item for item in properties if item.glyph == "铝"]
    names = {item.property_name for item in aluminum}
    assert names == {"kMandarin", "kDefinition", "kTotalStrokes"}
