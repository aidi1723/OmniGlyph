# OmniGlyph 0.4.0 Release Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship OmniGlyph 0.4.0 beta hardening for version consistency, reproducible data, SQLite lookup indexes, and deeper Unicode security rules.

**Architecture:** Keep the current Python package layout. Add small focused helpers to existing modules instead of introducing a new framework or service boundary.

**Tech Stack:** Python 3.10+, SQLite, FastAPI, pytest, stdio MCP JSON-RPC, setuptools build.

---

### Task 1: Version Consistency

**Files:**
- Modify: `src/omniglyph/__init__.py`
- Modify: `src/omniglyph/api.py`
- Modify: `src/omniglyph/mcp_server.py`
- Modify: `pyproject.toml`
- Modify: `tests/test_api.py`
- Modify: `tests/test_mcp.py`

- [ ] Write failing tests proving API health and MCP initialize use `omniglyph.__version__`.
- [ ] Run targeted tests and verify they fail before implementation.
- [ ] Update version to `0.4.0b0` and import `__version__` in API/MCP metadata.
- [ ] Run targeted tests and verify they pass.

### Task 2: Reproducible Data Sources

**Files:**
- Modify: `src/omniglyph/sources.py`
- Modify: `src/omniglyph/cli.py`
- Create: `tests/test_sources.py`

- [ ] Write failing tests for expected SHA-256 success and mismatch failure.
- [ ] Run targeted tests and verify they fail before implementation.
- [ ] Add `SourceIntegrityError`, expected hash validation, and CLI `--expected-sha256` options.
- [ ] Run targeted tests and verify they pass.

### Task 3: SQLite Indexes

**Files:**
- Modify: `src/omniglyph/repository.py`
- Modify: `tests/test_repository.py`

- [ ] Write failing tests asserting lookup indexes exist after repository initialization.
- [ ] Run targeted tests and verify they fail before implementation.
- [ ] Add idempotent indexes for glyph properties, lexical entries, and lexical aliases.
- [ ] Run targeted tests and verify they pass.

### Task 4: Unicode Security Rules

**Files:**
- Modify: `src/omniglyph/code_linter.py`
- Modify: `tests/test_code_linter.py`

- [ ] Write failing tests for fullwidth and NFKC normalization-difference findings.
- [ ] Run targeted tests and verify they fail before implementation.
- [ ] Add rule IDs and detection logic while preserving current warnings.
- [ ] Run targeted tests and verify they pass.

### Task 5: Release Documentation and Verification

**Files:**
- Modify: `docs/api.md`
- Modify: `CHANGELOG.md`
- Modify: `RELEASE.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`

- [ ] Update release-facing docs to `0.4.0b0`.
- [ ] Run full pytest suite.
- [ ] Run MCP smoke test.
- [ ] Build package.
- [ ] Run `twine check dist/*`.
- [ ] Inspect git diff and prepare publish commands.
