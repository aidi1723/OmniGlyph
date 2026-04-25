# MCP Registry Submission Plan

This document prepares OmniGlyph for submission to the MCP registry / server directory ecosystem.

## Target

Submit OmniGlyph as a local stdio MCP server:

- Repository: `https://github.com/aidi1723/OmniGlyph`
- Server name candidate: `io.github.aidi1723/omniglyph`
- Package: `omniglyph==0.3.2b0`
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

Use `package-registry/server.json` as the machine-readable registry draft. The draft follows the current public MCP Registry package metadata shape using `registryType` and schema `2025-12-11`; verify again before final submission because the registry is still in preview.

## PyPI Publication Status

OmniGlyph `0.3.2b0` is published and verified:

- PyPI: `https://pypi.org/project/omniglyph/0.3.2b0/`
- TestPyPI: `https://test.pypi.org/project/omniglyph/0.3.2b0/`
- Clean PyPI install verified with `pip install omniglyph==0.3.2b0`.
- Installed `omniglyph-mcp` returned all five MCP tools via `tools/list`.

## Validation Checklist

- [x] `pyproject.toml` version matches the package version used in registry metadata.
- [x] Package can be installed by a fresh user with `pip install omniglyph==0.3.2b0`.
- [x] `omniglyph-mcp` starts without repository-local assumptions.
- [x] `tools/list` returns all five tools.
- [x] README links to Claude Desktop, Claude Code, server card, and safety docs.
- [x] `docs/security/mcp-safety.md` explains read-only boundaries.
- [x] Release page exists for the submitted version.

## Smoke Test

From a clean environment:

```bash
python3 -m venv /tmp/omniglyph-pypi-install
/tmp/omniglyph-pypi-install/bin/pip install omniglyph==0.3.2b0
printf '{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n' | /tmp/omniglyph-pypi-install/bin/omniglyph-mcp
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

## Verification

- Published on PyPI: https://pypi.org/project/omniglyph/0.3.2b0/
- Clean install verified with `pip install omniglyph==0.3.2b0`
- `omniglyph-mcp` `tools/list` returns all five tools

## Links

- Repository: https://github.com/aidi1723/OmniGlyph
- Server card: https://github.com/aidi1723/OmniGlyph/blob/main/docs/mcp-server-card.md
- Safety notes: https://github.com/aidi1723/OmniGlyph/blob/main/docs/security/mcp-safety.md
- Claude Desktop guide: https://github.com/aidi1723/OmniGlyph/blob/main/docs/integrations/claude-desktop-mcp.md
- Claude Code guide: https://github.com/aidi1723/OmniGlyph/blob/main/docs/integrations/claude-code-mcp.md
```

## Recommended Submission Flow

1. Verify current registry submission requirements.
2. Update `package-registry/server.json` if schema requirements changed.
3. Fork the registry repository.
4. Add OmniGlyph metadata according to registry layout.
5. Open PR with the suggested title/body above.
6. Respond to maintainer feedback with minimal, focused changes.
