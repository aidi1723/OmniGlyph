# v0.6 Security Dictionary Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn OES into a reusable runtime protocol while adding developer-friendly Unicode security findings, a software-development domain pack, and structured audit events.

**Architecture:** Keep the slice local-first and source-backed. `omniglyph.oes` owns shared protocol constants and payload helpers, `omniglyph.security_pack` owns Unicode security rule metadata, `omniglyph.audit` turns OES/scan outputs into enterprise audit events, and API/MCP expose the new capabilities additively.

**Tech Stack:** Python 3.10+, SQLite-backed repository, FastAPI, stdio MCP server, pytest, CSV domain packs.

---

### Task 1: OES Core Helpers

**Files:**
- Create: `src/omniglyph/oes.py`
- Modify: `src/omniglyph/explanation.py`
- Test: `tests/test_oes.py`, `tests/test_explanation.py`

- [ ] **Step 1: Write failing tests** for stable OES constants, unknown payload shaping, and source payload shaping.
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_oes.py tests/test_explanation.py -q` and verify the new tests fail because `omniglyph.oes` does not exist.
- [ ] **Step 3: Implement** minimal helpers and migrate existing explanation code to use them.
- [ ] **Step 4: Re-run** `.venv/bin/pytest tests/test_oes.py tests/test_explanation.py -q` and verify the tests pass.

### Task 2: Unicode Security Pack

**Files:**
- Create: `src/omniglyph/security_pack.py`
- Modify: `src/omniglyph/code_linter.py`, `src/omniglyph/explanation.py`
- Test: `tests/test_code_linter.py`, `tests/test_explanation.py`

- [ ] **Step 1: Write failing tests** for source-backed `unicode-confusable` findings, `confusable_with`, `suggested_action`, `auto_fixable`, `source_id`, rule counts, and OES code-security explanations.
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_code_linter.py tests/test_explanation.py -q` and verify the new tests fail on missing fields/functions.
- [ ] **Step 3: Implement** the minimal confusable mapping and OES security wrapper.
- [ ] **Step 4: Re-run** `.venv/bin/pytest tests/test_code_linter.py tests/test_explanation.py -q` and verify the tests pass.

### Task 3: Software Development Domain Pack

**Files:**
- Create: `examples/domain-packs/software_development.csv`
- Modify: `tests/test_domain_pack.py`, `tests/test_explanation.py`

- [ ] **Step 1: Write failing tests** that parse the software-development pack and explain a term such as `API`.
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_domain_pack.py tests/test_explanation.py -q` and verify failure because the pack is absent.
- [ ] **Step 3: Add** the CSV with stable canonical IDs, aliases, definitions, and traits.
- [ ] **Step 4: Re-run** `.venv/bin/pytest tests/test_domain_pack.py tests/test_explanation.py -q` and verify the tests pass.

### Task 4: Audit Workflow

**Files:**
- Create: `src/omniglyph/audit.py`
- Modify: `src/omniglyph/api.py`, `src/omniglyph/mcp_server.py`, `scripts/mcp_smoke_test.sh`
- Test: `tests/test_audit.py`, `tests/test_api.py`, `tests/test_mcp.py`

- [ ] **Step 1: Write failing tests** for audit events that expose actor, action, input, status, canonical ID, source IDs, findings, and unknown limits.
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_audit.py tests/test_api.py tests/test_mcp.py -q` and verify failure because audit modules/tools are absent.
- [ ] **Step 3: Implement** structured audit event builders plus additive API/MCP endpoints.
- [ ] **Step 4: Re-run** `.venv/bin/pytest tests/test_audit.py tests/test_api.py tests/test_mcp.py -q` and verify the tests pass.

### Task 5: Docs, Version, Verification

**Files:**
- Modify: `pyproject.toml`, `src/omniglyph/__init__.py`, `docs/specs/omniglyph-explanation-standard.md`, `docs/use-cases/code-linter.md`, `docs/api.md`, `docs/mcp-tools.md`, `ROADMAP.md`

- [ ] **Step 1: Update docs** to describe OES as the core protocol, Unicode Security Pack fields, software-development pack, and audit workflow.
- [ ] **Step 2: Bump version** to `0.6.0b0`.
- [ ] **Step 3: Run** `.venv/bin/pytest -q`.
- [ ] **Step 4: Run** `scripts/mcp_smoke_test.sh .venv/bin/omniglyph-mcp`.
- [ ] **Step 5: Run** `.venv/bin/python -m build` and `.venv/bin/python -m twine check dist/*` if release artifacts are needed.
