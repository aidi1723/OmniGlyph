import json
import subprocess
import sys


def test_scan_code_cli_outputs_json_report(tmp_path):
    path = tmp_path / "poison.py"
    path.write_text("v\u0430lue = 1\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "omniglyph.cli", "scan-code", str(path), "--format", "json"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "warn"
    assert payload["findings"][0]["unicode_hex"] == "U+0430"


def test_scan_code_cli_can_fail_on_warning(tmp_path):
    path = tmp_path / "poison.py"
    path.write_text("value = 1\u200b\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "omniglyph.cli", "scan-code", str(path), "--fail-on", "warning"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "U+200B" in result.stdout
