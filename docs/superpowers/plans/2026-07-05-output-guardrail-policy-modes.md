# Output Guardrail Policy Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional policy modes to output guardrail enforcement so unknown, unapproved, and secret terms can be allowed, reviewed, or blocked deterministically.

**Architecture:** Keep `validate_output_terms` as a policy-free reporting function. Extend `enforce_grounded_output` to normalize an optional policy object, classify term details, compute the strongest decision, and expose severity, limits, and policy warnings through Python, API, and MCP.

**Tech Stack:** Python 3.10+, stdlib only, FastAPI/Pydantic, MCP stdio JSON-RPC, pytest.

---

### Task 1: Guardrail Core Policy Modes

**Files:**
- Modify: `src/omniglyph/guardrail.py`
- Modify: `tests/test_guardrail.py`

- [ ] **Step 1: Write failing guardrail tests**

Add tests for:

- default unknown terms still block.
- `unknown_action=review` returns `decision=review`.
- `unknown_action=allow` returns `decision=allow` and `severity=low`.
- unapproved terms respect `unapproved_action`.
- approved secret terms respect `secret_action`.
- invalid policy action falls back to block and returns `policy_warnings`.

- [ ] **Step 2: Run tests and verify failure**

Run: `.venv/bin/python -m pytest tests/test_guardrail.py -q`

Expected: new policy tests fail because `enforce_grounded_output` does not accept `policy`.

- [ ] **Step 3: Implement core policy behavior**

Update `enforce_grounded_output(repository, terms, actor_id=None, policy=None)`.

Add helpers:

- `_normalize_policy(policy)`
- `_action_for_detail(detail, policy)`
- `_strongest_action(actions)`
- `_severity_for(decision, risky_detail_count)`
- `_limit_for(action, detail)`

Keep default policy strict: unknown, unapproved, and secret terms all block.

- [ ] **Step 4: Run guardrail tests**

Run: `.venv/bin/python -m pytest tests/test_guardrail.py -q`

Expected: all guardrail tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/omniglyph/guardrail.py tests/test_guardrail.py
git commit -m "feat: add output guardrail policy modes"
```

### Task 2: API and MCP Policy Wiring

**Files:**
- Modify: `src/omniglyph/api.py`
- Modify: `src/omniglyph/mcp_server.py`
- Modify: `tests/test_api.py`
- Modify: `tests/test_mcp.py`

- [ ] **Step 1: Write failing API/MCP tests**

Add tests that send:

```json
{"unknown_action": "review"}
```

through `/api/v1/guardrail/enforce-output` and MCP `enforce_grounded_output`, expecting `decision=review`.

- [ ] **Step 2: Run focused tests and verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_api.py tests/test_mcp.py -q
```

Expected: new tests fail because API/MCP request schemas do not pass `policy`.

- [ ] **Step 3: Wire policy through API and MCP**

API:

- add `policy: dict | None = None` to `GuardrailEnforceRequest`.
- pass `policy=request.policy` to `enforce_grounded_output`.

MCP:

- add `policy` to tool input schema.
- validate policy is an object when provided.
- pass policy to `enforce_grounded_output`.

- [ ] **Step 4: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_api.py tests/test_mcp.py -q
```

Expected: selected tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/omniglyph/api.py src/omniglyph/mcp_server.py tests/test_api.py tests/test_mcp.py
git commit -m "feat: expose output guardrail policy modes"
```

### Task 3: Documentation, Maintenance Notes, and Release Gate

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/api.md`
- Modify: `docs/mcp-tools.md`
- Modify: `docs/architecture/deterministic-mcp-guardrail.md`
- Modify: `docs/product/v0.8-maintenance-log.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update docs**

Document default strict behavior, optional policy object, allowed actions, severity, and invalid action fallback.

- [ ] **Step 2: Run documentation-sensitive checks**

Run: `.venv/bin/python -m pytest tests/test_examples.py tests/test_package_manifest.py -q`

Expected: pass.

- [ ] **Step 3: Run full release gate**

Run: `scripts/release_check.sh`

Expected: pytest, Ruff, mypy, diff check, MCP smoke, build, Twine check, artifact audit, wheel smoke, and demo all pass.

- [ ] **Step 4: Commit and push**

```bash
git add README.md README.zh-CN.md docs CHANGELOG.md
git commit -m "docs: document output guardrail policy modes"
git push
```
