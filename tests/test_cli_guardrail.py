import json
import os
import subprocess
import sys
from pathlib import Path

from omniglyph.domain_pack import parse_domain_pack
from omniglyph.repository import GlyphRepository, SourceSnapshot


def seeded_domain_database(tmp_path):
    database_path = tmp_path / "test.sqlite3"
    repository = GlyphRepository(database_path)
    repository.initialize()
    source_id = repository.add_source_snapshot(SourceSnapshot("Private Domain Pack", "file://domain", "fixture", "sha-domain", "private", "domain"))
    repository.insert_lexical_entries(list(parse_domain_pack(Path("tests/fixtures/domain_pack.csv"), "private_building_materials")), source_id)
    return database_path


def run_cli(tmp_path, *args):
    env = os.environ.copy()
    env["OMNIGLYPH_SQLITE_PATH"] = str(seeded_domain_database(tmp_path))
    return subprocess.run(
        [sys.executable, "-m", "omniglyph.cli", *args],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def test_enforce_output_cli_blocks_unknown_terms_by_default(tmp_path):
    result = run_cli(tmp_path, "enforce-output", "--term", "FOB", "--term", "HS 7604.99X")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["schema"] == "omniglyph.guardrail:0.1"
    assert payload["mode"] == "strict_source_grounding"
    assert payload["decision"] == "block"
    assert payload["unknown"] == ["HS 7604.99X"]
    assert payload["review_packet"]["summary"]["actions"] == ["block"]


def test_enforce_output_cli_accepts_policy_json(tmp_path):
    result = run_cli(
        tmp_path,
        "enforce-output",
        "--term",
        "FOB",
        "--term",
        "HS 7604.99X",
        "--policy",
        '{"unknown_action":"review"}',
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["mode"] == "policy_source_grounding"
    assert payload["decision"] == "review"
    assert payload["review_packet"]["summary"]["actions"] == ["review"]


def test_enforce_output_cli_includes_audit_for_actor_id(tmp_path):
    result = run_cli(
        tmp_path,
        "enforce-output",
        "--term",
        "FOB",
        "--actor-id",
        "agent:quote",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["decision"] == "allow"
    assert payload["audit"]["actor"] == {"id": "agent:quote"}
    assert payload["audit"]["action"] == "enforce_grounded_output"


def test_enforce_output_cli_rejects_invalid_policy_json(tmp_path):
    result = run_cli(tmp_path, "enforce-output", "--term", "FOB", "--policy", "{bad")

    assert result.returncode == 2
    assert "--policy must be a JSON object" in result.stderr


def test_enforce_output_cli_rejects_non_object_policy_json(tmp_path):
    result = run_cli(tmp_path, "enforce-output", "--term", "FOB", "--policy", "[]")

    assert result.returncode == 2
    assert "--policy must be a JSON object" in result.stderr
