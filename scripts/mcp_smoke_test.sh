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
    "validate_output_terms",
    "scan_code_symbols",
    "scan_unicode_security",
    "audit_explain",
}
missing = expected - tools
if missing:
    raise SystemExit(f"missing MCP tools: {sorted(missing)}")
print("mcp tools ok:", ", ".join(sorted(tools)))
'
