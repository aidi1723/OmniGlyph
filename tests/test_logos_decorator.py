import pytest

from omniglyph.logos import LogosViolationError, logos_gate


def write_policy(path):
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
              "patterns": ["刷单"]
            },
            {
              "rule_id": "marketing_integrity.review_private_data",
              "description": "Review plans involving private data.",
              "severity": "review",
              "match_type": "regex",
              "patterns": ["private\\\\s+data"]
            }
          ]
        }""",
        encoding="utf-8",
    )


def test_logos_gate_allows_safe_plan_and_calls_wrapped_function(tmp_path):
    policy_path = tmp_path / "policy.json"
    write_policy(policy_path)
    calls = []

    @logos_gate(policy_path)
    def publish(action_plan, channel):
        calls.append((action_plan, channel))
        return "published"

    result = publish("Write honest product education.", "blog")

    assert result == "published"
    assert calls == [("Write honest product education.", "blog")]


def test_logos_gate_blocks_unsafe_plan_with_violation_result(tmp_path):
    policy_path = tmp_path / "policy.json"
    write_policy(policy_path)

    @logos_gate(policy_path)
    def publish(action_plan):
        return f"published: {action_plan}"

    with pytest.raises(LogosViolationError) as error:
        publish("本次增长计划包含刷单。")

    assert error.value.result["decision"] == "block"
    assert error.value.result["findings"][0]["matched"] == "刷单"


def test_logos_gate_allows_review_decision_by_default(tmp_path):
    policy_path = tmp_path / "policy.json"
    write_policy(policy_path)

    @logos_gate(policy_path)
    def publish(action_plan):
        return "published"

    assert publish("Analyze customer private data for segmentation.") == "published"


def test_logos_gate_can_block_review_decision(tmp_path):
    policy_path = tmp_path / "policy.json"
    write_policy(policy_path)

    @logos_gate(policy_path, block_on=("block", "review"))
    def publish(action_plan):
        return "published"

    with pytest.raises(LogosViolationError) as error:
        publish("Analyze customer private data for segmentation.")

    assert error.value.result["decision"] == "review"
