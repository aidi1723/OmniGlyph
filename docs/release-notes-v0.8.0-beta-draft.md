# OmniGlyph v0.8.0 Beta Draft Release Notes

Current source version: `0.8.0b0`.

v0.8.0 beta introduces World Protocol Pack v0.1, the first implementation slice of OmniGlyph's "world dictionary" direction. It turns protocol rules into versioned, source-backed, deterministic checks that Agent hosts can call before allowing goals, actions, intents, or outputs to proceed.

## Added

- `src/omniglyph/protocol_pack.py` for protocol pack validation, loading, matching, and decision aggregation.
- `examples/protocol-packs/root_starter/protocol.json` as a starter root protocol example.
- CLI commands:
  - `omniglyph init-protocol-pack`
  - `omniglyph validate-protocol-pack`
  - `omniglyph check-protocol`
- API endpoints:
  - `POST /api/v1/protocol/validate-pack`
  - `POST /api/v1/protocol/check`
- MCP tools:
  - `validate_protocol_pack`
  - `check_protocol`
- Documentation:
  - `docs/specs/world-protocol-pack-standard.md`
  - `docs/architecture/world-protocol-layer.md`

## Runtime Behavior

`check_protocol` returns:

- `block` when any matched rule blocks.
- `warn` when a matched rule warns and no rule blocks.
- `allow` when matched rules only allow.
- `unknown` when no configured rule matches.

`unknown` is not a permission grant. Host runtimes remain responsible for review, fallback, tool permissions, and final execution policy.

## MCP Tool Count

The current source MCP server exposes 18 tools:

- `lookup_glyph`
- `lookup_term`
- `explain_glyph`
- `explain_term`
- `explain_code_security`
- `normalize_tokens`
- `list_namespaces`
- `validate_lexicon_pack`
- `validate_protocol_pack`
- `check_protocol`
- `validate_output_terms`
- `enforce_grounded_output`
- `scan_code_symbols`
- `scan_unicode_security`
- `scan_language_input`
- `scan_output_dlp`
- `enforce_intent`
- `audit_explain`

## Boundary

World Protocol Pack v0.1 is not a global ethics authority and does not prove complete Agent alignment. It is a deterministic protocol-check layer for configured rules with explicit source and limit evidence.
