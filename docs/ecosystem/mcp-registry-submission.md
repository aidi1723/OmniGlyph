# MCP Registry Submission Plan

This document prepares OmniGlyph for submission to the MCP registry / server directory ecosystem.

## Target

Submit OmniGlyph as a local stdio MCP server:

- Repository: `https://github.com/aidi1723/OmniGlyph`
- Server name candidate: `io.github.aidi1723/omniglyph`
- Package candidate: `omniglyph`
- Transport: stdio
- License: Apache-2.0

## Current Registry Facts

Based on current MCP Registry documentation:

- The registry is in preview and may introduce breaking changes.
- PyPI packages use `registryType: "pypi"` in `server.json`.
- PyPI ownership is verified by checking for `mcp-name: io.github.aidi1723/omniglyph` in the package README / long description.
- Published server versions are immutable, so each submission needs a unique version string.

## Current Server Card

Use `docs/mcp-server-card.md` as the human-readable project card.

Use `package-registry/server.json` as the machine-readable draft. The draft follows the current public MCP Registry package metadata shape using `registryType` and schema `2025-12-11`; verify again before final submission because the registry is still in preview.

## Important Pre-Submission Gap

The draft `server.json` assumes a PyPI package named `omniglyph` with version `0.3.1b0`.

Before submitting to the registry, complete one of these:

1. Bump the Python package version to `0.3.1b0` in `pyproject.toml` and `src/omniglyph/__init__.py`.
2. Publish OmniGlyph to PyPI as `omniglyph`.
3. Confirm the PyPI long description contains `mcp-name: io.github.aidi1723/omniglyph`.

Until this is done, treat `package-registry/server.json` as a draft rather than a final registry artifact.

## Validation Checklist

- [ ] `pyproject.toml` version matches the package version used in registry metadata.
- [ ] Package can be installed by a fresh user with `pipx install omniglyph` or equivalent.
- [ ] `omniglyph-mcp` starts without repository-local assumptions.
- [ ] `tools/list` returns all five tools.
- [ ] README links to Claude Desktop, Claude Code, server card, and safety docs.
- [ ] `docs/security/mcp-safety.md` explains read-only boundaries.
- [ ] Release page exists for the submitted version.

## Smoke Test

From a clean local checkout:

```bash
UV_CACHE_DIR=.uv-cache uv venv .venv --python 3.11
UV_CACHE_DIR=.uv-cache uv pip install -e '.[dev]'
printf '{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n' | .venv/bin/omniglyph-mcp
```

Expected tools:

- `lookup_glyph`
- `lookup_term`
- `normalize_tokens`
- `validate_output_terms`
- `scan_code_symbols`

## Suggested PR Title

```text
Add OmniGlyph: local Symbol Ground Truth MCP server
```

## Suggested PR Body

```markdown
## Summary

Adds OmniGlyph, a local-first Symbol Ground Truth MCP server for deterministic Unicode lookup, private/domain term normalization, output guardrail checks, and code-symbol linting.

## Why this is useful

AI agents can hallucinate or miss low-level symbol facts, especially with invisible Unicode controls, homoglyphs, multilingual symbols, or domain-specific terms. OmniGlyph provides a local read-only fact layer so MCP clients can verify symbols before reasoning over them.

## Tools

- `lookup_glyph`
- `lookup_term`
- `normalize_tokens`
- `validate_output_terms`
- `scan_code_symbols`

## Safety

- stdio transport
- local-first
- read-only tools
- no shell execution
- no automatic file edits
- no remote API calls by default
- missing facts remain `unknown` / `null`

## Links

- Repository: https://github.com/aidi1723/OmniGlyph
- Server card: https://github.com/aidi1723/OmniGlyph/blob/main/docs/mcp-server-card.md
- Safety notes: https://github.com/aidi1723/OmniGlyph/blob/main/docs/security/mcp-safety.md
- Claude Desktop guide: https://github.com/aidi1723/OmniGlyph/blob/main/docs/integrations/claude-desktop-mcp.md
- Claude Code guide: https://github.com/aidi1723/OmniGlyph/blob/main/docs/integrations/claude-code-mcp.md
```

## Recommended Submission Flow

1. Verify current registry submission requirements.
2. Publish package or adapt install metadata.
3. Update `package-registry/server.json` to match the exact schema.
4. Fork the registry repository.
5. Add OmniGlyph metadata according to registry layout.
6. Open PR with the suggested title/body above.
7. Respond to maintainer feedback with minimal, focused changes.
