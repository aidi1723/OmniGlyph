from omniglyph.mcp_server import build_tools_list, handle_mcp_request


def test_build_tools_list_includes_validate_action_policy():
    names = {tool["name"] for tool in build_tools_list()}

    assert "validate_action_policy" in names


def test_handle_mcp_validate_action_policy_blocks_matching_action():
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "validate_action_policy",
                "arguments": {
                    "policy_path": "examples/logos-policies/marketing_integrity.json",
                    "text": "计划雇佣水军刷单。",
                },
            },
        }
    )

    payload = response["result"]["content"][0]["json"]
    assert payload["decision"] == "block"
    assert payload["findings"][0]["matched"] == "刷单"


def test_handle_mcp_validate_action_policy_requires_text():
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "validate_action_policy",
                "arguments": {"policy_path": "examples/logos-policies/marketing_integrity.json"},
            },
        }
    )

    assert response["error"]["code"] == -32602
    assert "text" in response["error"]["message"]


def test_handle_mcp_validate_action_policy_rejects_nonexistent_policy_path():
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "validate_action_policy",
                "arguments": {"policy_path": "examples/logos-policies/missing.json", "text": "计划雇佣水军刷单。"},
            },
        }
    )

    assert response["error"]["code"] == -32602
    assert "policy_path not found" in response["error"]["message"]


def test_handle_mcp_validate_action_policy_rejects_malformed_policy_file(tmp_path):
    policy_path = tmp_path / "malformed.json"
    policy_path.write_text("{", encoding="utf-8")

    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "validate_action_policy",
                "arguments": {"policy_path": str(policy_path), "text": "计划雇佣水军刷单。"},
            },
        }
    )

    assert response["error"]["code"] == -32602
    assert "not valid JSON" in response["error"]["message"]


def test_handle_mcp_validate_action_policy_rejects_invalid_policy_schema(tmp_path):
    policy_path = tmp_path / "invalid-policy.json"
    policy_path.write_text('{"policy_id": "broken"}', encoding="utf-8")

    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "validate_action_policy",
                "arguments": {"policy_path": str(policy_path), "text": "计划雇佣水军刷单。"},
            },
        }
    )

    assert response["error"]["code"] == -32602
    assert "invalid policy file" in response["error"]["message"]
