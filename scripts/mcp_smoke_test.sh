#!/usr/bin/env bash
set -euo pipefail

COMMAND="${1:-omniglyph-mcp}"
PYTHON_BIN="${PYTHON:-python3}"
OUTPUT="$(printf '{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n' | ${COMMAND})"

printf '%s' "${OUTPUT}" | "${PYTHON_BIN}" -c '
import json
import sys

payload = json.load(sys.stdin)
tools = {tool["name"] for tool in payload["result"]["tools"]}
expected = {
    "lookup_glyph",
    "lookup_term",
    "explain_glyph",
    "explain_term",
    "explain_code_security",
    "normalize_tokens",
    "list_namespaces",
    "validate_lexicon_pack",
    "validate_protocol_pack",
    "check_protocol",
    "validate_output_terms",
    "enforce_grounded_output",
    "scan_code_symbols",
    "scan_unicode_security",
    "scan_language_input",
    "scan_output_dlp",
    "enforce_intent",
    "audit_explain",
}
missing = expected - tools
if missing:
    raise SystemExit(f"missing MCP tools: {sorted(missing)}")
print("mcp tools ok:", ", ".join(sorted(tools)))
'
