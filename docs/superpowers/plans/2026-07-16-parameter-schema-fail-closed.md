# OmniGlyph Parameter Schema Fail-Closed Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject malformed uses of OmniGlyph's documented lightweight parameter-schema keywords across direct Python, inline manifest, Policy Pack, CLI, API, and MCP paths.

**Architecture:** Add one dependency-free recursive meta-validator in `parameter_schema.py`. Reuse it at the direct evaluator, inline manifest, and Policy Pack row boundaries so malformed policy definitions fail before parameter evaluation while unknown keywords remain ignored.

**Tech Stack:** Python 3.10+, stdlib `math`/JSON/CSV, FastAPI/Pydantic, MCP JSON-RPC, pytest, Ruff, mypy

---

## File Map

- `src/omniglyph/parameter_schema.py`: schema meta-validation and defensive direct evaluation.
- `src/omniglyph/language_security.py`: inline manifest schema integration.
- `src/omniglyph/policy_pack.py`: Policy Pack row schema integration.
- `tests/test_parameter_schema.py`: meta-validator and direct-call regressions.
- `tests/test_language_security.py`: core inline manifest regression.
- `tests/test_policy_pack.py`: Policy Pack and CLI regressions.
- `tests/test_api.py`: inline and policy-path API regressions.
- `tests/test_mcp.py`: inline and policy-path MCP regressions.
- `docs/specs/policy-pack-standard.md`: supported-keyword validity contract.
- `docs/architecture/language-security-gateway.md`: fail-closed schema flow.
- `docs/product/project-status.md`: third-stage closeout link.
- `docs/superpowers/reviews/2026-07-16-parameter-schema-fail-closed-closeout.md`: evidence and handoff.

### Task 1: Build the Recursive Schema Meta-Validator

**Files:**
- Modify: `src/omniglyph/parameter_schema.py`
- Test: `tests/test_parameter_schema.py`

- [ ] **Step 1: Add failing meta-schema tests**

Add imports for `validate_parameter_schema` and `pytest`, then add sixteen malformed
cases. The expected path proves recursive errors identify the schema definition,
not the runtime parameter value.

```python
import pytest

from omniglyph.parameter_schema import validate_parameter_schema, validate_parameters


@pytest.mark.parametrize(
    ("schema", "expected_path"),
    [
        ([], "$"),
        ({"type": []}, "$.type"),
        ({"type": "date"}, "$.type"),
        ({"required": "service"}, "$.required"),
        ({"required": [" "]}, "$.required[0]"),
        ({"properties": []}, "$.properties"),
        ({"properties": {"": {}}}, "$.properties"),
        ({"properties": {"service": []}}, "$.properties.service"),
        ({"enum": "safe"}, "$.enum"),
        ({"minLength": True}, "$.minLength"),
        ({"minLength": -1}, "$.minLength"),
        ({"maxLength": "8"}, "$.maxLength"),
        ({"minimum": True}, "$.minimum"),
        ({"minimum": float("nan")}, "$.minimum"),
        ({"maximum": "10"}, "$.maximum"),
        ({"items": []}, "$.items"),
    ],
)
def test_validate_parameter_schema_rejects_malformed_supported_keywords(schema, expected_path):
    findings = validate_parameter_schema(schema)

    assert expected_path in {finding["path"] for finding in findings}


def test_validate_parameter_schema_accepts_valid_nested_schema_and_ignores_unknown_keywords():
    schema = {
        "type": "object",
        "required": ["service"],
        "properties": {
            "service": {"type": "string", "enum": ["network"], "pattern": "^[a-z]+$"},
            "retries": {"type": "integer", "minimum": 1, "maximum": 3},
            "tags": {"type": "array", "items": {"type": "string", "minLength": 1}},
        },
        "format": "ignored",
    }

    assert validate_parameter_schema(schema) == []


def test_validate_parameters_fails_closed_on_invalid_schema():
    findings = validate_parameters({}, {"required": "service"})

    assert findings == [
        {"path": "$.schema.required", "rule": "type", "message": "required must be a list."}
    ]
```

- [ ] **Step 2: Run focused tests and verify expected failures**

Run: `.venv/bin/python -m pytest tests/test_parameter_schema.py -k 'parameter_schema or invalid_schema' -v`

Expected: collection fails because `validate_parameter_schema` does not exist.

- [ ] **Step 3: Implement the recursive validator and defensive evaluator**

Add `math`, the allowed type set, helper predicates, and the validator. Process
keywords in the fixed order shown here and ignore every unknown key.

```python
import math
from typing import Any

Finding = dict[str, str]
ALLOWED_PARAMETER_TYPES = {"object", "string", "number", "integer", "boolean", "array"}


def validate_parameter_schema(schema: object, path: str = "$") -> list[Finding]:
    if not isinstance(schema, dict):
        return [_finding(path, "type", "Parameter schema must be an object.")]

    findings: list[Finding] = []
    expected_type = schema.get("type")
    if "type" in schema and (
        not isinstance(expected_type, str) or expected_type not in ALLOWED_PARAMETER_TYPES
    ):
        findings.append(
            _finding(
                f"{path}.type",
                "type",
                "Schema type must be one of array, boolean, integer, number, object, string.",
            )
        )

    required = schema.get("required")
    if "required" in schema:
        if not isinstance(required, list):
            findings.append(_finding(f"{path}.required", "type", "required must be a list."))
        else:
            for index, field in enumerate(required):
                if not isinstance(field, str) or not field.strip():
                    findings.append(
                        _finding(
                            f"{path}.required[{index}]",
                            "type",
                            "Required field name must be a non-empty string.",
                        )
                    )

    properties = schema.get("properties")
    if "properties" in schema:
        if not isinstance(properties, dict):
            findings.append(_finding(f"{path}.properties", "type", "properties must be an object."))
        else:
            for field, field_schema in properties.items():
                if not isinstance(field, str) or not field.strip():
                    findings.append(
                        _finding(f"{path}.properties", "type", "Property name must be a non-empty string.")
                    )
                    continue
                findings.extend(validate_parameter_schema(field_schema, f"{path}.properties.{field}"))

    if "enum" in schema and not isinstance(schema.get("enum"), list):
        findings.append(_finding(f"{path}.enum", "type", "enum must be a list."))

    for keyword in ("minLength", "maxLength"):
        if keyword in schema and not _is_non_negative_integer(schema.get(keyword)):
            findings.append(
                _finding(f"{path}.{keyword}", "type", f"{keyword} must be a non-negative integer.")
            )

    for keyword in ("minimum", "maximum"):
        if keyword in schema and not _is_finite_number(schema.get(keyword)):
            findings.append(_finding(f"{path}.{keyword}", "type", f"{keyword} must be a finite number."))

    if "items" in schema:
        findings.extend(validate_parameter_schema(schema.get("items"), f"{path}.items"))
    return findings


def _is_non_negative_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_finite_number(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return False
    return not isinstance(value, float) or math.isfinite(value)
```

Change direct evaluation to validate first and narrow the schema before calling the
existing runtime evaluator:

```python
def validate_parameters(parameters: object, schema: object) -> list[Finding]:
    schema_findings = validate_parameter_schema(schema, "$.schema")
    if schema_findings:
        return schema_findings
    assert isinstance(schema, dict)
    if not schema:
        return []
    return _validate_value(parameters, schema, "$")
```

- [ ] **Step 4: Run parameter-schema tests and static checks**

Run: `.venv/bin/python -m pytest tests/test_parameter_schema.py -v`

Run: `.venv/bin/python -m ruff check src/omniglyph/parameter_schema.py tests/test_parameter_schema.py && .venv/bin/python -m mypy src/omniglyph/parameter_schema.py`

Expected: 25 parameter-schema tests pass; Ruff and mypy report no errors.

- [ ] **Step 5: Commit the meta-validator**

```bash
git add src/omniglyph/parameter_schema.py tests/test_parameter_schema.py
git commit -m "fix: validate parameter schema definitions"
```

### Task 2: Fail Closed on Invalid Inline Parameter Schemas

**Files:**
- Modify: `src/omniglyph/language_security.py`
- Test: `tests/test_language_security.py`
- Test: `tests/test_api.py`
- Test: `tests/test_mcp.py`

- [ ] **Step 1: Add failing inline regressions**

Extend the core invalid-manifest matrix with a malformed nested schema:

```python
(
    {"intents": [{"intent_id": "x", "parameters_schema": {"properties": {"service": {"type": "date"}}}}]},
    "$.intents[0].parameters_schema.properties.service.type",
),
```

Add API and MCP tests that require the same malformed schema to return normal
blocked evidence rather than `allow`:

```python
def test_language_security_enforce_intent_blocks_invalid_inline_parameter_schema(tmp_path):
    client = TestClient(create_app(GlyphRepository(tmp_path / "test.sqlite3")))
    manifest = {
        "intents": [
            {"intent_id": "network.restart", "decision": "allow", "parameters_schema": {"required": "service"}}
        ]
    }

    response = client.post(
        "/api/v1/language-security/enforce-intent",
        json={"intent_id": "network.restart", "manifest": manifest, "parameters": {}},
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "block"
    assert response.json()["status"] == "invalid_manifest"


def test_handle_mcp_enforce_intent_blocks_invalid_inline_parameter_schema(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    manifest = {
        "intents": [
            {"intent_id": "network.restart", "decision": "allow", "parameters_schema": {"required": "service"}}
        ]
    }
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 30,
            "method": "tools/call",
            "params": {
                "name": "enforce_intent",
                "arguments": {"intent_id": "network.restart", "manifest": manifest, "parameters": {}},
            },
        },
        repository=repository,
    )

    payload = mcp_json(response)
    assert payload["decision"] == "block"
    assert payload["status"] == "invalid_manifest"
```

- [ ] **Step 2: Run focused tests and verify fail-open behavior**

Run: `.venv/bin/python -m pytest tests/test_language_security.py tests/test_api.py tests/test_mcp.py -k 'invalid_manifests or invalid_inline_parameter_schema' -v`

Expected: the new core, API, and MCP cases return `allow / matched` or omit the
expected schema finding.

- [ ] **Step 3: Integrate the meta-validator with manifest validation**

Import `validate_parameter_schema`. Preserve the existing non-object message, and
extend findings only when the container is an object.

```python
from omniglyph.parameter_schema import validate_parameter_schema, validate_parameters

# Inside validate_intent_manifest()
parameters_schema = intent.get("parameters_schema")
if "parameters_schema" in intent:
    if not isinstance(parameters_schema, dict):
        findings.append(
            _manifest_finding(
                f"{path}.parameters_schema",
                "type",
                "parameters_schema must be an object.",
            )
        )
    else:
        findings.extend(
            validate_parameter_schema(parameters_schema, f"{path}.parameters_schema")
        )
```

- [ ] **Step 4: Run core and adapter suites plus static checks**

Run: `.venv/bin/python -m pytest tests/test_language_security.py tests/test_api.py tests/test_mcp.py -v`

Run: `.venv/bin/python -m ruff check src/omniglyph/language_security.py tests/test_language_security.py tests/test_api.py tests/test_mcp.py && .venv/bin/python -m mypy src/omniglyph/language_security.py`

Expected: all commands pass and malformed inline schemas return
`block / invalid_manifest`.

- [ ] **Step 5: Commit inline schema enforcement**

```bash
git add src/omniglyph/language_security.py tests/test_language_security.py tests/test_api.py tests/test_mcp.py
git commit -m "fix: reject invalid inline parameter schemas"
```

### Task 3: Reject Invalid Policy Pack Parameter Schemas

**Files:**
- Modify: `src/omniglyph/policy_pack.py`
- Test: `tests/test_policy_pack.py`
- Test: `tests/test_api.py`
- Test: `tests/test_mcp.py`

- [ ] **Step 1: Add failing Policy Pack and adapter regressions**

For each existing pack helper, replace the valid required list in the first row
with a malformed required string:

```python
text = intents_path.read_text(encoding="utf-8")
intents_path.write_text(
    text.replace('""required"":[""service""]', '""required"":""service""'),
    encoding="utf-8",
)
```

Add a direct validation/loader test:

```python
def test_policy_pack_rejects_invalid_parameter_schema_keywords(tmp_path):
    pack_dir = tmp_path / "policy"
    write_policy_pack(pack_dir)
    intents_path = pack_dir / "intents.csv"
    text = intents_path.read_text(encoding="utf-8")
    intents_path.write_text(
        text.replace('""required"":[""service""]', '""required"":""service""'),
        encoding="utf-8",
    )

    report = validate_policy_pack(pack_dir)

    assert report["status"] == "fail"
    assert "intents.csv row 2: parameters_schema.required: required must be a list." in report["errors"]
    with pytest.raises(ValueError, match="invalid policy pack:.*parameters_schema.required"):
        load_policy_pack(pack_dir)
```

Add a CLI test requiring exit `2` without a traceback:

```python
def test_cli_enforce_intent_rejects_invalid_parameter_schema(tmp_path):
    pack_dir = tmp_path / "policy"
    write_policy_pack(pack_dir)
    intents_path = pack_dir / "intents.csv"
    text = intents_path.read_text(encoding="utf-8")
    intents_path.write_text(
        text.replace('""required"":[""service""]', '""required"":""service""'),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "omniglyph.cli",
            "enforce-intent",
            "network.restart",
            "--policy-pack",
            str(pack_dir),
            "--actor-role",
            "admin",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "parameters_schema.required" in result.stderr
    assert "Traceback" not in result.stderr
```

Add an API policy-path test requiring HTTP `400`:

```python
def test_language_security_enforce_intent_rejects_invalid_parameter_schema_pack(tmp_path):
    pack_dir = tmp_path / "policy"
    write_api_policy_pack(pack_dir)
    intents_path = pack_dir / "intents.csv"
    text = intents_path.read_text(encoding="utf-8")
    intents_path.write_text(
        text.replace('""required"":[""service""]', '""required"":""service""'),
        encoding="utf-8",
    )
    client = TestClient(create_app(GlyphRepository(tmp_path / "test.sqlite3")))

    response = client.post(
        "/api/v1/language-security/enforce-intent",
        json={"intent_id": "network.restart", "policy_pack_path": str(pack_dir)},
    )

    assert response.status_code == 400
    assert "parameters_schema.required" in response.json()["detail"]
```

Add an MCP policy-path test requiring `-32602`:

```python
def test_handle_mcp_enforce_intent_rejects_invalid_parameter_schema_pack(tmp_path):
    pack_dir = tmp_path / "policy"
    write_mcp_policy_pack(pack_dir)
    intents_path = pack_dir / "intents.csv"
    text = intents_path.read_text(encoding="utf-8")
    intents_path.write_text(
        text.replace('""required"":[""service""]', '""required"":""service""'),
        encoding="utf-8",
    )
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()

    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 31,
            "method": "tools/call",
            "params": {
                "name": "enforce_intent",
                "arguments": {"intent_id": "network.restart", "policy_pack_path": str(pack_dir)},
            },
        },
        repository=repository,
    )

    assert response["error"]["code"] == -32602
    assert "parameters_schema.required" in response["error"]["message"]
```

- [ ] **Step 2: Run focused tests and verify invalid packs pass or execute**

Run: `.venv/bin/python -m pytest tests/test_policy_pack.py tests/test_api.py tests/test_mcp.py -k invalid_parameter_schema -v`

Expected: validation reports `pass`, the loader succeeds, CLI exits `0`, API returns
`200`, and MCP returns a normal tool result.

- [ ] **Step 3: Integrate schema findings into Policy Pack row errors**

Import `validate_parameter_schema` and append each path-based finding after JSON
object parsing:

```python
from omniglyph.parameter_schema import validate_parameter_schema

# Inside _validate_intent_row()
parameters_schema = _parse_json_object(row.get("parameters_schema") or "{}")
if parameters_schema is None:
    errors.append(f"{INTENTS_FILENAME} row {row_number}: parameters_schema must be a JSON object")
else:
    for finding in validate_parameter_schema(parameters_schema):
        schema_path = finding["path"][1:]
        errors.append(
            f"{INTENTS_FILENAME} row {row_number}: "
            f"parameters_schema{schema_path}: {finding['message']}"
        )
```

Keep the existing `if errors: return {}, errors` branch after schema findings so no
invalid row reaches `_intent_payload()`.

- [ ] **Step 4: Run Policy Pack and adapter suites plus static checks**

Run: `.venv/bin/python -m pytest tests/test_policy_pack.py tests/test_api.py tests/test_mcp.py -v`

Run: `.venv/bin/python -m ruff check src/omniglyph/policy_pack.py tests/test_policy_pack.py tests/test_api.py tests/test_mcp.py && .venv/bin/python -m mypy src/omniglyph/policy_pack.py`

Expected: all commands pass; malformed schemas use CLI `2`, API `400`, and MCP
`-32602` without tracebacks or internal errors.

- [ ] **Step 5: Commit Policy Pack schema enforcement**

```bash
git add src/omniglyph/policy_pack.py tests/test_policy_pack.py tests/test_api.py tests/test_mcp.py
git commit -m "fix: reject invalid policy pack parameter schemas"
```

### Task 4: Document, Review, and Verify the Third Stage

**Files:**
- Modify: `docs/specs/policy-pack-standard.md`
- Modify: `docs/architecture/language-security-gateway.md`
- Modify: `docs/product/project-status.md`
- Create: `docs/superpowers/reviews/2026-07-16-parameter-schema-fail-closed-closeout.md`

- [ ] **Step 1: Update runtime documentation**

Document the supported-keyword meta-validation rules, stable schema finding paths,
unknown-keyword compatibility, direct Python defense, and unchanged CLI/API/MCP
error semantics.

- [ ] **Step 2: Request independent code review**

Review the implementation from this plan's base commit through the current head
against `docs/superpowers/specs/2026-07-16-parameter-schema-fail-closed-design.md`.
Fix every Critical or Important finding with a focused failing test before closeout.

- [ ] **Step 3: Run the complete release gate and privacy scan**

Run: `PATH=.venv/bin:$PATH bash scripts/release_check.sh`

Run: `bash scripts/privacy-scan.sh`

Expected: at least 254 tests, Ruff, mypy, diff check, seventeen-tool MCP smoke, build, Twine,
artifact audit, clean-wheel smoke, demo, and privacy scan all pass.

- [ ] **Step 4: Write and link the closeout report**

Record reproductions, root cause, changes, commits, test coverage, exact verification
output, compatibility, remaining risks, Safe-Agent router misclassification, and the
local publication boundary. Link it from `docs/product/project-status.md`.

- [ ] **Step 5: Run final document and branch checks**

Run: `rg -n 'T[B]D|T[O]DO|F[I]XME|P[L]ACEHOLDER|待[定]' docs/superpowers/reviews/2026-07-16-parameter-schema-fail-closed-closeout.md`

Run: `git diff --check && git status --short`

Expected: no placeholder or whitespace findings; only intended closeout documents
remain.

- [ ] **Step 6: Commit the third-stage closeout**

```bash
git add docs/specs/policy-pack-standard.md docs/architecture/language-security-gateway.md docs/product/project-status.md docs/superpowers/plans/2026-07-16-parameter-schema-fail-closed.md docs/superpowers/reviews/2026-07-16-parameter-schema-fail-closed-closeout.md
git commit -m "docs: close parameter schema fail-closed hardening"
```

### Task 5: Final Independent Verification

**Files:**
- Verify only.

- [ ] **Step 1: Run fresh tests and static checks**

Run: `.venv/bin/python -m pytest -q`

Run: `.venv/bin/python -m ruff check . && .venv/bin/python -m mypy src`

Expected: at least 254 tests pass; Ruff and mypy report no errors.

- [ ] **Step 2: Inspect the branch diff and status**

Run: `git diff codex/intent-fail-closed...HEAD --check && git diff codex/intent-fail-closed...HEAD --stat && git status --short`

Expected: only the approved third-stage code, tests, specs, plan, and closeout differ
from the completed second-stage branch; the working tree is clean.

- [ ] **Step 3: Keep the branch local**

Do not merge, push, tag, publish, or deploy without a separate user instruction.
