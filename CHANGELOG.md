# Changelog

## 0.6.0-beta - 2026-04-25

- Add `omniglyph.oes` runtime helpers so OES is a project protocol, not only a document.
- Add Unicode Security Pack metadata for source-backed `unicode-confusable` findings with `confusable_with`, `why_it_matters`, `suggested_action`, and `auto_fixable`.
- Add OES-shaped `explain_code_security` runtime helper, API endpoint, and MCP tool.
- Add `POST /api/v1/security/scan` and MCP `scan_unicode_security` for developer-friendly scan reports.
- Add `examples/domain-packs/software_development.csv` with software and security terminology.
- Add `omniglyph.audit` event builder plus `/api/v1/audit/explain`, `/api/v1/audit/security-scan`, and MCP `audit_explain`.

## 0.5.0-beta - 2026-04-25

- Add OmniGlyph Explanation Standard v0.1 documentation for source-backed glyph, term, concept, and safety explanations.
- Add OES-shaped `explain_glyph` and `explain_term` runtime helpers.
- Add `GET /api/v1/explain/glyph` and `GET /api/v1/explain/term` API endpoints.
- Add MCP `explain_glyph` and `explain_term` tools.

## 0.4.0-beta - 2026-04-25

- Centralize runtime version metadata across package, API health metadata, and MCP initialize metadata.
- Add reproducible source integrity checks with optional expected SHA-256 validation for local and downloaded source artifacts.
- Add CLI `--expected-sha256` options for Unicode, Unihan, and private domain pack ingestion.
- Add SQLite lookup indexes for glyph properties, lexical terms, and lexical aliases.
- Extend code-symbol linting with fullwidth/halfwidth and NFKC normalization-change warnings.
- Refresh release-facing PyPI, MCP Registry, and API documentation for the `0.4.0b0` release candidate.

## 0.2.0-beta - Unreleased

- Add Stage 1 Symbol Fact Base skeleton.
- Add deterministic UnicodeData parsing and explicit ingestion.
- Add Unihan tab-separated property parsing and explicit ingestion.
- Add SQLite `source_snapshot`, `glyph_node`, and append-only `glyph_property` schema.
- Add read-only `/api/v1/glyph` FastAPI endpoint.
- Add agent-friendly `unicode`, `lexical`, `domain_traits`, raw `properties`, and `sources` response fields.
- Add minimal stdio MCP server with `lookup_glyph`, `lookup_term`, and `normalize_tokens` tools.
- Add private domain pack CSV ingestion.
- Add `GET /api/v1/term` and `POST /api/v1/normalize` APIs with compact mode.
- Add Dockerfile, docker-compose, GitHub Actions test workflow, migration SQL, benchmark script, notices, and data-source documentation.
- Add Sandwich Architecture documentation for input normalization and output guardrail workflows.
- Add minimal output guardrail API and MCP tool for deterministic known/unknown term validation.
- Add OmniGlyph Code Linter core scanner, CLI `scan-code`, MCP `scan_code_symbols`, and poisoned-code demo generator.
- Add Claude Desktop/Claude Code MCP readiness docs, MCP server card, and MCP safety notes.
- Add MCP Registry submission plan and draft `package-registry/server.json`.
- Prepare PyPI packaging metadata and publish checklist for MCP Registry submission.
- Publish and verify `omniglyph==0.3.2b0` on TestPyPI and PyPI.
- Publish `io.github.aidi1723/omniglyph` version `0.3.2-beta` to the MCP Registry.
