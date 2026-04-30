from omniglyph.logos.loader import load_policy_file, load_policy_files
from omniglyph.logos.models import LogosPolicy, LogosRule

import pytest


def sample_policy_mapping():
    return {
        "policy_id": "marketing_integrity.growth.v1",
        "concept": "growth",
        "namespace": "business.marketing",
        "definition": "Growth must not fabricate demand.",
        "version": "0.1.0",
        "rules": [
            {
                "rule_id": "marketing_integrity.no_fake_orders",
                "description": "Block fake order manipulation.",
                "severity": "block",
                "match_type": "literal",
                "patterns": ["刷单", "fake orders"],
                "allow_context": ["不要刷单", "avoid fake orders"],
                "source": {
                    "type": "project_policy",
                    "name": "LogosGate Genesis Policy Pack",
                    "version": "0.1.0",
                },
            }
        ],
    }


def test_logos_policy_from_mapping_parses_rules():
    policy = LogosPolicy.from_mapping(sample_policy_mapping())

    assert policy.schema == "omniglyph.logos.policy:0.1"
    assert policy.policy_id == "marketing_integrity.growth.v1"
    assert policy.concept == "growth"
    assert policy.namespace == "business.marketing"
    assert policy.rules[0].rule_id == "marketing_integrity.no_fake_orders"
    assert policy.rules[0].severity == "block"
    assert policy.rules[0].patterns == ["刷单", "fake orders"]
    assert policy.rules[0].source["name"] == "LogosGate Genesis Policy Pack"


def test_logos_policy_rejects_invalid_severity():
    mapping = sample_policy_mapping()
    mapping["rules"][0]["severity"] = "panic"

    with pytest.raises(ValueError, match="severity"):
        LogosPolicy.from_mapping(mapping)


def test_logos_policy_rejects_invalid_match_type():
    mapping = sample_policy_mapping()
    mapping["rules"][0]["match_type"] = "embedding"

    with pytest.raises(ValueError, match="match_type"):
        LogosPolicy.from_mapping(mapping)


def test_logos_rule_requires_patterns():
    with pytest.raises(ValueError, match="patterns"):
        LogosRule.from_mapping(
            {
                "rule_id": "missing.patterns",
                "description": "Invalid rule.",
                "severity": "block",
                "match_type": "literal",
                "patterns": [],
            }
        )


def test_load_policy_file_reads_json(tmp_path):
    path = tmp_path / "policy.json"
    path.write_text(
        """{
          "policy_id": "marketing_integrity.growth.v1",
          "concept": "growth",
          "namespace": "business.marketing",
          "definition": "Growth must not fabricate demand.",
          "version": "0.1.0",
          "rules": [
            {
              "rule_id": "marketing_integrity.no_fake_orders",
              "description": "Block fake order manipulation.",
              "severity": "block",
              "match_type": "literal",
              "patterns": ["刷单"],
              "allow_context": ["不要刷单"],
              "source": {"type": "project_policy", "name": "Fixture", "version": "0.1.0"}
            }
          ]
        }""",
        encoding="utf-8",
    )

    policy = load_policy_file(path)

    assert policy.policy_id == "marketing_integrity.growth.v1"
    assert policy.rules[0].patterns == ["刷单"]


def test_load_policy_files_reads_all_json_files(tmp_path):
    second = tmp_path / "second.json"
    first = tmp_path / "first.json"
    second.write_text(
        """{
          "policy_id": "policy.two",
          "concept": "safety",
          "namespace": "code.execution",
          "definition": "Two.",
          "version": "0.1.0",
          "rules": [{"rule_id": "two.rule", "description": "Two.", "severity": "block", "match_type": "literal", "patterns": ["two"]}]
        }""",
        encoding="utf-8",
    )
    first.write_text(
        """{
          "policy_id": "policy.one",
          "concept": "growth",
          "namespace": "business.marketing",
          "definition": "One.",
          "version": "0.1.0",
          "rules": [{"rule_id": "one.rule", "description": "One.", "severity": "warn", "match_type": "literal", "patterns": ["one"]}]
        }""",
        encoding="utf-8",
    )

    policies = load_policy_files(tmp_path)

    assert [policy.policy_id for policy in policies] == ["policy.one", "policy.two"]
