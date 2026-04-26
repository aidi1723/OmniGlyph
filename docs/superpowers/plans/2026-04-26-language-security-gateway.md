# Language Security Gateway Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal Language Security Gateway branch capability for prompt-injection scanning, output DLP redaction, and intent sandbox allow/block decisions.

**Architecture:** Keep OmniGlyph's language and symbol foundation as the core. Add one focused runtime module, `omniglyph.language_security`, that returns deterministic security evidence but never executes commands. Expose the module through FastAPI and MCP so AgentCore-style hosts can enforce boundaries before input, before output, and before tool execution.

**Tech Stack:** Python 3.10+, FastAPI, stdio MCP JSON-RPC, pytest.

---

### Task 1: Prompt Injection Security Pack

**Files:**
- Create: `tests/test_language_security.py`
- Create: `src/omniglyph/language_security.py`
- Modify: `src/omniglyph/api.py`
- Modify: `src/omniglyph/mcp_server.py`

- [x] Write tests for `scan_language_input()` detecting hidden Unicode controls and prompt-injection directives.
- [x] Verify the tests fail because `omniglyph.language_security` does not exist.
- [x] Implement `scan_language_input()` with deterministic findings and an `allow` / `block` decision.
- [x] Add API endpoint `POST /api/v1/language-security/scan-input`.
- [x] Add MCP tool `scan_language_input`.
- [x] Verify targeted tests pass.

### Task 2: Output DLP Pack

**Files:**
- Modify: `tests/test_language_security.py`
- Modify: `src/omniglyph/language_security.py`
- Modify: `src/omniglyph/api.py`
- Modify: `src/omniglyph/mcp_server.py`

- [x] Write tests for `scan_output_dlp()` redacting API keys and caller-provided secret terms.
- [x] Verify the tests fail because `scan_output_dlp()` is absent.
- [x] Implement deterministic DLP findings and `[REDACTED]` output.
- [x] Add API endpoint `POST /api/v1/language-security/scan-output`.
- [x] Add MCP tool `scan_output_dlp`.
- [x] Verify targeted tests pass.

### Task 3: Intent Sandbox Manifest

**Files:**
- Modify: `tests/test_language_security.py`
- Modify: `src/omniglyph/language_security.py`
- Modify: `src/omniglyph/api.py`
- Modify: `src/omniglyph/mcp_server.py`
- Add: `examples/security-policies/intent_manifest.json`

- [x] Write tests for `enforce_intent_manifest()` allowing known low-risk intents and blocking unknown or role-disallowed intents.
- [x] Verify the tests fail because `enforce_intent_manifest()` is absent.
- [x] Implement a manifest-only decision function that never executes commands.
- [x] Add API endpoint `POST /api/v1/language-security/enforce-intent`.
- [x] Add MCP tool `enforce_intent`.
- [x] Verify targeted tests pass.

### Task 4: Documentation and Verification

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/api.md`
- Modify: `docs/mcp-tools.md`
- Modify: `docs/security/mcp-safety.md`
- Add: `docs/architecture/language-security-gateway.md`
- Modify: `scripts/mcp_smoke_test.sh`

- [x] Document Language Security Gateway as a branch capability, not a replacement for the core symbol foundation.
- [x] Document all three new API surfaces and MCP tools.
- [x] Update safety notes to state that OmniGlyph does not execute shell commands or route tasks.
- [x] Run `.venv/bin/pytest -q`.
- [x] Run `scripts/mcp_smoke_test.sh .venv/bin/omniglyph-mcp`.
- [x] Run `git diff --check`.
