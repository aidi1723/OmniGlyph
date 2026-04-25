# OES Explain Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first runtime implementation of OmniGlyph Explanation Standard v0.1 for glyph and term explanations.

**Architecture:** Add a focused `omniglyph.explanation` module that shapes existing repository lookup results into OES payloads. Expose the module through additive FastAPI endpoints and MCP tools without changing existing lookup behavior.

**Tech Stack:** Python 3.10+, FastAPI, stdio MCP JSON-RPC, SQLite-backed `GlyphRepository`, pytest.

---

### Task 1: OES Explanation Module

**Files:**
- Create: `src/omniglyph/explanation.py`
- Create: `tests/test_explanation.py`

- [ ] **Step 1: Write failing tests**

```python
def test_explain_glyph_returns_oes_payload(tmp_path):
    repository = seeded_repository(tmp_path)
    payload = explain_glyph(repository, "铝")
    assert payload["schema"] == "oes:0.1"
    assert payload["status"] == "matched"
    assert payload["canonical_id"] == "glyph:U+94DD"
    assert payload["input"] == {"text": "铝", "kind": "glyph", "normalized": "铝"}
    assert payload["basic_facts"]["unicode_hex"] == "U+94DD"
    assert payload["lexical"][0]["definition"] == "aluminum"
    assert payload["safety"] == {"risk_level": "none", "findings": []}
    assert payload["limits"] == []

def test_explain_term_returns_oes_payload(tmp_path):
    repository = seeded_domain_repository(tmp_path)
    payload = explain_term(repository, "FOB")
    assert payload["schema"] == "oes:0.1"
    assert payload["status"] == "matched"
    assert payload["canonical_id"] == "trade:fob"
    assert payload["lexical"][0]["term"] == "FOB"

def test_explain_unknown_values_are_explicit(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    assert explain_glyph(repository, "水")["status"] == "unknown"
    assert explain_term(repository, "missing")["status"] == "unknown"
```

- [ ] **Step 2: Verify red**

Run: `.venv/bin/pytest tests/test_explanation.py -q`

Expected: FAIL because `omniglyph.explanation` does not exist.

- [ ] **Step 3: Implement minimal module**

Create `explain_glyph(repository, char)` and `explain_term(repository, text)` using current repository methods.

- [ ] **Step 4: Verify green**

Run: `.venv/bin/pytest tests/test_explanation.py -q`

Expected: PASS.

### Task 2: HTTP Explain Endpoints

**Files:**
- Modify: `src/omniglyph/api.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Write failing endpoint tests**

```python
def test_explain_glyph_endpoint_returns_oes_payload(tmp_path):
    client = TestClient(create_app(seeded_repository(tmp_path)))
    response = client.get("/api/v1/explain/glyph", params={"char": "铝"})
    assert response.status_code == 200
    assert response.json()["schema"] == "oes:0.1"

def test_explain_term_endpoint_returns_oes_payload(tmp_path):
    client = TestClient(create_app(seeded_domain_repository(tmp_path)))
    response = client.get("/api/v1/explain/term", params={"text": "FOB"})
    assert response.status_code == 200
    assert response.json()["canonical_id"] == "trade:fob"
```

- [ ] **Step 2: Verify red**

Run: `.venv/bin/pytest tests/test_api.py::test_explain_glyph_endpoint_returns_oes_payload tests/test_api.py::test_explain_term_endpoint_returns_oes_payload -q`

Expected: FAIL with 404.

- [ ] **Step 3: Add endpoints**

Add `GET /api/v1/explain/glyph` and `GET /api/v1/explain/term`.

- [ ] **Step 4: Verify green**

Run the same targeted tests.

Expected: PASS.

### Task 3: MCP Explain Tools

**Files:**
- Modify: `src/omniglyph/mcp_server.py`
- Modify: `tests/test_mcp.py`

- [ ] **Step 1: Write failing MCP tests**

```python
def test_mcp_tools_list_includes_explain_tools():
    names = {tool["name"] for tool in build_tools_list()}
    assert {"explain_glyph", "explain_term"}.issubset(names)

def test_handle_mcp_explain_glyph_tool_call(tmp_path):
    repository = seeded_repository(tmp_path)
    response = handle_mcp_request(
        {"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": {"name": "explain_glyph", "arguments": {"char": "铝"}}},
        repository=repository,
    )
    assert response["result"]["content"][0]["json"]["schema"] == "oes:0.1"
```

- [ ] **Step 2: Verify red**

Run: `.venv/bin/pytest tests/test_mcp.py::test_mcp_tools_list_includes_explain_tools tests/test_mcp.py::test_handle_mcp_explain_glyph_tool_call -q`

Expected: FAIL because the tools do not exist.

- [ ] **Step 3: Add MCP tools**

Add `explain_glyph` and `explain_term` to `build_tools_list()` and `handle_mcp_request()`.

- [ ] **Step 4: Verify green and full suite**

Run: `.venv/bin/pytest -q`

Expected: PASS.
