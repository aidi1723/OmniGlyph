# World Protocol Pack v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic World Protocol Pack v0.1 layer that validates protocol packs and checks agent goals, actions, intents, and outputs against source-backed rules.

**Architecture:** Add a focused `omniglyph.protocol_pack` module for parsing, validation, matching, and decision aggregation. Expose the runtime through FastAPI, MCP, and CLI using the same JSON payload shapes, and document the feature as a checked protocol layer rather than a global alignment guarantee.

**Tech Stack:** Python 3.10+, dataclasses, stdlib JSON, FastAPI, existing MCP stdio server, pytest.

---

### Task 1: Protocol Pack Core

**Files:**
- Create: `src/omniglyph/protocol_pack.py`
- Create: `tests/test_protocol_pack.py`
- Create: `examples/protocol-packs/root_starter/protocol.json`

- [ ] **Step 1: Write failing tests for validation and matching**

Add tests that cover a valid pack, missing fields, invalid decisions, `keyword_any`, `keyword_all`, `exact_intent`, and decision aggregation.

- [ ] **Step 2: Run red tests**

Run: `.venv/bin/pytest tests/test_protocol_pack.py -q`

Expected: fail because `omniglyph.protocol_pack` does not exist.

- [ ] **Step 3: Implement core module**

Implement constants, dataclasses, `init_protocol_pack`, `load_protocol_pack`, `validate_protocol_pack`, and `check_protocol`.

- [ ] **Step 4: Run green tests**

Run: `.venv/bin/pytest tests/test_protocol_pack.py -q`

Expected: pass.

### Task 2: API Runtime

**Files:**
- Modify: `src/omniglyph/api.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Write failing API tests**

Add tests for `POST /api/v1/protocol/validate-pack` and `POST /api/v1/protocol/check`.

- [ ] **Step 2: Run red tests**

Run: `.venv/bin/pytest tests/test_api.py -q`

Expected: fail with 404 for new endpoints.

- [ ] **Step 3: Implement endpoints**

Add Pydantic request models and route handlers that call `validate_protocol_pack` and `check_protocol`.

- [ ] **Step 4: Run green tests**

Run: `.venv/bin/pytest tests/test_api.py -q`

Expected: pass.

### Task 3: MCP Runtime

**Files:**
- Modify: `src/omniglyph/mcp_server.py`
- Modify: `tests/test_mcp.py`
- Modify: `scripts/mcp_smoke_test.sh`

- [ ] **Step 1: Write failing MCP tests**

Add tool-list and tool-call tests for `validate_protocol_pack` and `check_protocol`.

- [ ] **Step 2: Run red tests**

Run: `.venv/bin/pytest tests/test_mcp.py -q`

Expected: fail because new MCP tools are absent.

- [ ] **Step 3: Implement MCP tools**

Add schemas to `build_tools_list` and handlers in `handle_mcp_request`.

- [ ] **Step 4: Update MCP smoke test**

Add the two new tools to expected output.

- [ ] **Step 5: Run green tests and smoke**

Run: `.venv/bin/pytest tests/test_mcp.py -q`

Run: `scripts/mcp_smoke_test.sh .venv/bin/omniglyph-mcp`

Expected: pass and list 18 tools.

### Task 4: CLI Runtime

**Files:**
- Modify: `src/omniglyph/cli.py`
- Modify: `tests/test_protocol_pack.py`

- [ ] **Step 1: Write failing CLI tests**

Add subprocess tests for `init-protocol-pack`, `validate-protocol-pack`, and `check-protocol`.

- [ ] **Step 2: Run red tests**

Run: `.venv/bin/pytest tests/test_protocol_pack.py -q`

Expected: fail because CLI commands are absent.

- [ ] **Step 3: Implement CLI commands**

Wire commands to protocol pack helpers and return non-zero status for failed validation or `block` decisions.

- [ ] **Step 4: Run green tests**

Run: `.venv/bin/pytest tests/test_protocol_pack.py -q`

Expected: pass.

### Task 5: Documentation

**Files:**
- Create: `docs/specs/world-protocol-pack-standard.md`
- Create: `docs/architecture/world-protocol-layer.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/api.md`
- Modify: `docs/mcp-tools.md`
- Modify: `docs/product/project-status.md`

- [ ] **Step 1: Document standard and architecture**

Write the protocol pack standard and architecture page using the wording from the approved design spec.

- [ ] **Step 2: Update user-facing docs**

Add concise API, MCP, README, and status entries without claiming global alignment guarantees.

- [ ] **Step 3: Check docs formatting**

Run: `git diff --check`

Expected: no output.

### Task 6: Final Verification and Commit

**Files:**
- All changed files.

- [ ] **Step 1: Run full tests**

Run: `.venv/bin/pytest -q`

Expected: all tests pass.

- [ ] **Step 2: Run MCP smoke test**

Run: `scripts/mcp_smoke_test.sh .venv/bin/omniglyph-mcp`

Expected: all expected MCP tools are present.

- [ ] **Step 3: Build and metadata check**

Run: `.venv/bin/python -m build`

Run: `.venv/bin/python -m twine check dist/omniglyph-0.8.0b0.tar.gz dist/omniglyph-0.8.0b0-py3-none-any.whl`

Expected: build succeeds and twine check passes.

- [ ] **Step 4: Commit**

Run:

```bash
git add .
git commit -m "feat: add world protocol pack runtime"
```
