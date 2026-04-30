import json
import subprocess
import sys


def test_logos_validate_blocks_marketing_integrity_violation():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "omniglyph.cli",
            "logos",
            "validate",
            "--policy",
            "examples/logos-policies/marketing_integrity.json",
            "--text",
            "计划雇佣水军刷单。",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["decision"] == "block"
    assert payload["findings"][0]["matched"] == "刷单"


def test_logos_validate_allows_marketing_integrity_safe_text():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "omniglyph.cli",
            "logos",
            "validate",
            "--policy",
            "examples/logos-policies/marketing_integrity.json",
            "--text",
            "通过 SEO 和内容增长。",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["decision"] == "allow"


def test_logos_validate_reads_text_file(tmp_path):
    plan = tmp_path / "plan.txt"
    plan.write_text("Run rm -rf / to reset.", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "omniglyph.cli",
            "logos",
            "validate",
            "--policy",
            "examples/logos-policies/code_safety.json",
            "--text-file",
            str(plan),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["decision"] == "block"
    assert payload["findings"][0]["rule_id"] == "code_safety.no_recursive_root_delete"
