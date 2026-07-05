# Guardrail Review Packet Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden v0.8.3 review packets by adding missing branch coverage and using one shared action precedence source.

**Architecture:** Keep all behavior in `src/omniglyph/guardrail.py`; no API, MCP, CLI, schema, or payload changes are introduced. Add focused tests in `tests/test_guardrail.py`, then update only maintenance-level docs.

**Tech Stack:** Python 3.11, pytest, Ruff, existing local release gate `scripts/release_check.sh`.

---

## File Structure

- Modify: `tests/test_guardrail.py`
  - Add direct branch coverage for `unapproved` review-packet groups.
  - Add direct branch coverage for policy-allowed unknown terms in review packets.
- Modify: `src/omniglyph/guardrail.py`
  - Replace duplicated action precedence with one shared `ACTION_PRECEDENCE` tuple.
  - Use the same precedence in `_strongest_action()` and `_review_packet_summary()`.
- Modify: `CHANGELOG.md`
  - Add one v0.8.4 hardening line.
- Modify: `docs/product/v0.8-maintenance-log.md`
  - Add one v0.8.4 maintenance note.

---

### Task 1: Review Packet Branch Coverage and Precedence Cleanup

**Files:**
- Modify: `tests/test_guardrail.py`
- Modify: `src/omniglyph/guardrail.py`

- [ ] **Step 1: Add failing tests for missing review-packet branches**

Append these tests to `tests/test_guardrail.py`:

```python
def test_enforce_grounded_output_review_packet_includes_unapproved_terms(tmp_path):
    source = tmp_path / "terms.csv"
    source.write_text(
        "term,canonical_id,entry_type,language,aliases,definition,traits,sensitivity,review_status\n"
        'Draft Spec,company:draft_spec,product_spec,en,,Draft only,"{}",normal,draft\n',
        encoding="utf-8",
    )
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    source_id = repository.add_source_snapshot(SourceSnapshot("Private Domain Pack", "file://domain", "fixture", "sha-draft", "private", "domain"))
    repository.insert_lexical_entries(list(parse_domain_pack(source, "private_acme")), source_id)

    result = enforce_grounded_output(repository, ["Draft Spec"], policy={"unapproved_action": "review"})

    assert result["decision"] == "review"
    assert result["review_packet"]["summary"] == {
        "term_count": 1,
        "group_count": 1,
        "actions": ["review"],
        "classes": ["unapproved"],
    }
    assert result["review_packet"]["groups"][0] == {
        "class": "unapproved",
        "action": "review",
        "reason": "Term exists in the local fact base but is not approved.",
        "suggested_host_action": "Route to the source owner or reviewer before delivery.",
        "terms": [
            {
                "term": "Draft Spec",
                "canonical_id": "company:draft_spec",
                "entry_type": "product_spec",
                "sensitivity": "normal",
                "review_status": "draft",
                "source_id": source_id,
                "source_name": "Private Domain Pack",
            }
        ],
    }


def test_enforce_grounded_output_review_packet_records_allowed_unknown_terms(tmp_path):
    repository = seeded_repository(tmp_path)

    result = enforce_grounded_output(repository, ["HS 7604.99X"], policy={"unknown_action": "allow"})

    assert result["decision"] == "allow"
    assert result["severity"] == "low"
    assert result["review_packet"]["summary"] == {
        "term_count": 1,
        "group_count": 1,
        "actions": ["allow"],
        "classes": ["unknown"],
    }
    assert result["review_packet"]["groups"][0] == {
        "class": "unknown",
        "action": "allow",
        "reason": "Term is not present in the local fact base.",
        "suggested_host_action": "Deliver only if the host policy accepts unsupported terms.",
        "terms": [{"term": "HS 7604.99X", "canonical_id": None}],
    }
```

- [ ] **Step 2: Run tests and confirm current behavior**

Run:

```bash
.venv/bin/python -m pytest tests/test_guardrail.py::test_enforce_grounded_output_review_packet_includes_unapproved_terms tests/test_guardrail.py::test_enforce_grounded_output_review_packet_records_allowed_unknown_terms -q
```

Expected: the tests may already pass because v0.8.3 implementation supports these branches. If they pass, record that this is branch-locking coverage rather than a red failure. Continue to the precedence cleanup because that is the behavior-preserving code change in this task.

- [ ] **Step 3: Replace duplicated precedence constants**

Modify `src/omniglyph/guardrail.py`.

Replace:

```python
ACTION_STRENGTH_ORDER = ("block", "review", "allow")
```

with:

```python
ACTION_PRECEDENCE = ("block", "review", "allow")
```

Replace `_strongest_action` with:

```python
def _strongest_action(actions: list[str]) -> str:
    for action in ACTION_PRECEDENCE:
        if action in actions:
            return action
    return "allow"
```

Replace the loop in `_review_packet_summary`:

```python
    for action in ACTION_STRENGTH_ORDER:
```

with:

```python
    for action in ACTION_PRECEDENCE:
```

- [ ] **Step 4: Run focused guardrail tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_guardrail.py -q
```

Expected: all guardrail tests pass.

- [ ] **Step 5: Run focused Ruff**

Run:

```bash
.venv/bin/python -m ruff check src/omniglyph/guardrail.py tests/test_guardrail.py
```

Expected: `All checks passed!`

- [ ] **Step 6: Commit runtime hardening**

Run:

```bash
git add src/omniglyph/guardrail.py tests/test_guardrail.py
git commit -m "test: harden guardrail review packet branches"
```

---

### Task 2: Maintenance Documentation

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `docs/product/v0.8-maintenance-log.md`

- [ ] **Step 1: Update changelog**

Add this line under the current unreleased v0.8 entries in `CHANGELOG.md`:

```markdown
- Harden guardrail review packets with unapproved and policy-allowed branch coverage plus shared action precedence.
```

- [ ] **Step 2: Update maintenance log**

Add this note under `## Maintenance Notes` in `docs/product/v0.8-maintenance-log.md`:

```markdown
- Guardrail Review Packet Hardening in v0.8.4 adds direct `unapproved` and policy-`allow` branch coverage and consolidates action precedence into one runtime constant.
```

- [ ] **Step 3: Review doc diff**

Run:

```bash
git diff -- CHANGELOG.md docs/product/v0.8-maintenance-log.md
```

Expected: only the two maintenance-level notes changed; no user-facing payload claims changed.

- [ ] **Step 4: Commit docs**

Run:

```bash
git add CHANGELOG.md docs/product/v0.8-maintenance-log.md
git commit -m "docs: record guardrail review packet hardening"
```

---

### Task 3: Release Gate and Push

**Files:**
- Verify the whole repository.

- [ ] **Step 1: Run focused verification**

Run:

```bash
.venv/bin/python -m pytest tests/test_guardrail.py tests/test_api.py tests/test_mcp.py -q
.venv/bin/python -m ruff check src/omniglyph/guardrail.py tests/test_guardrail.py
```

Expected:

- Guardrail/API/MCP focused tests pass.
- Ruff reports `All checks passed!`

- [ ] **Step 2: Run full release gate**

Run:

```bash
scripts/release_check.sh
```

Expected:

- pytest reports all tests passed.
- Ruff reports no issues.
- MCP tools smoke check passes.
- package build succeeds.
- artifact audit passes.
- wheel smoke passes.
- demo output check passes.

- [ ] **Step 3: Inspect final git state**

Run:

```bash
git status --short --branch
git log --oneline -8
```

Expected: branch is ahead of origin by the v0.8.4 commits and has no uncommitted changes.

- [ ] **Step 4: Push to GitHub**

Run:

```bash
git push
```

Expected: `docs/logosgate-belief-whitepaper` updates on `https://github.com/aidi1723/OmniGlyph.git`.

- [ ] **Step 5: Final handoff**

Report:

- New commits.
- Verification commands and observed pass output.
- GitHub push target.
- Remaining risks. Expected remaining risk: this batch hardens existing behavior only; CLI exposure and rewrite suggestions remain future work.

---

## Self-Review

- Spec coverage: The plan covers missing `unapproved` and policy-`allow` review-packet tests, shared action precedence, maintenance notes, and release verification.
- Open-item scan: The plan contains no unresolved markers.
- Type consistency: The shared constant is consistently named `ACTION_PRECEDENCE`.
- Scope boundary: The plan does not change API, MCP, CLI, response schema, external integrations, or payload semantics.
