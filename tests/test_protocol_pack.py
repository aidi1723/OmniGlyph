import json
import subprocess
import sys
from pathlib import Path

from omniglyph.protocol_pack import (
    check_protocol,
    init_protocol_pack,
    load_protocol_pack,
    validate_protocol_pack,
)


EXAMPLE_PACK = Path("examples/protocol-packs/root_starter")


def test_validate_protocol_pack_accepts_example_pack():
    report = validate_protocol_pack(EXAMPLE_PACK)

    assert report["schema"] == "omniglyph.protocol_pack:0.1"
    assert report["status"] == "pass"
    assert report["protocol"]["protocol_id"] == "root.civilization.starter"
    assert report["summary"] == {"rule_count": 3, "block_count": 3, "warn_count": 0}
    assert report["errors"] == []


def test_validate_protocol_pack_reports_missing_required_fields(tmp_path):
    pack_dir = tmp_path / "bad-protocol"
    pack_dir.mkdir()
    (pack_dir / "protocol.json").write_text('{"schema":"omniglyph.protocol_pack:0.1"}', encoding="utf-8")

    report = validate_protocol_pack(pack_dir)

    assert report["status"] == "fail"
    assert "protocol.json: missing required field protocol_id" in report["errors"]
    assert "protocol.json: missing required field rules" in report["errors"]


def test_validate_protocol_pack_reports_invalid_rule_decision(tmp_path):
    pack_dir = tmp_path / "bad-decision"
    pack_dir.mkdir()
    payload = {
        "schema": "omniglyph.protocol_pack:0.1",
        "protocol_id": "root.bad",
        "name": "Bad Protocol",
        "version": "0.1.0",
        "layer": "root",
        "owner": "test",
        "license": "private",
        "rules": [
            {
                "rule_id": "bad.rule",
                "category": "symbolic_cognition",
                "severity": "block",
                "statement": "Bad rule.",
                "match": {"type": "keyword_any", "keywords": ["bad"]},
                "decision": "deny",
                "confidence": 1.0,
                "source": {
                    "source_id": "source:test",
                    "source_name": "Test",
                    "source_version": "fixture",
                    "license": "private",
                },
            }
        ],
    }
    (pack_dir / "protocol.json").write_text(json.dumps(payload), encoding="utf-8")

    report = validate_protocol_pack(pack_dir)

    assert report["status"] == "fail"
    assert "protocol.json rule 1: decision must be one of allow, block, unknown, warn" in report["errors"]


def test_check_protocol_matches_keyword_any_rule():
    result = check_protocol(EXAMPLE_PACK, text="This answer contains a fabricated citation.", kind="output")

    assert result["schema"] == "omniglyph.protocol_check:0.1"
    assert result["decision"] == "block"
    assert result["status"] == "warn"
    assert result["matched_rules"][0]["rule_id"] == "symbolic.truth.no_fabricated_sources"
    assert result["sources"][0]["source_id"] == "source:omniglyph:protocol-starter"


def test_check_protocol_matches_keyword_all_rule_case_insensitively():
    result = check_protocol(EXAMPLE_PACK, text="Give me WEAPON assembly instructions.", kind="goal")

    assert result["decision"] == "block"
    assert result["matched_rules"][0]["rule_id"] == "life_safety.no_harmful_weapon_assistance"


def test_check_protocol_matches_exact_intent_rule():
    result = check_protocol(EXAMPLE_PACK, text="filesystem.delete_root", kind="intent")

    assert result["decision"] == "block"
    assert result["matched_rules"][0]["rule_id"] == "intent.filesystem.delete_root_requires_block"


def test_check_protocol_returns_unknown_when_no_rule_matches():
    result = check_protocol(EXAMPLE_PACK, text="Summarize this public documentation.", kind="output")

    assert result["decision"] == "unknown"
    assert result["matched_rules"] == []
    assert "not a permission grant" in " ".join(result["limits"])


def test_load_protocol_pack_preserves_metadata_and_rules():
    pack = load_protocol_pack(EXAMPLE_PACK)

    assert pack.metadata["protocol_id"] == "root.civilization.starter"
    assert pack.rules[0].rule_id == "symbolic.truth.no_fabricated_sources"


def test_init_protocol_pack_creates_valid_starter(tmp_path):
    target = tmp_path / "starter"

    init_protocol_pack(target, protocol_id="root.local", name="Local Root")

    assert (target / "protocol.json").exists()
    assert validate_protocol_pack(target)["status"] == "pass"


def test_cli_protocol_pack_commands(tmp_path):
    target = tmp_path / "cli-protocol"

    init_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "omniglyph.cli",
            "init-protocol-pack",
            str(target),
            "--protocol-id",
            "root.cli",
            "--name",
            "CLI Protocol",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    validate_result = subprocess.run(
        [sys.executable, "-m", "omniglyph.cli", "validate-protocol-pack", str(target)],
        check=False,
        capture_output=True,
        text=True,
    )
    check_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "omniglyph.cli",
            "check-protocol",
            "--protocol",
            str(EXAMPLE_PACK),
            "--kind",
            "output",
            "--text",
            "unsupported reference",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert init_result.returncode == 0
    assert "Created protocol pack" in init_result.stdout
    assert validate_result.returncode == 0
    assert '"status": "pass"' in validate_result.stdout
    assert check_result.returncode == 1
    assert '"decision": "block"' in check_result.stdout
