
import pytest

from omniglyph.code_linter import format_text_report, scan_file, scan_path, scan_text


def test_scan_text_rejects_oversized_input_and_directory_scans_continue(tmp_path):
    from omniglyph.limits import MAX_TEXT_CHARS

    with pytest.raises(ValueError, match="exceeds"):
        scan_text("a" * (MAX_TEXT_CHARS + 1), source_name="huge.py")

    (tmp_path / "huge.py").write_text("a" * (MAX_TEXT_CHARS + 1), encoding="utf-8")
    (tmp_path / "small.py").write_text("ok = 1\u200b\n", encoding="utf-8")
    report = scan_path(tmp_path)

    assert report["status"] == "error"
    assert report["failed_files"][0]["error_type"] == "TextLimitError"
    assert report["findings"][0]["rule_id"] == "unicode-invisible-format"
    assert report["findings"][0]["source"].endswith("small.py")


def test_scan_text_flags_ascii_controls_and_accepts_printable_ascii():
    report = scan_text("ok\x00\n", source_name="sample.py")

    assert report["findings"][0]["rule_id"] == "unicode-control-character"
    assert scan_text("value = 1\n", source_name="sample.py")["status"] == "pass"


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
    assert report["summary"]["risk_level"] == "medium"
    assert report["summary"]["rule_counts"] == {"unicode-confusable": 1}
    finding = report["findings"][0]
    assert finding["rule_id"] == "unicode-confusable"
    assert finding["unicode_hex"] == "U+0430"
    assert finding["script_hint"] == "Cyrillic"
    assert finding["confusable_with"] == "a"
    assert finding["source_id"] == "source:unicode-confusables:minimal"
    assert finding["suggested_action"] == "review"
    assert finding["auto_fixable"] is False
    assert "Latin" in finding["why_it_matters"]


def test_scan_text_names_more_identical_confusables_and_keeps_other_letters_generic():
    cyrillic = scan_text("to\u0440en = 1\n", source_name="sample.py")
    assert cyrillic["findings"][0]["rule_id"] == "unicode-confusable"
    assert cyrillic["findings"][0]["confusable_with"] == "p"

    greek = scan_text("pi = \u03c0\n", source_name="sample.py")
    assert greek["findings"][0]["rule_id"] == "unicode-cross-script-homoglyph-risk"
    assert "confusable_with" not in greek["findings"][0]


def test_scan_text_detects_bidi_control():
    report = scan_text("safe = True # \u202e hidden\n", source_name="sample.py")

    assert report["status"] == "warn"
    assert report["summary"]["risk_level"] == "high"
    assert report["findings"][0]["rule_id"] == "unicode-bidi-control"
    assert report["findings"][0]["unicode_hex"] == "U+202E"


def test_scan_text_detects_fullwidth_and_halfwidth_forms():
    report = scan_text("Ａ = 1\n", source_name="sample.py")

    assert report["status"] == "warn"
    finding = report["findings"][0]
    assert finding["rule_id"] == "unicode-fullwidth-halfwidth-form"
    assert finding["unicode_hex"] == "U+FF21"
    assert finding["normalized"] == "A"


def test_scan_text_detects_nfkc_normalization_changes():
    report = scan_text("K = 1\n", source_name="sample.py")

    assert report["status"] == "warn"
    finding = report["findings"][0]
    assert finding["rule_id"] == "unicode-nfkc-normalization-change"
    assert finding["unicode_hex"] == "U+212A"
    assert finding["normalized"] == "K"


def test_scan_text_allows_clean_ascii_code():
    report = scan_text("value = 42\nprint(value)\n", source_name="sample.py")

    assert report["status"] == "pass"
    assert report["summary"]["finding_count"] == 0
    assert report["summary"]["risk_level"] == "none"
    assert report["summary"]["rule_counts"] == {}
    assert report["findings"] == []


def test_format_text_report_includes_review_guidance():
    report = scan_text("v\u0430lue = 1\n", source_name="sample.py")

    output = format_text_report(report)

    assert "confusable with a" in output
    assert "action=review" in output


def test_scan_file_reports_file_path(tmp_path):
    path = tmp_path / "poison.py"
    path.write_text("v\u0430lue = 1\n", encoding="utf-8")

    report = scan_file(path)

    assert report["source"] == str(path)
    assert report["status"] == "warn"
    assert report["findings"][0]["line"] == 1


def test_scan_path_skips_virtualenv_and_build_artifact_directories(tmp_path):
    source_path = tmp_path / "src" / "app.py"
    source_path.parent.mkdir()
    source_path.write_text("value = 1\n", encoding="utf-8")
    venv_path = tmp_path / ".venv" / "lib.py"
    venv_path.parent.mkdir()
    venv_path.write_text("v\u0430lue = 1\n", encoding="utf-8")
    dist_path = tmp_path / "dist" / "bundle.py"
    dist_path.parent.mkdir()
    dist_path.write_text("v\u0430lue = 1\n", encoding="utf-8")

    report = scan_path(tmp_path)

    assert report["status"] == "pass"
    assert report["files"] == [str(source_path)]


def test_scan_path_reports_decode_errors_without_aborting(tmp_path):
    source_path = tmp_path / "src" / "app.py"
    source_path.parent.mkdir()
    source_path.write_text("value = 1\n", encoding="utf-8")
    bad_path = tmp_path / "src" / "bad.py"
    bad_path.write_bytes(b"\xff\xfe\xfa")

    report = scan_path(tmp_path)

    assert report["status"] == "error"
    assert report["summary"]["file_count"] == 1
    assert report["summary"]["failed_count"] == 1
    assert report["files"] == [str(source_path)]
    assert report["failed_files"] == [
        {
            "source": str(bad_path),
            "error_type": "UnicodeDecodeError",
            "message": "file is not valid UTF-8 text",
        }
    ]


def test_scan_path_reports_missing_path_as_error(tmp_path):
    missing_path = tmp_path / "missing"

    report = scan_path(missing_path)

    assert report["status"] == "error"
    assert report["summary"]["file_count"] == 0
    assert report["summary"]["failed_count"] == 1
    assert report["files"] == []
    assert report["failed_files"] == [
        {
            "source": str(missing_path),
            "error_type": "FileNotFoundError",
            "message": "path does not exist",
        }
    ]
