# Policy Pack Parameter Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate intent `parameters` against the Policy Pack `parameters_schema` subset and block invalid tool-action requests deterministically.

**Architecture:** Add `src/omniglyph/parameter_schema.py` as a dependency-free validator that returns structured findings. Wire it into `enforce_intent_manifest` after intent and role checks, so Python, CLI, API, and MCP share the same behavior through existing parameters.

**Tech Stack:** Python 3.10+, stdlib only, pytest, existing FastAPI/MCP/CLI surfaces.

---

### Task 1: Parameter Schema Validator

**Files:**
- Create: `src/omniglyph/parameter_schema.py`
- Create: `tests/test_parameter_schema.py`

- [ ] **Step 1: Write failing validator tests**

Create `tests/test_parameter_schema.py` with tests for valid object parameters, missing required fields, enum and length failures, numeric bounds, array item validation, and ignored unknown keywords.

- [ ] **Step 2: Run tests and verify module-missing failure**

Run: `.venv/bin/python -m pytest tests/test_parameter_schema.py -q`

Expected: collection fails with `ModuleNotFoundError: No module named 'omniglyph.parameter_schema'`.

- [ ] **Step 3: Implement validator**

Create `validate_parameters(parameters: object, schema: dict[str, object]) -> list[dict[str, str]]`.

Support:

- `type`
- `required`
- `properties`
- `enum`
- `minLength`
- `maxLength`
- `minimum`
- `maximum`
- `items`

Return findings with `path`, `rule`, and `message`.

- [ ] **Step 4: Run validator tests**

Run: `.venv/bin/python -m pytest tests/test_parameter_schema.py -q`

Expected: all validator tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/omniglyph/parameter_schema.py tests/test_parameter_schema.py
git commit -m "feat: add lightweight parameter schema validator"
```

### Task 2: Intent Enforcement Integration

**Files:**
- Modify: `src/omniglyph/language_security.py`
- Modify: `tests/test_language_security.py`
- Modify: `tests/test_policy_pack.py`
- Modify: `tests/test_api.py`
- Modify: `tests/test_mcp.py`

- [ ] **Step 1: Write failing runtime tests**

Add tests that invalid `parameters` return:

```json
{
  "decision": "block",
  "status": "invalid_parameters",
  "limits": ["Intent parameters do not match parameters_schema."]
}
```

Cover Python runtime, CLI, API, and MCP. Also add one positive runtime test for valid parameters and one compatibility test for manifests without `parameters_schema`.

- [ ] **Step 2: Run focused tests and verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_language_security.py tests/test_policy_pack.py tests/test_api.py tests/test_mcp.py -q
```

Expected: new invalid-parameter tests fail because enforcement does not call the validator yet.

- [ ] **Step 3: Wire validator into `enforce_intent_manifest`**

Import `validate_parameters`. After explicit block and role checks, call the validator when `parameters_schema` is a non-empty dict. On findings, return `decision=block`, `status=invalid_parameters`, the standard limit, and `parameter_findings`.

- [ ] **Step 4: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_language_security.py tests/test_policy_pack.py tests/test_api.py tests/test_mcp.py -q
```

Expected: selected tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/omniglyph/language_security.py tests/test_language_security.py tests/test_policy_pack.py tests/test_api.py tests/test_mcp.py
git commit -m "feat: enforce intent parameter schemas"
```

### Task 3: Documentation and Release Verification

**Files:**
- Modify: `docs/specs/policy-pack-standard.md`
- Modify: `docs/mcp-tools.md`
- Modify: `docs/api.md`
- Modify: `docs/product/v0.8-maintenance-log.md`
- Modify: `CHANGELOG.md`
- Modify: `examples/policy-packs/agent_intents/intents.csv`

- [ ] **Step 1: Update docs and example schema**

Document the supported `parameters_schema` subset, invalid-parameter result shape, and non-goals. Update the example Policy Pack so `network.restart` has a useful `service` schema.

- [ ] **Step 2: Run focused docs/example tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_examples.py tests/test_policy_pack.py -q
```

Expected: examples and Policy Pack tests pass.

- [ ] **Step 3: Run full release gate**

Run: `scripts/release_check.sh`

Expected: pytest, Ruff, mypy, diff check, MCP smoke, build, Twine check, artifact audit, wheel smoke, and demo all pass.

- [ ] **Step 4: Commit and push**

```bash
git add docs examples CHANGELOG.md
git commit -m "docs: document policy pack parameter guard"
git push
```
