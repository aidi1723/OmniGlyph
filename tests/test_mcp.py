import json

from omniglyph import __version__
from omniglyph.domain_pack import parse_domain_pack
from omniglyph.mcp_server import build_tools_list, handle_mcp_request
from omniglyph.normalizer import GlyphRecord
from omniglyph.repository import GlyphRepository, SourceSnapshot
from omniglyph.unihan import parse_unihan_data


def mcp_json(response):
    content = response["result"]["content"][0]
    assert content["type"] == "text"
    return json.loads(content["text"])


def seeded_glyph_repository(tmp_path):
    from pathlib import Path

    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    unicode_source = repository.add_source_snapshot(SourceSnapshot("Unicode Character Database", "file://fixture", "fixture", "sha-u", "Unicode Terms of Use", "fixture"))
    unihan_source = repository.add_source_snapshot(SourceSnapshot("Unihan Database", "file://unihan", "fixture", "sha-unihan", "Unicode Terms of Use", "unihan"))
    repository.insert_glyph_records([GlyphRecord(glyph="铝", unicode_hex="U+94DD", basic_definition="CJK UNIFIED IDEOGRAPH-94DD")], unicode_source)
    repository.insert_unihan_properties(list(parse_unihan_data(Path("tests/fixtures/Unihan.sample.txt"))), unihan_source)
    return repository


def seeded_domain_repository(tmp_path):
    from pathlib import Path

    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    source_id = repository.add_source_snapshot(SourceSnapshot("Private Domain Pack", "file://domain", "fixture", "sha-domain", "private", "domain"))
    repository.insert_lexical_entries(list(parse_domain_pack(Path("tests/fixtures/domain_pack.csv"), "private_building_materials")), source_id)
    return repository


def write_mcp_policy_pack(path):
    path.mkdir()
    (path / "policy.json").write_text(
        '{"schema":"omniglyph.policy_pack:0.1","policy_id":"company.acme.agent_policy","namespace":"private_acme","name":"ACME Agent Policy","version":"2026.07.05","owner_type":"enterprise","license":"private","visibility":"private"}',
        encoding="utf-8",
    )
    (path / "intents.csv").write_text(
        "intent_id,canonical_phrase,decision,risk_level,requires_approval,allowed_roles,audit_required,parameters_schema\n"
        'network.restart,restart network service,review,high,true,admin,true,"{""type"":""object"",""required"":[""service""],""properties"":{""service"":{""type"":""string"",""enum"":[""network""]}}}"\n',
        encoding="utf-8",
    )


def test_build_tools_list_exposes_lookup_glyph_tool():
    tools = build_tools_list()

    assert tools[0]["name"] == "lookup_glyph"
    assert tools[0]["inputSchema"]["required"] == ["char"]


def test_handle_mcp_tools_list_request():
    response = handle_mcp_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})

    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert response["result"]["tools"][0]["name"] == "lookup_glyph"


def test_handle_mcp_initialize_uses_package_version():
    response = handle_mcp_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"})

    assert __version__ == "0.7.0b0"
    assert response["result"]["serverInfo"]["version"] == __version__


def test_handle_mcp_lookup_glyph_tool_call(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    source_id = repository.add_source_snapshot(SourceSnapshot("Unicode Character Database", "file://fixture", "fixture", "sha", "Unicode Terms of Use", "fixture"))
    repository.insert_glyph_records([
        GlyphRecord(glyph="铝", unicode_hex="U+94DD", basic_definition="CJK UNIFIED IDEOGRAPH-94DD")
    ], source_id=source_id)

    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "lookup_glyph", "arguments": {"char": "铝"}},
        },
        repository=repository,
    )

    assert response["id"] == 2
    content = response["result"]["content"][0]
    assert content["type"] == "text"
    assert json.loads(content["text"])["unicode"]["hex"] == "U+94DD"


def test_handle_mcp_unknown_tool_returns_error(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()

    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "missing", "arguments": {}},
        },
        repository=repository,
    )

    assert response["error"]["code"] == -32601


def test_mcp_tools_list_includes_term_and_normalize_tools():
    names = {tool["name"] for tool in build_tools_list()}

    assert {"lookup_glyph", "lookup_term", "normalize_tokens"}.issubset(names)


def test_mcp_tools_list_includes_explain_tools():
    names = {tool["name"] for tool in build_tools_list()}

    assert {"explain_glyph", "explain_term"}.issubset(names)


def test_mcp_tools_list_includes_security_and_audit_tools():
    names = {tool["name"] for tool in build_tools_list()}

    assert {
        "scan_code_symbols",
        "scan_unicode_security",
        "explain_code_security",
        "audit_explain",
        "enforce_grounded_output",
    }.issubset(names)


def test_mcp_tools_list_includes_lexicon_product_tools():
    names = {tool["name"] for tool in build_tools_list()}

    assert {"list_namespaces", "validate_lexicon_pack"}.issubset(names)


def test_mcp_tools_list_includes_policy_pack_tools():
    names = {tool["name"] for tool in build_tools_list()}

    assert "validate_policy_pack" in names


def test_handle_mcp_lookup_term_tool_call(tmp_path):
    from pathlib import Path

    from omniglyph.domain_pack import parse_domain_pack

    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    source_id = repository.add_source_snapshot(SourceSnapshot("Private Domain Pack", "file://domain", "fixture", "sha-domain", "private", "domain"))
    repository.insert_lexical_entries(list(parse_domain_pack(Path("tests/fixtures/domain_pack.csv"), "private_building_materials")), source_id)

    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "lookup_term", "arguments": {"text": "FOB"}},
        },
        repository=repository,
    )

    assert mcp_json(response)["canonical_id"] == "trade:fob"


def test_handle_mcp_normalize_tokens_tool_call(tmp_path):
    from pathlib import Path

    from omniglyph.domain_pack import parse_domain_pack

    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    glyph_source = repository.add_source_snapshot(SourceSnapshot("Unicode Character Database", "file://fixture", "fixture", "sha-u", "Unicode Terms of Use", "fixture"))
    term_source = repository.add_source_snapshot(SourceSnapshot("Private Domain Pack", "file://domain", "fixture", "sha-d", "private", "domain"))
    repository.insert_glyph_records([GlyphRecord(glyph="铝", unicode_hex="U+94DD", basic_definition="CJK UNIFIED IDEOGRAPH-94DD")], glyph_source)
    repository.insert_lexical_entries(list(parse_domain_pack(Path("tests/fixtures/domain_pack.csv"), "private_building_materials")), term_source)

    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "normalize_tokens", "arguments": {"tokens": ["铝", "FOB", "unknown"], "mode": "compact"}},
        },
        repository=repository,
    )

    assert mcp_json(response) == {"known": {"铝": "glyph:U+94DD", "FOB": "trade:fob"}, "unknown": ["unknown"]}


def test_handle_mcp_validate_output_terms_tool_call(tmp_path):
    from pathlib import Path

    from omniglyph.domain_pack import parse_domain_pack

    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    source_id = repository.add_source_snapshot(SourceSnapshot("Private Domain Pack", "file://domain", "fixture", "sha-domain-guard", "private", "domain"))
    repository.insert_lexical_entries(list(parse_domain_pack(Path("examples/domain-packs/building_materials.csv"), "private_building_materials")), source_id)

    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {"name": "validate_output_terms", "arguments": {"terms": ["FOB", "HS 7604.99X"]}},
        },
        repository=repository,
    )

    payload = mcp_json(response)
    assert payload["status"] == "warn"
    assert payload["unknown"] == ["HS 7604.99X"]


def test_handle_mcp_scan_code_symbols_tool_call():
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {"name": "scan_code_symbols", "arguments": {"text": "v\u0430lue = 1\n", "source_name": "agent.py"}},
        }
    )

    payload = mcp_json(response)
    assert payload["status"] == "warn"
    assert payload["findings"][0]["unicode_hex"] == "U+0430"
    assert payload["findings"][0]["source"] == "agent.py"


def test_handle_mcp_scan_unicode_security_tool_call():
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {"name": "scan_unicode_security", "arguments": {"text": "v\u0430lue = 1\n", "source_name": "agent.py"}},
        }
    )

    payload = mcp_json(response)
    assert payload["status"] == "warn"
    assert payload["findings"][0]["rule_id"] == "unicode-confusable"
    assert payload["findings"][0]["confusable_with"] == "a"


def test_handle_mcp_explain_glyph_tool_call(tmp_path):
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {"name": "explain_glyph", "arguments": {"char": "铝"}},
        },
        repository=seeded_glyph_repository(tmp_path),
    )

    payload = mcp_json(response)
    assert payload["schema"] == "oes:0.1"
    assert payload["canonical_id"] == "glyph:U+94DD"


def test_handle_mcp_explain_term_tool_call(tmp_path):
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "tools/call",
            "params": {"name": "explain_term", "arguments": {"text": "FOB"}},
        },
        repository=seeded_domain_repository(tmp_path),
    )

    payload = mcp_json(response)
    assert payload["schema"] == "oes:0.1"
    assert payload["canonical_id"] == "trade:fob"


def test_handle_mcp_explain_code_security_tool_call():
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {"name": "explain_code_security", "arguments": {"text": "v\u0430lue = 1\n", "source_name": "agent.py"}},
        }
    )

    payload = mcp_json(response)
    assert payload["schema"] == "oes:0.1"
    assert payload["status"] == "unsafe"
    assert payload["safety"]["findings"][0]["source_id"] == "source:unicode-confusables:minimal"


def test_handle_mcp_audit_explain_tool_call(tmp_path):
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "tools/call",
            "params": {"name": "audit_explain", "arguments": {"actor_id": "user:alice", "kind": "term", "text": "FOB"}},
        },
        repository=seeded_domain_repository(tmp_path),
    )

    payload = mcp_json(response)
    assert payload["result"]["canonical_id"] == "trade:fob"
    assert payload["audit"]["actor"] == {"id": "user:alice"}
    assert payload["audit"]["action"] == "explain_term"
    assert payload["audit"]["source_ids"]


def test_handle_mcp_audit_explain_rejects_invalid_glyph_text(tmp_path):
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 13,
            "method": "tools/call",
            "params": {"name": "audit_explain", "arguments": {"actor_id": "user:alice", "kind": "glyph", "text": "ab"}},
        },
        repository=seeded_glyph_repository(tmp_path),
    )

    assert response["error"]["code"] == -32602
    assert "exactly one Unicode character" in response["error"]["message"]


def test_handle_mcp_enforce_grounded_output_tool_call(tmp_path):
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 14,
            "method": "tools/call",
            "params": {
                "name": "enforce_grounded_output",
                "arguments": {"terms": ["FOB", "HS 7604.99X"], "actor_id": "agent:quote"},
            },
        },
        repository=seeded_domain_repository(tmp_path),
    )

    payload = mcp_json(response)
    assert payload["schema"] == "omniglyph.guardrail:0.1"
    assert payload["decision"] == "block"
    assert payload["unknown"] == ["HS 7604.99X"]
    assert payload["audit"]["action"] == "enforce_grounded_output"


def test_handle_mcp_list_namespaces_tool_call(tmp_path):
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 16,
            "method": "tools/call",
            "params": {"name": "list_namespaces", "arguments": {}},
        },
        repository=seeded_domain_repository(tmp_path),
    )

    payload = mcp_json(response)
    assert payload["schema"] == "omniglyph.lexicon_namespaces:0.1"
    assert payload["namespaces"][0]["namespace"] == "private_building_materials"


def test_handle_mcp_validate_lexicon_pack_tool_call(tmp_path):
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 17,
            "method": "tools/call",
            "params": {
                "name": "validate_lexicon_pack",
                "arguments": {"path": "examples/lexicon-packs/company_trade_terms"},
            },
        },
        repository=seeded_domain_repository(tmp_path),
    )

    payload = mcp_json(response)
    assert payload["status"] == "pass"
    assert payload["pack"]["pack_id"] == "company.example.trade_terms"


def test_handle_mcp_validate_lexicon_pack_rejects_paths_outside_configured_root(tmp_path, monkeypatch):
    from omniglyph import mcp_server
    from omniglyph.config import Settings

    pack_root = tmp_path / "packs"
    outside_pack = tmp_path / "outside"
    pack_root.mkdir()
    outside_pack.mkdir()
    monkeypatch.setattr(
        mcp_server,
        "settings",
        Settings(
            data_dir=tmp_path / "data",
            raw_dir=tmp_path / "data" / "raw",
            sqlite_path=tmp_path / "data" / "omniglyph.sqlite3",
            lexicon_pack_root=pack_root,
        ),
    )
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()

    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 21,
            "method": "tools/call",
            "params": {"name": "validate_lexicon_pack", "arguments": {"path": str(outside_pack)}},
        },
        repository=repository,
    )

    assert response["error"]["code"] == -32602
    assert "outside OMNIGLYPH_LEXICON_PACK_ROOT" in response["error"]["message"]


def test_handle_mcp_validate_policy_pack_tool_call(tmp_path):
    pack_dir = tmp_path / "policy"
    write_mcp_policy_pack(pack_dir)
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()

    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 22,
            "method": "tools/call",
            "params": {"name": "validate_policy_pack", "arguments": {"path": str(pack_dir)}},
        },
        repository=repository,
    )

    payload = mcp_json(response)
    assert payload["status"] == "pass"
    assert payload["policy"]["policy_id"] == "company.acme.agent_policy"


def test_handle_mcp_enforce_intent_accepts_policy_pack_path(tmp_path):
    pack_dir = tmp_path / "policy"
    write_mcp_policy_pack(pack_dir)
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()

    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 23,
            "method": "tools/call",
            "params": {
                "name": "enforce_intent",
                "arguments": {
                    "intent_id": "network.restart",
                    "policy_pack_path": str(pack_dir),
                    "actor_role": "admin",
                    "parameters": {"service": "network"},
                },
            },
        },
        repository=repository,
    )

    payload = mcp_json(response)
    assert payload["decision"] == "review"
    assert payload["policy"]["policy_id"] == "company.acme.agent_policy"


def test_handle_mcp_enforce_intent_blocks_invalid_policy_pack_parameters(tmp_path):
    pack_dir = tmp_path / "policy"
    write_mcp_policy_pack(pack_dir)
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()

    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 25,
            "method": "tools/call",
            "params": {
                "name": "enforce_intent",
                "arguments": {
                    "intent_id": "network.restart",
                    "policy_pack_path": str(pack_dir),
                    "actor_role": "admin",
                    "parameters": {"service": 123},
                },
            },
        },
        repository=repository,
    )

    payload = mcp_json(response)
    assert payload["decision"] == "block"
    assert payload["status"] == "invalid_parameters"


def test_handle_mcp_enforce_intent_rejects_ambiguous_policy_sources(tmp_path):
    pack_dir = tmp_path / "policy"
    write_mcp_policy_pack(pack_dir)
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()

    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 24,
            "method": "tools/call",
            "params": {
                "name": "enforce_intent",
                "arguments": {
                    "intent_id": "network.restart",
                    "manifest": {"intents": []},
                    "policy_pack_path": str(pack_dir),
                },
            },
        },
        repository=repository,
    )

    assert response["error"]["code"] == -32602
    assert response["error"]["message"] == "enforce_intent requires exactly one of manifest or policy_pack_path"
