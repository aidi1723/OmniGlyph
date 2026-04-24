from pathlib import Path

from omniglyph.code_linter import scan_file, scan_text


def test_scan_text_detects_zero_width_space():
    report = scan_text("result = 1\u200b\n", source_name="sample.py")

    assert report["status"] == "warn"
    assert report["summary"]["finding_count"] == 1
    finding = report["findings"][0]
    assert finding["rule_id"] == "unicode-invisible-format"
    assert finding["unicode_hex"] == "U+200B"
    assert finding["name"] == "ZERO WIDTH SPACE"
    assert finding["line"] == 1
    assert finding["column"] == 11


def test_scan_text_detects_cyrillic_homoglyph_in_latin_code():
    report = scan_text("v\u0430lue = 42\n", source_name="sample.py")

    assert report["status"] == "warn"
    assert report["findings"][0]["rule_id"] == "unicode-cross-script-homoglyph-risk"
    assert report["findings"][0]["unicode_hex"] == "U+0430"
    assert report["findings"][0]["script_hint"] == "Cyrillic"


def test_scan_text_detects_bidi_control():
    report = scan_text("safe = True # \u202e hidden\n", source_name="sample.py")

    assert report["status"] == "warn"
    assert report["findings"][0]["rule_id"] == "unicode-bidi-control"
    assert report["findings"][0]["unicode_hex"] == "U+202E"


def test_scan_text_allows_clean_ascii_code():
    report = scan_text("value = 42\nprint(value)\n", source_name="sample.py")

    assert report["status"] == "pass"
    assert report["summary"]["finding_count"] == 0
    assert report["findings"] == []


def test_scan_file_reports_file_path(tmp_path):
    path = tmp_path / "poison.py"
    path.write_text("v\u0430lue = 1\n", encoding="utf-8")

    report = scan_file(path)

    assert report["source"] == str(path)
    assert report["status"] == "warn"
    assert report["findings"][0]["line"] == 1
