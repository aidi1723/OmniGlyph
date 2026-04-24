# Changelog

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
