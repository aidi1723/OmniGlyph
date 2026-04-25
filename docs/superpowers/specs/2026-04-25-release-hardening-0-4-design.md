# OmniGlyph 0.4.0 Release Hardening Design

## Goal

Prepare OmniGlyph for a 0.4.0 beta release by tightening version consistency, reproducible source ingestion, SQLite lookup performance, and Unicode security scanning depth.

## Scope

This release keeps the existing product shape: local SQLite fact base, CLI ingestion, FastAPI endpoints, and stdio MCP tools. It does not add a hosted service, OCR, full semantic graph reasoning, or automatic source-code rewriting.

## Design

Version consistency will move to a single package-level version constant. API and MCP metadata will import that constant, and release-facing docs will be updated to `0.4.0b0`.

Reproducible data handling will add a source manifest model that records URL, version, license, and expected SHA-256. CLI ingestion will support expected SHA-256 validation for local files, and download helpers will validate expected hashes after retrieval.

SQLite performance will add explicit indexes for glyph properties, lexical term lookup, and lexical alias lookup. The schema remains migration-friendly because `CREATE INDEX IF NOT EXISTS` is idempotent.

Unicode security scanning will expand the existing code linter with NFKC normalization-difference findings and fullwidth/halfwidth findings. The scanner will continue to report warnings only and will not mutate files.

## Testing

Tests will be added before implementation for each behavior:

- Version metadata consistency across package, API, and MCP.
- SHA-256 validation success and failure for local and downloaded source artifacts.
- Schema indexes exposed by SQLite `PRAGMA index_list`.
- Code scanner findings for fullwidth characters and NFKC-changing symbols.

## Release Checks

Before publishing, run the full test suite, MCP smoke test, package build, and `twine check`. Public upload requires valid credentials and a final confirmation at execution time.
