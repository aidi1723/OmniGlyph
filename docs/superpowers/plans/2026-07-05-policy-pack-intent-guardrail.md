# Policy Pack Intent Guardrail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local-first Policy Pack format for deterministic intent enforcement across Python, CLI, API, and MCP while preserving inline manifest compatibility.

**Architecture:** Implement `src/omniglyph/policy_pack.py` as the single source for Policy Pack init, validation, loading, manifest conversion, and path restrictions. Reuse the existing `enforce_intent_manifest` runtime so API, MCP, and CLI share one deterministic decision path.

**Tech Stack:** Python 3.10+, stdlib `csv/json/dataclasses/pathlib`, FastAPI/Pydantic, pytest, existing OmniGlyph release gate.

**Execution workspace:** The repository is already on feature branch `docs/logosgate-belief-whitepaper`. No `.worktrees/` or `worktrees/` convention exists, so implementation continues on this feature branch.

---

### Task 1: Policy Pack Core

**Files:**
- Create: `src/omniglyph/policy_pack.py`
- Test: `tests/test_policy_pack.py`

- [ ] **Step 1: Write failing tests for validation, loading, init, and path restriction**

Add tests that define the public API before implementation:

```python
from pathlib import Path

import pytest

from omniglyph.policy_pack import (
    ensure_allowed_policy_pack_path,
    init_policy_pack,
    load_policy_pack,
    validate_policy_pack,
)


def write_policy_pack(path: Path) -> None:
    path.mkdir()
    (path / "policy.json").write_text(
        '{"schema":"omniglyph.policy_pack:0.1","policy_id":"company.acme.agent_policy","namespace":"private_acme","name":"ACME Agent Policy","version":"2026.07.05","owner_type":"enterprise","license":"private","visibility":"private"}',
        encoding="utf-8",
    )
    (path / "intents.csv").write_text(
        "intent_id,canonical_phrase,decision,risk_level,requires_approval,allowed_roles,audit_required,parameters_schema\n"
        'network.restart,restart network service,review,high,true,admin,true,"{""type"":""object""}"\n'
        'ticket.create,create support ticket,allow,low,false,admin;operator,true,"{}"\n'
        'system.delete_root,delete root filesystem,block,critical,false,,true,"{}"\n',
        encoding="utf-8",
    )


def test_validate_policy_pack_accepts_pack_directory(tmp_path):
    pack_dir = tmp_path / "policy"
    write_policy_pack(pack_dir)

    report = validate_policy_pack(pack_dir)

    assert report["status"] == "pass"
    assert report["policy"]["policy_id"] == "company.acme.agent_policy"
    assert report["summary"] == {"intent_count": 3, "allow_count": 1, "review_count": 1, "block_count": 1}
    assert report["errors"] == []


def test_load_policy_pack_converts_rows_to_manifest(tmp_path):
    pack_dir = tmp_path / "policy"
    write_policy_pack(pack_dir)

    pack = load_policy_pack(pack_dir)
    manifest = pack.to_manifest()

    assert manifest["policy"]["policy_id"] == "company.acme.agent_policy"
    assert manifest["policy"]["namespace"] == "private_acme"
    assert manifest["intents"][0]["intent_id"] == "network.restart"
    assert manifest["intents"][0]["allowed_roles"] == ["admin"]
    assert manifest["intents"][0]["parameters_schema"] == {"type": "object"}


def test_validate_policy_pack_reports_invalid_rows(tmp_path):
    pack_dir = tmp_path / "bad-policy"
    pack_dir.mkdir()
    (pack_dir / "policy.json").write_text(
        '{"schema":"omniglyph.policy_pack:0.1","policy_id":"bad","namespace":"public_bad","name":"Bad","version":"1","owner_type":"personal","license":"private","visibility":"private"}',
        encoding="utf-8",
    )
    (pack_dir / "intents.csv").write_text(
        "intent_id,canonical_phrase,decision,risk_level,requires_approval,allowed_roles,audit_required,parameters_schema\n"
        "bad.intent,Bad,sometimes,severe,maybe,admin,true,[]\n",
        encoding="utf-8",
    )

    report = validate_policy_pack(pack_dir)

    assert report["status"] == "fail"
    assert "policy.json: namespace should start with private_ for user policy packs" in report["errors"]
    assert "intents.csv row 2: decision must be one of allow, block, review" in report["errors"]
    assert "intents.csv row 2: risk_level must be one of critical, high, low, medium" in report["errors"]
    assert "intents.csv row 2: requires_approval must be a boolean string" in report["errors"]
    assert "intents.csv row 2: parameters_schema must be a JSON object" in report["errors"]


def test_init_policy_pack_creates_valid_template(tmp_path):
    target = tmp_path / "starter"

    init_policy_pack(target, namespace="private_starter", policy_id="personal.starter", name="Starter Policy")

    assert (target / "policy.json").exists()
    assert (target / "intents.csv").exists()
    assert validate_policy_pack(target)["status"] == "pass"


def test_ensure_allowed_policy_pack_path_blocks_outside_root(tmp_path):
    root = tmp_path / "allowed"
    inside = root / "policy"
    outside = tmp_path / "outside"
    inside.mkdir(parents=True)
    outside.mkdir()

    ensure_allowed_policy_pack_path(str(inside), root)
    with pytest.raises(ValueError, match="outside OMNIGLYPH_POLICY_PACK_ROOT"):
        ensure_allowed_policy_pack_path(str(outside), root)
```

- [ ] **Step 2: Run tests and verify they fail because the module is missing**

Run: `pytest tests/test_policy_pack.py -q`

Expected: collection fails with `ModuleNotFoundError: No module named 'omniglyph.policy_pack'`.

- [ ] **Step 3: Implement `policy_pack.py`**

Implement:

```python
POLICY_PACK_SCHEMA = "omniglyph.policy_pack:0.1"
POLICY_FILENAME = "policy.json"
INTENTS_FILENAME = "intents.csv"
ALLOWED_DECISIONS = {"allow", "review", "block"}
ALLOWED_RISK_LEVELS = {"low", "medium", "high", "critical"}
```

Create a frozen `PolicyPack` dataclass with `metadata`, `intents`, and `to_manifest()`.

Implement these public functions:

```python
def init_policy_pack(path: Path | str, namespace: str, policy_id: str, name: str) -> None: ...
def load_policy_pack(path: Path | str) -> PolicyPack: ...
def validate_policy_pack(path: Path | str) -> dict: ...
def ensure_allowed_policy_pack_path(path: str, root: Path | None) -> None: ...
```

Parse `allowed_roles` as semicolon-separated strings, booleans from `true/false/yes/no/1/0`, and `parameters_schema` as a JSON object.

- [ ] **Step 4: Run core tests and verify green**

Run: `pytest tests/test_policy_pack.py -q`

Expected: all tests in `tests/test_policy_pack.py` pass.

- [ ] **Step 5: Commit**

```bash
git add src/omniglyph/policy_pack.py tests/test_policy_pack.py
git commit -m "feat: add policy pack core"
```

### Task 2: Intent Enforcement Compatibility

**Files:**
- Modify: `src/omniglyph/language_security.py`
- Modify: `tests/test_language_security.py`

- [ ] **Step 1: Write failing tests for explicit decisions and policy metadata**

Add tests:

```python
def test_enforce_intent_manifest_blocks_explicit_block_decision():
    manifest = {
        "intents": [
            {
                "intent_id": "system.delete_root",
                "decision": "block",
                "allowed_roles": ["admin"],
                "requires_approval": False,
            }
        ]
    }

    result = enforce_intent_manifest("system.delete_root", manifest, actor_role="admin")

    assert result["decision"] == "block"
    assert result["status"] == "matched"
    assert result["limits"] == ["Intent policy blocks this request."]


def test_enforce_intent_manifest_includes_policy_metadata_when_present():
    manifest = {
        "policy": {"policy_id": "company.acme.agent_policy", "namespace": "private_acme", "version": "2026.07.05"},
        "intents": [{"intent_id": "ticket.create", "decision": "allow", "allowed_roles": ["operator"]}],
    }

    result = enforce_intent_manifest("ticket.create", manifest, actor_role="operator")

    assert result["decision"] == "allow"
    assert result["policy"]["policy_id"] == "company.acme.agent_policy"
```

- [ ] **Step 2: Run focused tests and verify new tests fail**

Run: `pytest tests/test_language_security.py::test_enforce_intent_manifest_blocks_explicit_block_decision tests/test_language_security.py::test_enforce_intent_manifest_includes_policy_metadata_when_present -q`

Expected: tests fail because explicit `decision=block` and `policy` passthrough are not implemented.

- [ ] **Step 3: Update `enforce_intent_manifest` minimally**

Add explicit block precedence and pass manifest policy metadata into `_intent_result`.

- [ ] **Step 4: Run language security tests**

Run: `pytest tests/test_language_security.py -q`

Expected: all language-security tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/omniglyph/language_security.py tests/test_language_security.py
git commit -m "feat: support policy metadata in intent enforcement"
```

### Task 3: CLI Integration

**Files:**
- Modify: `src/omniglyph/cli.py`
- Modify: `tests/test_policy_pack.py`

- [ ] **Step 1: Write failing CLI tests**

Add subprocess tests for:

```python
def test_cli_init_validate_and_enforce_policy_pack(tmp_path):
    target = tmp_path / "cli-policy"
    init_result = subprocess.run([... "init-policy-pack", str(target), "--namespace", "private_cli", "--policy-id", "personal.cli", "--name", "CLI Policy"], check=False, capture_output=True, text=True)
    validate_result = subprocess.run([... "validate-policy-pack", str(target)], check=False, capture_output=True, text=True)
    enforce_result = subprocess.run([... "enforce-intent", "example.review", "--policy-pack", str(target), "--actor-role", "admin", "--parameters", "{\"ticket\":\"123\"}"], check=False, capture_output=True, text=True)
```

Assert all return code `0`, validation prints `"status": "pass"`, and enforcement prints a JSON decision of `review`.

- [ ] **Step 2: Run CLI test and verify it fails because commands are missing**

Run: `pytest tests/test_policy_pack.py::test_cli_init_validate_and_enforce_policy_pack -q`

Expected: fail with argparse invalid choice for `init-policy-pack`.

- [ ] **Step 3: Add CLI commands**

Import Policy Pack helpers, add parsers for:

- `init-policy-pack`
- `validate-policy-pack`
- `enforce-intent`

Parse `--parameters` with `json.loads`; invalid JSON should print an argparse parser error.

- [ ] **Step 4: Run Policy Pack tests**

Run: `pytest tests/test_policy_pack.py -q`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/omniglyph/cli.py tests/test_policy_pack.py
git commit -m "feat: add policy pack CLI commands"
```

### Task 4: API and Config Integration

**Files:**
- Modify: `src/omniglyph/config.py`
- Modify: `src/omniglyph/api.py`
- Modify: `tests/test_config.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Write failing tests**

Add tests for:

- `OMNIGLYPH_POLICY_PACK_ROOT` loading into settings.
- `POST /api/v1/policy/validate-pack` returns `pass`.
- `POST /api/v1/language-security/enforce-intent` with `policy_pack_path` returns `review`.
- Supplying both `manifest` and `policy_pack_path` returns `400`.

- [ ] **Step 2: Run focused tests and verify failure**

Run: `pytest tests/test_config.py tests/test_api.py -q`

Expected: new tests fail because setting and endpoints are missing.

- [ ] **Step 3: Implement settings and API wiring**

Add `policy_pack_root: Path | None` to `Settings` and read `OMNIGLYPH_POLICY_PACK_ROOT`.

In API:

- import `ensure_allowed_policy_pack_path`, `load_policy_pack`, `validate_policy_pack`.
- add `PolicyValidatePackRequest`.
- extend `IntentEnforceRequest` with optional `manifest` and `policy_pack_path`.
- reject both or neither policy source.
- enforce policy root checks for API pack operations.

- [ ] **Step 4: Run API/config tests**

Run: `pytest tests/test_config.py tests/test_api.py -q`

Expected: all selected tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/omniglyph/config.py src/omniglyph/api.py tests/test_config.py tests/test_api.py
git commit -m "feat: expose policy packs in API"
```

### Task 5: MCP Integration

**Files:**
- Modify: `src/omniglyph/mcp_server.py`
- Modify: `tests/test_mcp.py`

- [ ] **Step 1: Write failing MCP tests**

Add tests that:

- `validate_policy_pack` is listed in `tools/list`.
- `validate_policy_pack` returns a `pass` report for a valid pack.
- `enforce_intent` accepts `policy_pack_path`.
- `enforce_intent` rejects simultaneous `manifest` and `policy_pack_path`.

- [ ] **Step 2: Run MCP tests and verify failure**

Run: `pytest tests/test_mcp.py -q`

Expected: new tests fail because MCP tool support is missing.

- [ ] **Step 3: Implement MCP tool schema and dispatch**

Import Policy Pack helpers, add `validate_policy_pack` tool, and extend `enforce_intent` argument validation to accept exactly one of `manifest` or `policy_pack_path`.

- [ ] **Step 4: Run MCP tests**

Run: `pytest tests/test_mcp.py -q`

Expected: all MCP tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/omniglyph/mcp_server.py tests/test_mcp.py
git commit -m "feat: expose policy packs in MCP"
```

### Task 6: Documentation, Examples, and Maintenance Log

**Files:**
- Create: `examples/policy-packs/agent_intents/policy.json`
- Create: `examples/policy-packs/agent_intents/intents.csv`
- Create: `docs/specs/policy-pack-standard.md`
- Create: `docs/product/v0.8-maintenance-log.md`
- Modify: `docs/architecture/language-security-gateway.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/mcp-tools.md`
- Modify: `docs/api.md`

- [ ] **Step 1: Add example pack**

Use the same schema and example rows from the spec, with at least one `allow`, one `review`, and one `block` intent.

- [ ] **Step 2: Add user-facing Policy Pack standard**

Document layout, metadata, CSV fields, runtime behavior, CLI commands, API/MCP behavior, root restriction, and safety boundary.

- [ ] **Step 3: Update product docs**

Update language-security architecture, API docs, MCP docs, README files, changelog, and v0.8 maintenance log with paths and verification expectations.

- [ ] **Step 4: Run documentation-sensitive tests**

Run: `pytest tests/test_examples.py tests/test_package_manifest.py -q`

Expected: pass after examples and package manifest expectations are updated if needed.

- [ ] **Step 5: Commit**

```bash
git add examples/policy-packs docs README.md README.zh-CN.md CHANGELOG.md
git commit -m "docs: document policy pack intent guardrails"
```

### Task 7: Final Verification and Push

**Files:**
- Inspect all changed files.

- [ ] **Step 1: Run focused regression suite**

Run: `pytest tests/test_policy_pack.py tests/test_language_security.py tests/test_api.py tests/test_mcp.py tests/test_config.py -q`

Expected: all selected tests pass.

- [ ] **Step 2: Run full release gate**

Run: `scripts/release_check.sh`

Expected: pytest, Ruff, mypy, diff check, MCP smoke, build, Twine check, artifact audit, wheel smoke, and demo check all pass.

- [ ] **Step 3: Inspect final diff and log**

Run:

```bash
git status --short
git log --oneline -8
```

Expected: only intentional committed changes remain, with no uncommitted files except generated build artifacts ignored by git.

- [ ] **Step 4: Push branch**

Run:

```bash
git push
```

Expected: remote branch updates successfully.
