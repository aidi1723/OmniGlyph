# OmniGlyph Intent Policy Fail-Closed Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure malformed inline intent manifests and invalid Policy Packs block deterministically across Python, CLI, API, and MCP instead of allowing actions or raising uncontrolled exceptions.

**Architecture:** Add one dependency-free inline manifest validator at the core enforcement boundary and make Policy Pack validation and loading consume one shared parsed snapshot. Keep transport adapters thin: they translate strict loader failures into their native error semantics while every JSON inline-manifest value reaches the core fail-closed validator.

**Tech Stack:** Python 3.10+, FastAPI/Pydantic, stdlib JSON/CSV/argparse, MCP JSON-RPC over stdio, pytest, Ruff, mypy

---

## File Map

- `src/omniglyph/language_security.py`: manifest validation findings and fail-closed enforcement.
- `src/omniglyph/policy_pack.py`: single-snapshot Policy Pack inspection, validation, and loading.
- `src/omniglyph/cli.py`: argparse error for invalid packs.
- `src/omniglyph/api.py`: HTTP 400 for invalid policy-path enforcement.
- `src/omniglyph/mcp_server.py`: JSON-RPC `-32602` for invalid policy-path enforcement.
- `tests/test_language_security.py`: core and API inline manifest regressions.
- `tests/test_policy_pack.py`: strict loader and CLI regressions.
- `tests/test_api.py`: invalid Policy Pack HTTP regression.
- `tests/test_mcp.py`: invalid Policy Pack and inline manifest MCP regressions.
- `docs/specs/policy-pack-standard.md`: automatic enforcement validation contract.
- `docs/architecture/language-security-gateway.md`: fail-closed runtime flow.
- `docs/product/project-status.md`: second-stage closeout link.
- `docs/superpowers/reviews/2026-07-16-intent-policy-fail-closed-closeout.md`: evidence and handoff.

### Task 1: Validate Inline Manifests at the Core Boundary

**Files:**
- Modify: `src/omniglyph/language_security.py`
- Test: `tests/test_language_security.py`

- [x] **Step 1: Add failing core regression tests**

Add tests for an unknown decision, string roles, a non-object intent, duplicate IDs,
and a valid approval manifest with omitted `decision`. Invalid cases must return
`block` / `invalid_manifest` with path-based findings and must not raise.

```python
@pytest.mark.parametrize(
    ("manifest", "expected_path"),
    [
        ({"intents": [{"intent_id": "x", "decision": "sometimes"}]}, "$.intents[0].decision"),
        ({"intents": [{"intent_id": "x", "allowed_roles": "admin"}]}, "$.intents[0].allowed_roles"),
        ({"intents": [1]}, "$.intents[0]"),
        ({"intents": [{"intent_id": "x"}, {"intent_id": "x"}]}, "$.intents[1].intent_id"),
    ],
)
def test_enforce_intent_manifest_blocks_invalid_manifests(manifest, expected_path):
    result = enforce_intent_manifest("x", manifest, actor_role="admin")

    assert result["decision"] == "block"
    assert result["status"] == "invalid_manifest"
    assert expected_path in {finding["path"] for finding in result["manifest_findings"]}


def test_enforce_intent_manifest_preserves_omitted_decision_compatibility():
    manifest = {"intents": [{"intent_id": "x", "requires_approval": True, "allowed_roles": ["admin"]}]}

    result = enforce_intent_manifest("x", manifest, actor_role="admin")

    assert result["decision"] == "review"
    assert result["status"] == "matched"
```

- [x] **Step 2: Run focused tests and verify failures**

Run: `.venv/bin/python -m pytest tests/test_language_security.py -k 'invalid_manifests or omitted_decision' -v`

Expected: invalid decisions and string roles incorrectly allow; non-object intent
raises; duplicate IDs are accepted; compatibility case already passes.

- [x] **Step 3: Implement structured manifest validation**

Add `validate_intent_manifest(manifest: object) -> list[dict[str, str]]` with the
rules in the approved spec. Call it before `_find_intent()`. Extend `_intent_result`
with optional `manifest_findings`; invalid input returns the stable limit
`Intent manifest is invalid and cannot authorize actions.`.

- [x] **Step 4: Run all language-security tests and static checks**

Run: `.venv/bin/python -m pytest tests/test_language_security.py -v`

Run: `.venv/bin/python -m ruff check src/omniglyph/language_security.py tests/test_language_security.py && .venv/bin/python -m mypy src/omniglyph/language_security.py`

Expected: all commands pass.

- [x] **Step 5: Commit core fail-closed validation**

```bash
git add src/omniglyph/language_security.py tests/test_language_security.py
git commit -m "fix: fail closed on invalid intent manifests"
```

### Task 2: Make Policy Pack Loading Strict

**Files:**
- Modify: `src/omniglyph/policy_pack.py`
- Test: `tests/test_policy_pack.py`

- [x] **Step 1: Add failing invalid-loader tests**

Reuse the existing invalid-row and duplicate-ID pack fixtures. Assert
`load_policy_pack()` raises `ValueError` with an `invalid policy pack:` prefix for
both, while the valid loader test remains unchanged.

```python
with pytest.raises(ValueError, match="invalid policy pack:.*duplicate intent_id"):
    load_policy_pack(pack_dir)
```

- [x] **Step 2: Run loader tests and verify they fail**

Run: `.venv/bin/python -m pytest tests/test_policy_pack.py -k 'load_policy_pack or duplicate' -v`

Expected: invalid packs currently load successfully.

- [x] **Step 3: Validate before loading**

At the start of `load_policy_pack()`, call `validate_policy_pack()`. If status is
not `pass`, raise `ValueError("invalid policy pack: " + "; ".join(report["errors"]))`.
Do not change the valid `PolicyPack` result.

- [x] **Step 4: Run Policy Pack tests and static checks**

Run: `.venv/bin/python -m pytest tests/test_policy_pack.py -v`

Run: `.venv/bin/python -m ruff check src/omniglyph/policy_pack.py tests/test_policy_pack.py && .venv/bin/python -m mypy src/omniglyph/policy_pack.py`

Expected: all commands pass.

- [x] **Step 5: Commit strict Policy Pack loading**

```bash
git add src/omniglyph/policy_pack.py tests/test_policy_pack.py
git commit -m "fix: validate policy packs before loading"
```

### Task 3: Translate Validation Failures Across CLI, API, and MCP

**Files:**
- Modify: `src/omniglyph/cli.py`
- Modify: `src/omniglyph/api.py`
- Modify: `src/omniglyph/mcp_server.py`
- Test: `tests/test_policy_pack.py`
- Test: `tests/test_api.py`
- Test: `tests/test_mcp.py`
- Test: `tests/test_language_security.py`

- [x] **Step 1: Add failing adapter regression tests**

For a duplicate-ID Policy Pack, assert CLI exits 2 without `Traceback`, API returns
HTTP 400, and MCP returns `-32602`. For malformed inline manifests, assert API and
MCP return normal blocked `invalid_manifest` results.

```python
assert cli_result.returncode == 2
assert "invalid policy pack:" in cli_result.stderr
assert "Traceback" not in cli_result.stderr

assert api_response.status_code == 400
assert api_response.json()["detail"].startswith("invalid policy pack:")

assert mcp_response["error"]["code"] == -32602
assert mcp_response["error"]["message"].startswith("invalid policy pack:")
```

- [x] **Step 2: Run adapter tests and verify expected failures**

Run: `.venv/bin/python -m pytest tests/test_policy_pack.py tests/test_api.py tests/test_mcp.py tests/test_language_security.py -k 'invalid_pack or invalid_inline_manifest' -v`

Expected: CLI prints a traceback, API raises through TestClient, and MCP reaches the
generic internal-error boundary or raises in direct calls.

- [x] **Step 3: Add native error translation**

- CLI: catch `ValueError` around `load_policy_pack()` and call `parser.error(str(exc))`.
- API: catch `ValueError` and raise `HTTPException(status_code=400, detail=str(exc))`.
- MCP: catch `ValueError` and return `_error(request_id, -32602, str(exc))`.
- Inline manifests need no adapter branch beyond the core blocked result.

- [x] **Step 4: Run adapter suites and MCP smoke**

Run: `.venv/bin/python -m pytest tests/test_policy_pack.py tests/test_api.py tests/test_mcp.py tests/test_language_security.py -v`

Run: `PYTHON=.venv/bin/python bash scripts/mcp_smoke_test.sh .venv/bin/omniglyph-mcp`

Expected: all tests pass and the same seventeen MCP tools are reported.

- [x] **Step 5: Commit adapter error semantics**

```bash
git add src/omniglyph/cli.py src/omniglyph/api.py src/omniglyph/mcp_server.py tests/test_policy_pack.py tests/test_api.py tests/test_mcp.py tests/test_language_security.py
git commit -m "fix: surface invalid intent policies consistently"
```

### Task 4: Reject Non-String Inline Decisions

**Files:**
- Modify: `src/omniglyph/language_security.py`
- Test: `tests/test_language_security.py`

- [ ] **Step 1: Add failing array and object decision cases**

Extend `test_enforce_intent_manifest_blocks_invalid_manifests` with both JSON
container types so the test proves enum validation never hashes arbitrary input.

```python
({"intents": [{"intent_id": "x", "decision": []}]}, "$.intents[0].decision"),
({"intents": [{"intent_id": "x", "decision": {}}]}, "$.intents[0].decision"),
```

- [ ] **Step 2: Run the focused test and verify the expected error**

Run: `.venv/bin/python -m pytest tests/test_language_security.py -k invalid_manifests -v`

Expected: both new cases error with `TypeError: unhashable type` before an
`invalid_manifest` result can be returned.

- [ ] **Step 3: Type-check decision before enum membership**

```python
decision = intent.get("decision")
if "decision" in intent and (
    not isinstance(decision, str) or decision not in ALLOWED_INTENT_DECISIONS
):
    findings.append(
        _manifest_finding(
            f"{path}.decision",
            "enum",
            "Decision must be one of allow, block, review.",
        )
    )
```

- [ ] **Step 4: Run focused and static checks**

Run: `.venv/bin/python -m pytest tests/test_language_security.py -v`

Run: `.venv/bin/python -m ruff check src/omniglyph/language_security.py tests/test_language_security.py && .venv/bin/python -m mypy src/omniglyph/language_security.py`

Expected: all commands pass with no exception cases.

- [ ] **Step 5: Commit decision type hardening**

```bash
git add src/omniglyph/language_security.py tests/test_language_security.py
git commit -m "fix: reject non-string intent decisions"
```

### Task 5: Load the Validated Policy Pack Snapshot

**Files:**
- Modify: `src/omniglyph/policy_pack.py`
- Test: `tests/test_policy_pack.py`
- Test: `tests/test_api.py`
- Test: `tests/test_mcp.py`

- [ ] **Step 1: Add failing snapshot and malformed-CSV regressions**

Monkeypatch `_validate_intents()` so the source file changes immediately after the
validated rows are returned. The loader must still return the original `review`
row. Add an extra-column row and require a failed report plus a stable loader error.
Update the existing CLI/API/MCP invalid-pack fixtures to use the extra-column row so
all three adapters prove that this structural error does not escape as a traceback,
HTTP 500, or JSON-RPC internal error.

```python
def test_load_policy_pack_uses_the_validated_snapshot(tmp_path, monkeypatch):
    pack_dir = tmp_path / "policy"
    write_policy_pack(pack_dir)
    original_validate_intents = policy_pack_module._validate_intents

    def validate_then_replace(path):
        intents, errors = original_validate_intents(path)
        intents_path = path / "intents.csv"
        text = intents_path.read_text(encoding="utf-8")
        intents_path.write_text(text.replace("review,high", "allow,high"), encoding="utf-8")
        return intents, errors

    monkeypatch.setattr(policy_pack_module, "_validate_intents", validate_then_replace)

    pack = load_policy_pack(pack_dir)

    assert pack.intents[0]["decision"] == "review"


def test_policy_pack_rejects_rows_with_extra_columns(tmp_path):
    pack_dir = tmp_path / "policy"
    write_policy_pack(pack_dir)
    intents_path = pack_dir / "intents.csv"
    lines = intents_path.read_text(encoding="utf-8").splitlines()
    lines[1] += ",unexpected"
    intents_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    report = validate_policy_pack(pack_dir)

    assert report["status"] == "fail"
    assert "intents.csv row 2: unexpected extra column values" in report["errors"]
    with pytest.raises(ValueError, match="invalid policy pack:.*unexpected extra column values"):
        load_policy_pack(pack_dir)
```

- [ ] **Step 2: Run focused tests and verify both root causes**

Run: `.venv/bin/python -m pytest tests/test_policy_pack.py tests/test_api.py tests/test_mcp.py -k 'validated_snapshot or extra_columns or invalid_pack' -v`

Expected: the snapshot test returns the replacement `allow` decision, while the
extra-column cases raise `AttributeError` or surface adapter internal errors.

- [ ] **Step 3: Introduce one internal Policy Pack inspection result**

Add `_inspect_policy_pack()` and make both public functions consume its returned
metadata, intents, and errors. Preserve the existing report shape and its rule that
summary counts are zero when any error exists. Remove the now-unused second-read
helpers.

```python
def load_policy_pack(path: Path | str) -> PolicyPack:
    metadata, intents, errors = _inspect_policy_pack(Path(path))
    if errors:
        raise ValueError("invalid policy pack: " + "; ".join(errors))
    return PolicyPack(metadata=metadata, intents=intents)


def validate_policy_pack(path: Path | str) -> dict:
    metadata, intents, errors = _inspect_policy_pack(Path(path))
    summary_intents = [] if errors else intents
    return _policy_pack_report(metadata, summary_intents, errors)


def _policy_pack_report(
    metadata: dict[str, Any],
    intents: list[dict[str, Any]],
    errors: list[str],
) -> dict:
    return {
        "schema": POLICY_PACK_SCHEMA,
        "status": "pass" if not errors else "fail",
        "policy": {
            "policy_id": metadata.get("policy_id"),
            "namespace": metadata.get("namespace"),
            "name": metadata.get("name"),
            "version": metadata.get("version"),
        },
        "summary": {
            "intent_count": len(intents),
            "allow_count": sum(1 for intent in intents if intent["decision"] == "allow"),
            "review_count": sum(1 for intent in intents if intent["decision"] == "review"),
            "block_count": sum(1 for intent in intents if intent["decision"] == "block"),
        },
        "errors": errors,
        "warnings": [],
    }


def _inspect_policy_pack(pack_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    metadata: dict[str, Any] = {}
    intents: list[dict[str, Any]] = []
    if not pack_dir.exists():
        errors.append(f"policy pack directory not found: {pack_dir}")
    elif not pack_dir.is_dir():
        errors.append(f"policy pack path must be a directory: {pack_dir}")
    if not errors:
        metadata, metadata_errors = _validate_metadata(pack_dir)
        errors.extend(metadata_errors)
        intents, intent_errors = _validate_intents(pack_dir)
        errors.extend(intent_errors)
    return metadata, intents, errors
```

At the start of each CSV row, reject DictReader overflow before calling `.strip()`
on row values:

```python
if None in row:
    errors.append(f"{INTENTS_FILENAME} row {row_number}: unexpected extra column values")
    continue
```

- [ ] **Step 4: Run Policy Pack and adapter suites plus static checks**

Run: `.venv/bin/python -m pytest tests/test_policy_pack.py tests/test_api.py tests/test_mcp.py -v`

Run: `.venv/bin/python -m ruff check src/omniglyph/policy_pack.py tests/test_policy_pack.py tests/test_api.py tests/test_mcp.py && .venv/bin/python -m mypy src/omniglyph/policy_pack.py`

Expected: all commands pass; invalid CSV uses the existing CLI `2`, API `400`, and
MCP `-32602` paths.

- [ ] **Step 5: Commit snapshot and CSV hardening**

```bash
git add src/omniglyph/policy_pack.py tests/test_policy_pack.py tests/test_api.py tests/test_mcp.py
git commit -m "fix: load validated policy pack snapshots"
```

### Task 6: Route Every Inline Manifest Through Core Validation

**Files:**
- Modify: `src/omniglyph/api.py`
- Modify: `src/omniglyph/mcp_server.py`
- Test: `tests/test_api.py`
- Test: `tests/test_mcp.py`

- [ ] **Step 1: Add failing top-level array regressions**

```python
def test_language_security_enforce_intent_blocks_non_object_inline_manifest(tmp_path):
    client = TestClient(create_app(GlyphRepository(tmp_path / "test.sqlite3")))

    response = client.post(
        "/api/v1/language-security/enforce-intent",
        json={"intent_id": "network.restart", "manifest": []},
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "block"
    assert response.json()["status"] == "invalid_manifest"


def test_handle_mcp_enforce_intent_blocks_non_object_inline_manifest(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 28,
            "method": "tools/call",
            "params": {"name": "enforce_intent", "arguments": {"intent_id": "x", "manifest": []}},
        },
        repository=repository,
    )

    payload = mcp_json(response)
    assert payload["decision"] == "block"
    assert payload["status"] == "invalid_manifest"
```

- [ ] **Step 2: Run focused tests and verify adapter rejection**

Run: `.venv/bin/python -m pytest tests/test_api.py tests/test_mcp.py -k non_object_inline_manifest -v`

Expected: API returns validation status `422`; MCP returns JSON-RPC `-32602`.

- [ ] **Step 3: Widen only the manifest transport boundary**

Change `IntentEnforceRequest.manifest` to `object | None` and remove the MCP branch
that requires `manifest` to be a dictionary. Keep the exactly-one-of check and all
other actor, parameter, and policy-path type checks unchanged. Both adapters then
pass the value to `enforce_intent_manifest()`.

```python
class IntentEnforceRequest(BaseModel):
    intent_id: str
    manifest: object | None = None
    policy_pack_path: str | None = None
    actor_role: str | None = None
    parameters: dict | None = None
```

- [ ] **Step 4: Run adapter, full test, and static checks**

Run: `.venv/bin/python -m pytest tests/test_api.py tests/test_mcp.py -v`

Run: `.venv/bin/python -m pytest -q`

Run: `.venv/bin/python -m ruff check src/omniglyph/api.py src/omniglyph/mcp_server.py tests/test_api.py tests/test_mcp.py && .venv/bin/python -m mypy src`

Expected: 227 tests pass; Ruff and mypy report no errors.

- [ ] **Step 5: Commit transport-boundary semantics**

```bash
git add src/omniglyph/api.py src/omniglyph/mcp_server.py tests/test_api.py tests/test_mcp.py
git commit -m "fix: validate all inline manifest values"
```

### Task 7: Document, Verify, and Close the Second Stage

**Files:**
- Modify: `docs/specs/policy-pack-standard.md`
- Modify: `docs/architecture/language-security-gateway.md`
- Modify: `docs/product/project-status.md`
- Create: `docs/superpowers/reviews/2026-07-16-intent-policy-fail-closed-closeout.md`

- [ ] **Step 1: Update runtime documentation**

State that enforcement validates Policy Packs automatically, malformed inline
manifests return blocked `invalid_manifest` evidence, and transport-specific
invalid-pack errors are CLI exit 2, HTTP 400, and MCP `-32602`.

- [ ] **Step 2: Run the full release gate and privacy scan**

Run: `PATH=.venv/bin:$PATH bash scripts/release_check.sh`

Run: `bash scripts/privacy-scan.sh`

Expected: tests, Ruff, mypy, diff check, seventeen-tool MCP smoke, build, Twine,
artifact audit, clean-wheel smoke, demo, and privacy scan all pass.

- [ ] **Step 3: Write and link the closeout report**

Record root-cause reproductions, resolved paths, exact verification output,
compatibility, remaining risks, Safe-Agent router misclassification, and the local
publication boundary. Link it from `docs/product/project-status.md`.

- [ ] **Step 4: Run final document and branch checks**

Run: `rg -n 'T[B]D|T[O]DO|F[I]XME|P[L]ACEHOLDER|待[定]' docs/superpowers/reviews/2026-07-16-intent-policy-fail-closed-closeout.md`

Run: `git diff --check && git status --short`

Expected: no placeholder or whitespace findings; only intended documentation remains.

- [ ] **Step 5: Commit the second-stage closeout**

```bash
git add docs/specs/policy-pack-standard.md docs/architecture/language-security-gateway.md docs/product/project-status.md docs/superpowers/reviews/2026-07-16-intent-policy-fail-closed-closeout.md
git commit -m "docs: close fail-closed intent policy hardening"
```

### Task 8: Final Independent Verification

**Files:**
- Verify only.

- [ ] **Step 1: Run fresh tests and static checks**

Run: `.venv/bin/python -m pytest -q`

Run: `.venv/bin/python -m ruff check . && .venv/bin/python -m mypy src`

Expected: all commands pass with no failures.

- [ ] **Step 2: Inspect the branch diff and status**

Run: `git diff main...HEAD --check && git diff main...HEAD --stat && git status --short`

Expected: only the approved fail-closed implementation, tests, specs, and closeout
records differ from `main`; working tree is clean.

- [ ] **Step 3: Keep the branch local**

Do not merge, push, tag, publish, or deploy without a separate user instruction.
