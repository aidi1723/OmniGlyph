import pytest

from omniglyph.logos.models import LogosPolicy
from omniglyph.logos.validator import validate_action


def sample_policy():
    return LogosPolicy.from_mapping(
        {
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
                },
                {
                    "rule_id": "marketing_integrity.review_private_data",
                    "description": "Review plans involving private data.",
                    "severity": "review",
                    "match_type": "regex",
                    "patterns": [r"private\s+data"],
                },
                {
                    "rule_id": "marketing_integrity.warn_aggressive_growth",
                    "description": "Warn about aggressive growth claims.",
                    "severity": "warn",
                    "match_type": "literal",
                    "patterns": ["aggressive growth"],
                },
            ],
        }
    )


def test_clean_plan_returns_allow_pass_without_findings():
    result = validate_action("Focus on natural content growth.", sample_policy())

    assert result["decision"] == "allow"
    assert result["status"] == "pass"
    assert result["findings"] == []
    assert result["limits"] == []


def test_literal_block_match_returns_unsafe_decision():
    result = validate_action("本次增长计划包含刷单。", sample_policy())

    assert result["decision"] == "block"
    assert result["status"] == "unsafe"
    assert result["findings"][0]["rule_id"] == "marketing_integrity.no_fake_orders"
    assert result["findings"][0]["matched"] == "刷单"
    assert result["limits"] == ["Blocked by one or more LogosGate policy rules."]


def test_allow_context_suppresses_literal_block():
    result = validate_action("本次增长计划明确要求不要刷单，只做自然流量。", sample_policy())

    assert result["decision"] == "allow"
    assert result["status"] == "pass"
    assert result["findings"] == []
    assert result["limits"] == []


def test_allow_context_only_suppresses_the_covered_match():
    result = validate_action("不要刷单是规则，但这个计划仍然安排刷单。", sample_policy())

    assert result["decision"] == "block"
    assert len(result["findings"]) == 1
    assert result["findings"][0]["matched"] == "刷单"


def test_regex_review_match_returns_needs_review_decision():
    result = validate_action("Analyze customer private data for segmentation.", sample_policy())

    assert result["decision"] == "review"
    assert result["status"] == "needs_review"
    assert result["findings"][0]["rule_id"] == "marketing_integrity.review_private_data"
    assert result["limits"] == ["Human review is required before execution."]


def test_regex_matching_checks_beyond_allowed_first_match():
    policy = LogosPolicy.from_mapping(
        {
            "policy_id": "marketing_integrity.privacy.v1",
            "concept": "privacy",
            "namespace": "business.marketing",
            "definition": "Private data collection requires review.",
            "version": "0.1.0",
            "rules": [
                {
                    "rule_id": "marketing_integrity.review_private_data",
                    "description": "Review plans involving private data.",
                    "severity": "review",
                    "match_type": "regex",
                    "patterns": [r"private\s+data"],
                    "allow_context": ["avoid private data"],
                }
            ],
        }
    )

    result = validate_action("We avoid private data, but later collect private data for ads.", policy)

    assert result["decision"] == "review"
    assert len(result["findings"]) == 1
    assert result["findings"][0]["matched"] == "private data"


def test_warn_only_match_returns_warn_decision():
    result = validate_action("Use aggressive growth copy for the campaign.", sample_policy())

    assert result["decision"] == "warn"
    assert result["status"] == "warn"
    assert result["findings"][0]["severity"] == "warn"
    assert result["limits"] == ["Policy warning should be logged before execution."]


def test_validate_action_rejects_blank_text():
    with pytest.raises(ValueError, match="text must be a non-empty string"):
        validate_action(" ", sample_policy())
