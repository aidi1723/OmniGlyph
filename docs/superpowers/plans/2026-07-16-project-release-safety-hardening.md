# OmniGlyph Project Release-Safety Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close confirmed release-safety gaps in ingestion, source downloads, policy validation, DLP redaction, and the MCP JSON-RPC boundary without changing the public product surface.

**Architecture:** Keep fixes at existing ownership boundaries: SQLite transaction helpers in `GlyphRepository`, filesystem integrity in `sources.py`, deterministic validation in the existing policy/parameter modules, redaction interval handling in `language_security.py`, and protocol validation in `mcp_server.py`. Every behavioral change begins with a focused failing regression test and retains the current API, CLI, MCP tool list, and database table layout.

**Tech Stack:** Python 3.10+, SQLite, FastAPI/Pydantic, stdlib JSON-RPC over stdio, pytest, Ruff, mypy, setuptools/build, Twine

---

## File Map

- `src/omniglyph/repository.py`: deterministic property identity, metadata upsert, transaction-scoped lexical replacement.
- `src/omniglyph/cli.py`: route `--replace-namespace` imports through the atomic repository operation.
- `src/omniglyph/sources.py`: temporary download, checksum validation, and atomic destination replacement.
- `src/omniglyph/policy_pack.py`: duplicate intent ID validation.
- `src/omniglyph/parameter_schema.py`: JSON-type-aware enum comparison.
- `src/omniglyph/language_security.py`: coalesced redaction intervals.
- `src/omniglyph/mcp_server.py`: JSON-RPC envelope/container validation and safe stdio error handling.
- `tests/test_repository.py`, `tests/test_sources.py`, `tests/test_policy_pack.py`, `tests/test_parameter_schema.py`, `tests/test_language_security.py`, `tests/test_mcp.py`: focused regression coverage.
- `docs/product/project-status.md`: link the new closeout record.
- `docs/superpowers/reviews/2026-07-16-project-release-safety-closeout.md`: final findings, evidence, compatibility, and residual-risk report.

### Task 1: Make Repository Ingestion Deterministic

**Files:**
- Modify: `src/omniglyph/repository.py`
- Test: `tests/test_repository.py`

- [ ] **Step 1: Add failing idempotency and import-order tests**

Add tests that ingest the same Unihan property twice and assert one database row,
then create a glyph through Unihan before importing its `GlyphRecord` and assert
that `record["unicode"]["name"]` is filled from UnicodeData.

```python
def test_repository_repeated_unihan_import_is_idempotent(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    source_id = repository.add_source_snapshot(
        SourceSnapshot("Unihan Database", "file://unihan", "fixture", "sha-unihan", "Unicode Terms", "Unihan.txt")
    )
    properties = list(parse_unihan_data(Path("tests/fixtures/Unihan.sample.txt")))[:1]

    repository.insert_unihan_properties(properties, source_id)
    repository.insert_unihan_properties(properties, source_id)

    with repository.connect() as connection:
        count = connection.execute("SELECT COUNT(*) FROM glyph_property").fetchone()[0]
    assert count == 1


def test_repository_unicode_import_fills_name_after_unihan_import(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    unihan_source = repository.add_source_snapshot(
        SourceSnapshot("Unihan Database", "file://unihan", "fixture", "sha-unihan", "Unicode Terms", "Unihan.txt")
    )
    unicode_source = repository.add_source_snapshot(
        SourceSnapshot("Unicode Database", "file://unicode", "fixture", "sha-unicode", "Unicode Terms", "UnicodeData.txt")
    )
    repository.insert_unihan_properties(list(parse_unihan_data(Path("tests/fixtures/Unihan.sample.txt")))[:1], unihan_source)
    repository.insert_glyph_records([GlyphRecord("铝", "U+94DD", "CJK UNIFIED IDEOGRAPH-94DD")], unicode_source)

    assert repository.find_by_glyph("铝")["unicode"]["name"] == "CJK UNIFIED IDEOGRAPH-94DD"
```

- [ ] **Step 2: Run the focused tests and verify both fail**

Run: `.venv/bin/python -m pytest tests/test_repository.py -k 'idempotent or fills_name' -v`

Expected: duplicate property count is `2`, and the Unicode name remains `None`.

- [ ] **Step 3: Implement deterministic property IDs and null-filling upserts**

Use UUID5 over `glyph_uid`, namespace, name, value, language, and source ID in
`_insert_property_with_connection`. Extend the glyph conflict clause with:

```sql
name = COALESCE(glyph_node.name, excluded.name),
updated_at = excluded.updated_at
```

This lets the primary key enforce exact idempotency even when `language` is SQL
`NULL`, while preserving an existing canonical name.

- [ ] **Step 4: Re-run repository tests**

Run: `.venv/bin/python -m pytest tests/test_repository.py -v`

Expected: all repository tests pass.

- [ ] **Step 5: Commit the deterministic ingestion change**

```bash
git add src/omniglyph/repository.py tests/test_repository.py
git commit -m "fix: make source ingestion deterministic"
```

### Task 2: Make Namespace Replacement Atomic

**Files:**
- Modify: `src/omniglyph/repository.py`
- Modify: `src/omniglyph/cli.py`
- Test: `tests/test_repository.py`

- [ ] **Step 1: Add a failing rollback test**

Seed one namespace, then call a new `replace_lexical_namespace` operation with an
entry whose `traits` contains a non-JSON-serializable object. Assert the operation
raises `TypeError`, the original term remains queryable, and no replacement source
snapshot remains committed.

```python
def test_repository_namespace_replacement_rolls_back_on_insert_failure(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    old_source = SourceSnapshot("Old Pack", "file://old", "1", "sha-old", "private", "old.csv")
    old_source_id = repository.add_source_snapshot(old_source)
    old_entry = DomainEntry("FOB", "trade:fob", "trade_term", "en", [], None, {}, "private_trade")
    repository.insert_lexical_entries([old_entry], old_source_id)
    invalid_entry = DomainEntry("CIF", "trade:cif", "trade_term", "en", [], None, {"bad": object()}, "private_trade")

    with pytest.raises(TypeError):
        repository.replace_lexical_namespace(
            "private_trade",
            [invalid_entry],
            SourceSnapshot("New Pack", "file://new", "2", "sha-new", "private", "new.csv"),
        )

    assert repository.find_term("FOB") is not None
    with repository.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM source_snapshot").fetchone()[0] == 1
```

- [ ] **Step 2: Run the rollback test and verify it fails**

Run: `.venv/bin/python -m pytest tests/test_repository.py::test_repository_namespace_replacement_rolls_back_on_insert_failure -v`

Expected: fail because `replace_lexical_namespace` does not exist.

- [ ] **Step 3: Refactor transaction-scoped repository helpers**

Extract private connection-aware helpers for source insertion, lexical entry
insertion, and namespace deletion. Keep existing public methods as transaction
wrappers. Add:

```python
def replace_lexical_namespace(self, namespace, entries, source: SourceSnapshot) -> int:
    with self.connect() as connection:
        self._delete_lexical_namespace_with_connection(connection, namespace)
        source_id = self._add_source_snapshot_with_connection(connection, source)
        return self._insert_lexical_entries_with_connection(connection, entries, source_id)
```

Update `ingest_domain_pack` so `replace_namespace=True` uses this operation; normal
imports continue through `add_source_snapshot` and `insert_lexical_entries`.

- [ ] **Step 4: Run repository and CLI tests**

Run: `.venv/bin/python -m pytest tests/test_repository.py tests/test_lexicon_pack.py tests/test_cli_product_tools.py -v`

Expected: all selected tests pass.

- [ ] **Step 5: Commit the atomic replacement change**

```bash
git add src/omniglyph/repository.py src/omniglyph/cli.py tests/test_repository.py
git commit -m "fix: replace lexical namespaces atomically"
```

### Task 3: Protect Existing Files During Source Downloads

**Files:**
- Modify: `src/omniglyph/sources.py`
- Test: `tests/test_sources.py`

- [ ] **Step 1: Add failing preservation tests**

Use a `file://` source for a checksum mismatch and a monkeypatched response whose
`read` raises after one chunk. In both cases pre-populate the destination with
`b"known-good"` and assert it remains unchanged. Also assert no temporary sibling
files remain.

```python
def test_download_source_hash_mismatch_preserves_existing_destination(tmp_path):
    source = tmp_path / "remote.txt"
    destination = tmp_path / "UnicodeData.txt"
    source.write_bytes(b"untrusted")
    destination.write_bytes(b"known-good")

    with pytest.raises(SourceIntegrityError):
        download_source(source.as_uri(), destination, "test", "fixture", expected_sha256="0" * 64)

    assert destination.read_bytes() == b"known-good"
    assert sorted(tmp_path.glob(".UnicodeData.txt.*.tmp")) == []
```

- [ ] **Step 2: Run source tests and verify the preservation test fails**

Run: `.venv/bin/python -m pytest tests/test_sources.py -v`

Expected: the checksum mismatch test shows the destination was overwritten.

- [ ] **Step 3: Implement validated temporary download and atomic replacement**

Create a named temporary file in `destination.parent`, stream the response into it,
close it, call `validate_sha256` on the temporary path, then call
`temporary_path.replace(destination)`. Use `finally` to unlink the temporary path
when it still exists. Return `register_local_source(destination, ...)` only after
replacement.

- [ ] **Step 4: Re-run source tests**

Run: `.venv/bin/python -m pytest tests/test_sources.py -v`

Expected: all source tests pass and no temporary files remain.

- [ ] **Step 5: Commit the download integrity change**

```bash
git add src/omniglyph/sources.py tests/test_sources.py
git commit -m "fix: preserve verified source downloads"
```

### Task 4: Harden Policy and Parameter Validation

**Files:**
- Modify: `src/omniglyph/policy_pack.py`
- Modify: `src/omniglyph/parameter_schema.py`
- Test: `tests/test_policy_pack.py`
- Test: `tests/test_parameter_schema.py`

- [ ] **Step 1: Add failing duplicate-ID and enum-type tests**

Add a second Policy Pack row with the same `intent_id` and expect a validation
error naming the duplicate row. Add enum assertions proving `True` does not match
`1`, while `1.0` continues to match numeric enum member `1`.

```python
def test_validate_parameters_distinguishes_boolean_and_numeric_enum_values():
    schema = {"type": "object", "properties": {"level": {"enum": [1]}}}

    assert validate_parameters({"level": True}, schema) == [
        {"path": "$.level", "rule": "enum", "message": "Value is not in the allowed enum."}
    ]
    assert validate_parameters({"level": 1.0}, schema) == []
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run: `.venv/bin/python -m pytest tests/test_policy_pack.py tests/test_parameter_schema.py -k 'duplicate or distinguishes' -v`

Expected: duplicate intent validation passes incorrectly and `True` satisfies `[1]`.

- [ ] **Step 3: Implement deterministic duplicate and JSON enum checks**

Track the first valid row number for every `intent_id` in `_validate_intents` and
append `intents.csv row N: duplicate intent_id X (first defined at row M)` for a
repeat. In parameter validation, replace direct membership with a recursive
`_json_values_equal` helper that treats booleans as distinct, treats integers and
floats as the same JSON number category, and recursively compares lists and objects.

- [ ] **Step 4: Run policy, parameter, and intent tests**

Run: `.venv/bin/python -m pytest tests/test_policy_pack.py tests/test_parameter_schema.py tests/test_language_security.py -v`

Expected: all selected tests pass.

- [ ] **Step 5: Commit validation hardening**

```bash
git add src/omniglyph/policy_pack.py src/omniglyph/parameter_schema.py tests/test_policy_pack.py tests/test_parameter_schema.py
git commit -m "fix: reject ambiguous policy values"
```

### Task 5: Coalesce DLP Redaction Ranges

**Files:**
- Modify: `src/omniglyph/language_security.py`
- Test: `tests/test_language_security.py`

- [ ] **Step 1: Add failing overlapping and adjacent redaction tests**

```python
@pytest.mark.parametrize(
    ("text", "terms"),
    [("floor price", ["floor price", "price"]), ("alphabeta", ["alpha", "beta"])],
)
def test_scan_output_dlp_coalesces_overlapping_or_adjacent_redactions(text, terms):
    report = scan_output_dlp(text, secret_terms=terms)

    assert report["summary"]["finding_count"] == 2
    assert report["redacted_text"] == "[REDACTED]"
```

- [ ] **Step 2: Run the new test and verify it fails**

Run: `.venv/bin/python -m pytest tests/test_language_security.py -k coalesces -v`

Expected: at least the overlapping case returns two redaction markers.

- [ ] **Step 3: Add interval coalescing before rendering**

Sort spans by start/end, merge a span when `start <= current_end`, and render one
marker per merged span. Do not change the original findings or their offsets.

- [ ] **Step 4: Run language security tests**

Run: `.venv/bin/python -m pytest tests/test_language_security.py -v`

Expected: all language security tests pass.

- [ ] **Step 5: Commit stable DLP redaction**

```bash
git add src/omniglyph/language_security.py tests/test_language_security.py
git commit -m "fix: coalesce overlapping DLP redactions"
```

### Task 6: Harden the MCP JSON-RPC Boundary

**Files:**
- Modify: `src/omniglyph/mcp_server.py`
- Test: `tests/test_mcp.py`

- [ ] **Step 1: Add failing protocol-boundary tests**

Cover a top-level array, wrong `jsonrpc`, non-string method, non-object `params`, and
non-object tool `arguments`. Add a stdio test containing an internal-error request
followed by `tools/list`; assert the first response preserves its ID and uses the
generic message `Internal error`, and the second request still succeeds.

```python
def test_handle_mcp_rejects_non_object_request():
    response = handle_mcp_request([])
    assert response == {
        "jsonrpc": "2.0",
        "id": None,
        "error": {"code": -32600, "message": "Invalid Request"},
    }
```

- [ ] **Step 2: Run focused MCP boundary tests and verify they fail**

Run: `.venv/bin/python -m pytest tests/test_mcp.py -k 'invalid_request or invalid_params or continues_after_internal_error' -v`

Expected: current code raises `AttributeError` for non-object containers or leaks raw exception text.

- [ ] **Step 3: Validate envelopes and sanitize stdio internal errors**

Change `handle_mcp_request` to accept `object`, reject non-dicts with `-32600`,
require JSON-RPC `2.0` and a string method, and validate optional `params` plus tool
`arguments` as objects before access. In `serve_stdio`, recover the request ID from
a parsed dict before dispatch and return `_error(request_id, -32603, "Internal error")`
for unexpected exceptions. Keep parse errors at `-32700`.

- [ ] **Step 4: Run all MCP tests and smoke test**

Run: `.venv/bin/python -m pytest tests/test_mcp.py -v`

Run: `PYTHON=.venv/bin/python bash scripts/mcp_smoke_test.sh .venv/bin/omniglyph-mcp`

Expected: all MCP tests pass and the same seventeen tools are reported.

- [ ] **Step 5: Commit MCP boundary hardening**

```bash
git add src/omniglyph/mcp_server.py tests/test_mcp.py
git commit -m "fix: validate MCP JSON-RPC boundaries"
```

### Task 7: Run Full Verification and Write the Closeout Report

**Files:**
- Create: `docs/superpowers/reviews/2026-07-16-project-release-safety-closeout.md`
- Modify: `docs/product/project-status.md`

- [ ] **Step 1: Run focused static and test verification**

Run: `.venv/bin/python -m pytest -q`

Run: `.venv/bin/python -m ruff check .`

Run: `.venv/bin/python -m mypy src`

Run: `bash scripts/privacy-scan.sh`

Expected: all commands exit `0`; record the exact test count in the report.

- [ ] **Step 2: Run the complete release gate**

Run: `PATH=.venv/bin:$PATH bash scripts/release_check.sh`

Expected: tests, Ruff, mypy, diff check, seventeen-tool MCP smoke, fresh build,
Twine metadata check, artifact audit, clean-wheel smoke, and demo check all pass.

- [ ] **Step 3: Write the closeout report with observed evidence**

Use sections `Executive Summary`, `Scope and Baseline`, `Findings Resolved`,
`Implementation`, `Verification Evidence`, `Compatibility`, `Remaining Risks`, and
`Publication Boundary`. Classify the atomic namespace replacement and source-file
preservation issues as high impact; classify ingestion ordering, policy ambiguity,
MCP error semantics, enum type confusion, and DLP rendering as medium or low based
on their blast radius. Record command outputs, not predictions.

- [ ] **Step 4: Link the report from project status**

Add the closeout path under `Current Closeout Reference` in
`docs/product/project-status.md`. Do not alter historical release evidence.

- [ ] **Step 5: Run documentation and diff checks**

Run: `rg -n 'T[B]D|T[O]DO|F[I]XME|P[L]ACEHOLDER|待[定]' docs/superpowers/reviews/2026-07-16-project-release-safety-closeout.md`

Expected: no matches.

Run: `git diff --check && git status --short`

Expected: no whitespace errors; only the intended closeout documents remain uncommitted.

- [ ] **Step 6: Commit closeout documentation**

```bash
git add docs/product/project-status.md docs/superpowers/reviews/2026-07-16-project-release-safety-closeout.md
git commit -m "docs: close project release safety review"
```

### Task 8: Final Independent Verification

**Files:**
- Verify only; no planned source edits.

- [ ] **Step 1: Inspect the complete branch diff**

Run: `git diff origin/main...HEAD --stat`

Run: `git diff origin/main...HEAD --check`

Expected: the diff contains the design, plan, focused runtime/tests, and closeout
documentation with no whitespace errors or unrelated files.

- [ ] **Step 2: Confirm clean state and release boundary**

Run: `git status --short`

Expected: empty output. Do not publish packages, push tags, or update registries.

- [ ] **Step 3: Prepare the user handoff**

Report the resolved findings, exact test/release evidence, commits, closeout report
path, and remaining risks. Explicitly state that TestPyPI, PyPI, MCP Registry, tags,
and production deployment were not changed.
