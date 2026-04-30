from pathlib import Path

from omniglyph.logos.loader import load_policy_files
from omniglyph.logos.validator import validate_action


def policies_by_id():
    return {policy.policy_id: policy for policy in load_policy_files(Path("examples/logos-policies"))}


def test_example_policy_files_are_valid():
    policies = load_policy_files(Path("examples/logos-policies"))

    assert {policy.policy_id for policy in policies} == {
        "code_safety.execution.v1",
        "marketing_integrity.growth.v1",
        "trade_compliance.commitment.v1",
    }


def test_marketing_policy_blocks_fake_growth():
    policy = policies_by_id()["marketing_integrity.growth.v1"]

    result = validate_action("计划雇佣水军刷单并制造虚假评价。", policy)

    assert result["decision"] == "block"
    assert result["findings"][0]["rule_id"] == "marketing_integrity.no_fake_orders"


def test_code_safety_policy_blocks_rm_root():
    policy = policies_by_id()["code_safety.execution.v1"]

    result = validate_action("Run rm -rf / to reset the machine.", policy)

    assert result["decision"] == "block"
    assert result["findings"][0]["rule_id"] == "code_safety.no_recursive_root_delete"


def test_trade_policy_requires_review_for_contract_commitment():
    policy = policies_by_id()["trade_compliance.commitment.v1"]

    result = validate_action("向客户承诺最终合同价格和 HS code。", policy)

    assert result["decision"] == "review"
    assert result["findings"][0]["rule_id"] == "trade_compliance.review_contract_commitment"
