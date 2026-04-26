# OmniGlyph v0.6.0-beta Release Notes

OmniGlyph `v0.6.0-beta` turns the project from a local Unicode lookup utility into a clearer agent-facing protocol layer for explanation, Unicode security review, domain terminology, and auditability.

This release is published on PyPI as `omniglyph==0.6.0b0`.

## Highlights

### 1. OES becomes a runtime protocol

OmniGlyph Explanation Standard is no longer only a written spec. It now has shared runtime helpers in `omniglyph.oes`, and explanation payloads follow a stable contract with:

- `schema`
- `input`
- `status`
- `canonical_id`
- `basic_facts`
- `lexical`
- `concept_links`
- `safety`
- `sources`
- `limits`

This makes OmniGlyph easier to compose inside Agent pipelines, MCP tools, and enterprise review workflows.

### 2. Unicode Security Pack

The code-symbol scanner now returns developer-friendly security findings instead of only raw suspicious-character hits.

New finding fields include:

- `confusable_with`
- `why_it_matters`
- `suggested_action`
- `auto_fixable`
- `source_id`

The initial bundled rules cover:

- Unicode confusables
- Bidi controls
- invisible format characters
- control characters
- fullwidth and halfwidth forms
- NFKC normalization changes

Two usage layers are now available:

- `scan_unicode_security`: direct review-oriented scan output
- `explain_code_security`: OES-shaped explanation output

### 3. Vertical Domain Pack for software development

This release adds a starter software-development terminology pack, available both as an example CSV and as a packaged wheel resource.

Included terms cover concepts such as:

- `API`
- `SDK`
- `CLI`
- `CI`
- `CD`
- `MCP`
- `RAG`
- `SQL injection`
- `XSS`
- `Unicode confusable`
- `Trojan Source`

This is the first concrete step toward domain packs that are useful to coding agents and enterprise internal tooling.

### 4. Audit workflow

OmniGlyph now emits structured audit events that answer four practical questions:

- who queried
- what was checked
- which source IDs supported the result
- what remained unknown

New audit output is available through:

- `POST /api/v1/audit/explain`
- `POST /api/v1/audit/security-scan`
- MCP `audit_explain`

This makes the project much closer to a reviewable enterprise component instead of a standalone lookup helper.

## API and MCP additions

### API

Added:

- `POST /api/v1/explain/code-security`
- `POST /api/v1/security/scan`
- `POST /api/v1/audit/explain`
- `POST /api/v1/audit/security-scan`

### MCP

OmniGlyph MCP now exposes 10 tools:

- `lookup_glyph`
- `lookup_term`
- `explain_glyph`
- `explain_term`
- `explain_code_security`
- `normalize_tokens`
- `validate_output_terms`
- `scan_code_symbols`
- `scan_unicode_security`
- `audit_explain`

## Verification

Verified in this release:

- local test suite: `85 passed`
- MCP smoke test: all 10 tools available
- package build: passed
- `twine check`: passed for wheel and sdist
- clean install from PyPI: passed
- packaged software-development domain pack loads correctly from installed wheel

## Install

```bash
pip install omniglyph==0.6.0b0
```

## Notes

This is still a beta release. The project is now much stronger in protocol consistency, Unicode safety review, domain terminology, and auditability, but it is not yet a fully mature enterprise platform or a complete semantic computation engine.

The next likely frontier is expanding domain packs, broadening security-source coverage, and moving from “auditable lookup” toward richer policy and review workflows.
