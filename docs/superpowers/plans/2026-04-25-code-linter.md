# OmniGlyph Code Linter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a code-symbol scanner that detects invisible Unicode controls, Bidi controls, and cross-script homoglyph risks in source files for CLI and MCP use.

**Architecture:** Add a focused `omniglyph.code_linter` module that scans text/files and returns deterministic JSON-compatible reports. Wire it into the existing argparse CLI as `omniglyph scan-code` and into the MCP stdio server as `scan_code_symbols`. Add poisoned-code examples and bilingual documentation for developer-facing demos.

**Tech Stack:** Python 3.10+, standard-library `unicodedata`, existing argparse CLI, existing MCP JSON-RPC handler, pytest.

---

### Task 1: Core Scanner

**Files:**
- Create: `src/omniglyph/code_linter.py`
- Test: `tests/test_code_linter.py`

- [ ] Write failing tests for zero-width, Bidi, Cyrillic homoglyph, clean code, and file scanning.
- [ ] Run `python -m pytest tests/test_code_linter.py -q` and confirm import failure.
- [ ] Implement `scan_text`, `scan_file`, and JSON-compatible finding dictionaries.
- [ ] Re-run scanner tests and confirm pass.

### Task 2: CLI Integration

**Files:**
- Modify: `src/omniglyph/cli.py`
- Test: `tests/test_cli_scan_code.py`

- [ ] Write failing CLI tests for JSON output and warning exit behavior.
- [ ] Add `omniglyph scan-code PATH --format text|json --fail-on warning`.
- [ ] Re-run CLI tests and confirm pass.

### Task 3: MCP Integration

**Files:**
- Modify: `src/omniglyph/mcp_server.py`
- Test: `tests/test_mcp.py`

- [ ] Add failing MCP test for `scan_code_symbols` with text input.
- [ ] Expose tool schema and handler.
- [ ] Re-run MCP tests and confirm pass.

### Task 4: Demo and Docs

**Files:**
- Create: `examples/poisoned-code/generate_poison.py`
- Create: `docs/use-cases/code-linter.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/mcp-tools.md`

- [ ] Add poisoned-code generator.
- [ ] Add docs showing CLI, MCP, and expected findings.
- [ ] Run full tests and demo smoke.

### Task 5: Release Hygiene

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `RELEASE.md`

- [ ] Add v0.3.0 development notes.
- [ ] Run `git diff --check` and full test suite.
- [ ] Commit and push.
