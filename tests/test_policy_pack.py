import json
import subprocess
import sys
from pathlib import Path

import pytest

from omniglyph.policy_pack import (
    ensure_allowed_policy_pack_path,
    init_policy_pack,
    load_policy_pack,
    validate_policy_pack,
)


def write_policy_pack(path: Path) -> None:
    path.mkdir()
    (path / "policy.json").write_text(
        json.dumps(
            {
                "schema": "omniglyph.policy_pack:0.1",
                "policy_id": "company.acme.agent_policy",
                "namespace": "private_acme",
                "name": "ACME Agent Policy",
                "version": "2026.07.05",
                "owner_type": "enterprise",
                "license": "private",
                "visibility": "private",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (path / "intents.csv").write_text(
        "intent_id,canonical_phrase,decision,risk_level,requires_approval,allowed_roles,audit_required,parameters_schema\n"
        'network.restart,restart network service,review,high,true,admin,true,"{""type"":""object""}"\n'
        'ticket.create,create support ticket,allow,low,false,admin;operator,true,"{}"\n'
        'system.delete_root,delete root filesystem,block,critical,false,,true,"{}"\n',
        encoding="utf-8",
    )


def test_validate_policy_pack_accepts_pack_directory(tmp_path):
    pack_dir = tmp_path / "policy"
    write_policy_pack(pack_dir)

    report = validate_policy_pack(pack_dir)

    assert report["status"] == "pass"
    assert report["policy"]["policy_id"] == "company.acme.agent_policy"
    assert report["policy"]["namespace"] == "private_acme"
    assert report["summary"] == {"intent_count": 3, "allow_count": 1, "review_count": 1, "block_count": 1}
    assert report["errors"] == []


def test_load_policy_pack_converts_rows_to_manifest(tmp_path):
    pack_dir = tmp_path / "policy"
    write_policy_pack(pack_dir)

    pack = load_policy_pack(pack_dir)
    manifest = pack.to_manifest()

    assert manifest["policy"]["policy_id"] == "company.acme.agent_policy"
    assert manifest["policy"]["namespace"] == "private_acme"
    assert manifest["policy"]["version"] == "2026.07.05"
    assert manifest["intents"][0]["intent_id"] == "network.restart"
    assert manifest["intents"][0]["allowed_roles"] == ["admin"]
    assert manifest["intents"][0]["parameters_schema"] == {"type": "object"}


def test_validate_policy_pack_reports_invalid_rows(tmp_path):
    pack_dir = tmp_path / "bad-policy"
    pack_dir.mkdir()
    (pack_dir / "policy.json").write_text(
        json.dumps(
            {
                "schema": "omniglyph.policy_pack:0.1",
                "policy_id": "bad",
                "namespace": "public_bad",
                "name": "Bad",
                "version": "1",
                "owner_type": "personal",
                "license": "private",
                "visibility": "private",
            }
        ),
        encoding="utf-8",
    )
    (pack_dir / "intents.csv").write_text(
        "intent_id,canonical_phrase,decision,risk_level,requires_approval,allowed_roles,audit_required,parameters_schema\n"
        "bad.intent,Bad,sometimes,severe,maybe,admin,true,[]\n",
        encoding="utf-8",
    )

    report = validate_policy_pack(pack_dir)

    assert report["status"] == "fail"
    assert "policy.json: namespace should start with private_ for user policy packs" in report["errors"]
    assert "intents.csv row 2: decision must be one of allow, block, review" in report["errors"]
    assert "intents.csv row 2: risk_level must be one of critical, high, low, medium" in report["errors"]
    assert "intents.csv row 2: requires_approval must be a boolean string" in report["errors"]
    assert "intents.csv row 2: parameters_schema must be a JSON object" in report["errors"]


def test_init_policy_pack_creates_valid_template(tmp_path):
    target = tmp_path / "starter"

    init_policy_pack(target, namespace="private_starter", policy_id="personal.starter", name="Starter Policy")

    assert (target / "policy.json").exists()
    assert (target / "intents.csv").exists()
    report = validate_policy_pack(target)
    assert report["status"] == "pass"
    assert report["policy"]["policy_id"] == "personal.starter"


def test_ensure_allowed_policy_pack_path_blocks_outside_root(tmp_path):
    root = tmp_path / "allowed"
    inside = root / "policy"
    outside = tmp_path / "outside"
    inside.mkdir(parents=True)
    outside.mkdir()

    ensure_allowed_policy_pack_path(str(inside), root)
    with pytest.raises(ValueError, match="outside OMNIGLYPH_POLICY_PACK_ROOT"):
        ensure_allowed_policy_pack_path(str(outside), root)


def test_cli_init_validate_and_enforce_policy_pack(tmp_path):
    target = tmp_path / "cli-policy"

    init_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "omniglyph.cli",
            "init-policy-pack",
            str(target),
            "--namespace",
            "private_cli",
            "--policy-id",
            "personal.cli",
            "--name",
            "CLI Policy",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    validate_result = subprocess.run(
        [sys.executable, "-m", "omniglyph.cli", "validate-policy-pack", str(target)],
        check=False,
        capture_output=True,
        text=True,
    )
    enforce_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "omniglyph.cli",
            "enforce-intent",
            "example.review",
            "--policy-pack",
            str(target),
            "--actor-role",
            "admin",
            "--parameters",
            '{"ticket":"123"}',
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert init_result.returncode == 0, init_result.stderr
    assert "Created policy pack" in init_result.stdout
    assert validate_result.returncode == 0, validate_result.stderr
    assert '"status": "pass"' in validate_result.stdout
    assert enforce_result.returncode == 0, enforce_result.stderr
    assert json.loads(enforce_result.stdout)["decision"] == "review"
