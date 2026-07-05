# Guardrail Review Packet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic `review_packet` evidence to output guardrail enforcement so hosts can route unknown, unapproved, and secret terms to review without inferring from raw details.

**Architecture:** Keep the change inside `src/omniglyph/guardrail.py` and let API/MCP surfaces inherit the payload through their existing passthrough calls. `review_packet` is additive, derived from existing validation details and policy actions, and omitted for fully safe output.

**Tech Stack:** Python 3.11, pytest, FastAPI TestClient, existing MCP JSON-RPC helpers, Ruff, local `scripts/release_check.sh`.

---

## File Structure

- Modify: `src/omniglyph/guardrail.py`
  - Add deterministic helpers for review packet grouping, term serialization, reason strings, host action strings, and summary derivation.
  - Add `review_packet` to `enforce_grounded_output` results when risky terms exist.
- Modify: `tests/test_guardrail.py`
  - Add focused Python runtime tests for default block packets, review packets, safe omission, mixed grouping, and deduplication.
- Modify: `tests/test_api.py`
  - Assert API response exposes the same packet shape.
- Modify: `tests/test_mcp.py`
  - Assert MCP response exposes the same packet shape.
- Modify: `docs/api.md`
  - Document `review_packet` in `POST /api/v1/guardrail/enforce-output`.
- Modify: `docs/mcp-tools.md`
  - Document `review_packet` in MCP `enforce_grounded_output`.
- Modify: `docs/architecture/deterministic-mcp-guardrail.md`
  - Record the review-packet role in the deterministic guardrail flow.
- Modify: `docs/product/v0.8-maintenance-log.md`
  - Add v0.8.3 maintenance note and focused verification command.
- Modify: `CHANGELOG.md`
  - Add the v0.8.3 additive feature line.
- Modify: `README.md`
  - Mention review packet evidence in the output guardrail section.
- Modify: `README.zh-CN.md`
  - Mirror the README update in Chinese.

---

### Task 1: Core Review Packet Runtime

**Files:**
- Modify: `tests/test_guardrail.py`
- Modify: `src/omniglyph/guardrail.py`

- [ ] **Step 1: Add failing tests for core packet behavior**

Append these tests to `tests/test_guardrail.py`:

```python
def test_enforce_grounded_output_includes_review_packet_for_default_unknown_block(tmp_path):
    repository = seeded_repository(tmp_path)

    result = enforce_grounded_output(repository, ["FOB", "HS 7604.99X"])

    assert result["decision"] == "block"
    assert result["review_packet"] == {
        "status": "needs_review",
        "summary": {
            "term_count": 1,
            "group_count": 1,
            "actions": ["block"],
            "classes": ["unknown"],
        },
        "groups": [
            {
                "class": "unknown",
                "action": "block",
                "reason": "Term is not present in the local fact base.",
                "suggested_host_action": "Block delivery until the term is reviewed, removed, or added to an approved source.",
                "terms": [{"term": "HS 7604.99X", "canonical_id": None}],
            }
        ],
    }


def test_enforce_grounded_output_review_packet_reflects_review_policy(tmp_path):
    repository = seeded_repository(tmp_path)

    result = enforce_grounded_output(repository, ["HS 7604.99X"], policy={"unknown_action": "review"})

    assert result["decision"] == "review"
    assert result["review_packet"]["summary"]["actions"] == ["review"]
    assert result["review_packet"]["groups"][0]["action"] == "review"
    assert result["review_packet"]["groups"][0]["suggested_host_action"] == "Route to human review or regenerate with verified terms only."


def test_enforce_grounded_output_omits_review_packet_for_safe_output(tmp_path):
    repository = seeded_repository(tmp_path)

    result = enforce_grounded_output(repository, ["FOB", "tempered glass"])

    assert result["decision"] == "allow"
    assert "review_packet" not in result


def test_enforce_grounded_output_groups_mixed_unknown_and_secret_terms(tmp_path):
    source = tmp_path / "terms.csv"
    source.write_text(
        "term,canonical_id,entry_type,language,aliases,definition,traits,sensitivity,review_status\n"
        'Floor Price,company:floor_price,confidential_term,en,,Internal floor price,"{}",secret,approved\n',
        encoding="utf-8",
    )
    repository = seeded_repository(tmp_path)
    source_id = repository.add_source_snapshot(SourceSnapshot("Private Domain Pack", "file://secret", "fixture", "sha-secret", "private", "domain"))
    repository.insert_lexical_entries(list(parse_domain_pack(source, "private_acme")), source_id)

    result = enforce_grounded_output(
        repository,
        ["HS 7604.99X", "Floor Price"],
        policy={"unknown_action": "review", "secret_action": "block"},
    )

    assert result["decision"] == "block"
    assert result["review_packet"]["summary"] == {
        "term_count": 2,
        "group_count": 2,
        "actions": ["block", "review"],
        "classes": ["unknown", "secret"],
    }
    assert result["review_packet"]["groups"][0]["class"] == "unknown"
    assert result["review_packet"]["groups"][0]["action"] == "review"
    assert result["review_packet"]["groups"][0]["terms"] == [{"term": "HS 7604.99X", "canonical_id": None}]
    assert result["review_packet"]["groups"][1]["class"] == "secret"
    assert result["review_packet"]["groups"][1]["action"] == "block"
    assert result["review_packet"]["groups"][1]["terms"][0]["term"] == "Floor Price"
    assert result["review_packet"]["groups"][1]["terms"][0]["canonical_id"] == "company:floor_price"
    assert result["review_packet"]["groups"][1]["terms"][0]["sensitivity"] == "secret"
    assert result["review_packet"]["groups"][1]["terms"][0]["source_name"] == "Private Domain Pack"


def test_enforce_grounded_output_deduplicates_repeated_risky_terms_in_review_packet(tmp_path):
    repository = seeded_repository(tmp_path)

    result = enforce_grounded_output(repository, ["HS 7604.99X", "HS 7604.99X"])

    assert result["unknown"] == ["HS 7604.99X", "HS 7604.99X"]
    assert result["review_packet"]["summary"]["term_count"] == 1
    assert result["review_packet"]["groups"][0]["terms"] == [{"term": "HS 7604.99X", "canonical_id": None}]
```

- [ ] **Step 2: Run tests and verify they fail for missing packet**

Run:

```bash
.venv/bin/python -m pytest tests/test_guardrail.py -q
```

Expected: the newly added tests fail with `KeyError: 'review_packet'` or an assertion that `review_packet` is missing.

- [ ] **Step 3: Implement minimal review packet helpers**

Modify `src/omniglyph/guardrail.py` by adding constants after `DEFAULT_POLICY`:

```python
RISKY_STATUS_ORDER = ("unknown", "unapproved", "secret")
ACTION_STRENGTH_ORDER = ("block", "review", "allow")

REVIEW_REASONS = {
    "unknown": "Term is not present in the local fact base.",
    "unapproved": "Term exists in the local fact base but is not approved.",
    "secret": "Term is approved but marked secret.",
}

SUGGESTED_HOST_ACTIONS = {
    ("unknown", "block"): "Block delivery until the term is reviewed, removed, or added to an approved source.",
    ("unknown", "review"): "Route to human review or regenerate with verified terms only.",
    ("unknown", "allow"): "Deliver only if the host policy accepts unsupported terms.",
    ("unapproved", "block"): "Block delivery until the term is approved or removed.",
    ("unapproved", "review"): "Route to the source owner or reviewer before delivery.",
    ("unapproved", "allow"): "Deliver only if the host policy accepts unapproved terms.",
    ("secret", "block"): "Block delivery and remove or redact the sensitive term.",
    ("secret", "review"): "Route to an authorized reviewer before delivery.",
    ("secret", "allow"): "Deliver only if the host policy explicitly permits sensitive terms.",
}
```

Add `review_packet` assembly in `enforce_grounded_output` after `limits` is computed:

```python
    review_packet = _review_packet_for_details(details, actions)
```

Add it to the result only when present:

```python
    if review_packet:
        result["review_packet"] = review_packet
```

Add these helper functions before `_audit_payload`:

```python
def _review_packet_for_details(details: list[dict], actions: list[str]) -> dict | None:
    groups = []
    for status in RISKY_STATUS_ORDER:
        terms = []
        action = None
        seen_terms = set()
        for detail, detail_action in zip(details, actions, strict=True):
            if detail["status"] != status:
                continue
            if detail["term"] in seen_terms:
                continue
            seen_terms.add(detail["term"])
            action = detail_action
            terms.append(_review_term_payload(detail))
        if not terms or action is None:
            continue
        groups.append(
            {
                "class": status,
                "action": action,
                "reason": REVIEW_REASONS[status],
                "suggested_host_action": SUGGESTED_HOST_ACTIONS[(status, action)],
                "terms": terms,
            }
        )
    if not groups:
        return None
    return {
        "status": "needs_review",
        "summary": _review_packet_summary(groups),
        "groups": groups,
    }


def _review_term_payload(detail: dict) -> dict:
    payload = {
        "term": detail["term"],
        "canonical_id": detail.get("canonical_id"),
    }
    for key in ("entry_type", "sensitivity", "review_status", "source_id", "source_name"):
        if key in detail:
            payload[key] = detail[key]
    return payload


def _review_packet_summary(groups: list[dict]) -> dict:
    actions = []
    group_actions = {group["action"] for group in groups}
    for action in ACTION_STRENGTH_ORDER:
        if action in group_actions:
            actions.append(action)
    return {
        "term_count": sum(len(group["terms"]) for group in groups),
        "group_count": len(groups),
        "actions": actions,
        "classes": [group["class"] for group in groups],
    }
```

- [ ] **Step 4: Run core tests and verify green**

Run:

```bash
.venv/bin/python -m pytest tests/test_guardrail.py -q
```

Expected: all guardrail tests pass.

- [ ] **Step 5: Run Ruff for touched runtime**

Run:

```bash
.venv/bin/python -m ruff check src/omniglyph/guardrail.py tests/test_guardrail.py
```

Expected: `All checks passed!`

- [ ] **Step 6: Commit core runtime**

Run:

```bash
git add src/omniglyph/guardrail.py tests/test_guardrail.py
git commit -m "feat: add guardrail review packet"
```

---

### Task 2: API and MCP Surface Tests

**Files:**
- Modify: `tests/test_api.py`
- Modify: `tests/test_mcp.py`

- [ ] **Step 1: Add failing API assertion**

In `tests/test_api.py`, update `test_guardrail_enforce_output_endpoint_accepts_policy_modes` by adding these assertions after `assert payload["severity"] == "medium"`:

```python
    assert payload["review_packet"]["summary"] == {
        "term_count": 1,
        "group_count": 1,
        "actions": ["review"],
        "classes": ["unknown"],
    }
    assert payload["review_packet"]["groups"][0]["suggested_host_action"] == "Route to human review or regenerate with verified terms only."
```

- [ ] **Step 2: Add failing MCP assertion**

In `tests/test_mcp.py`, update `test_handle_mcp_enforce_grounded_output_accepts_policy_modes` by adding these assertions after `assert payload["severity"] == "medium"`:

```python
    assert payload["review_packet"]["summary"] == {
        "term_count": 1,
        "group_count": 1,
        "actions": ["review"],
        "classes": ["unknown"],
    }
    assert payload["review_packet"]["groups"][0]["terms"] == [{"term": "HS 7604.99X", "canonical_id": None}]
```

- [ ] **Step 3: Verify API/MCP tests pass through runtime payload**

Run:

```bash
.venv/bin/python -m pytest tests/test_api.py::test_guardrail_enforce_output_endpoint_accepts_policy_modes tests/test_mcp.py::test_handle_mcp_enforce_grounded_output_accepts_policy_modes -q
```

Expected after Task 1 implementation: both tests pass because API and MCP already return `enforce_grounded_output` payloads unchanged.

- [ ] **Step 4: Run focused API/MCP guardrail tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_guardrail.py tests/test_api.py tests/test_mcp.py -q
```

Expected: all selected tests pass.

- [ ] **Step 5: Commit API/MCP tests**

Run:

```bash
git add tests/test_api.py tests/test_mcp.py
git commit -m "test: cover guardrail review packet surfaces"
```

---

### Task 3: Documentation and Maintenance Log

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/api.md`
- Modify: `docs/mcp-tools.md`
- Modify: `docs/architecture/deterministic-mcp-guardrail.md`
- Modify: `docs/product/v0.8-maintenance-log.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update CHANGELOG**

Add this line under the current unreleased v0.8 entries in `CHANGELOG.md`:

```markdown
- Add guardrail review packets that group unknown, unapproved, and secret output terms into deterministic host-review evidence.
```

- [ ] **Step 2: Update English README**

In the Output Guardrail section of `README.md`, add one sentence after the policy example paragraph:

```markdown
When risky terms are present, `enforce_grounded_output` also returns a `review_packet` that groups unknown, unapproved, and secret terms into deterministic host-review evidence.
```

- [ ] **Step 3: Update Chinese README**

In the matching Output Guardrail section of `README.zh-CN.md`, add:

```markdown
当输出中存在风险术语时，`enforce_grounded_output` 还会返回 `review_packet`，把未知、未批准和敏感术语整理成确定性的人工复核证据。
```

- [ ] **Step 4: Update API docs**

In `docs/api.md`, extend the `POST /api/v1/guardrail/enforce-output` response example with:

```json
  "review_packet": {
    "status": "needs_review",
    "summary": {
      "term_count": 1,
      "group_count": 1,
      "actions": ["block"],
      "classes": ["unknown"]
    },
    "groups": [
      {
        "class": "unknown",
        "action": "block",
        "reason": "Term is not present in the local fact base.",
        "suggested_host_action": "Block delivery until the term is reviewed, removed, or added to an approved source.",
        "terms": [{"term": "HS 7604.99X", "canonical_id": null}]
      }
    ]
  }
```

Add this sentence after the response example:

```markdown
`review_packet` is omitted when every checked term is approved and non-secret.
```

- [ ] **Step 5: Update MCP docs**

In `docs/mcp-tools.md`, add the same `review_packet` field to the `enforce_grounded_output` output example and add:

```markdown
The packet is derived from `details` and policy actions; MCP clients can use it to build review queues without parsing free text.
```

- [ ] **Step 6: Update deterministic guardrail architecture doc**

In `docs/architecture/deterministic-mcp-guardrail.md`, add:

```markdown
v0.8.3 adds `review_packet` as an additive evidence layer. It groups risky terms by class and policy action, but it does not rewrite output, persist queues, or call external systems.
```

- [ ] **Step 7: Update maintenance log**

In `docs/product/v0.8-maintenance-log.md`, add a maintenance note:

```markdown
- Guardrail Review Packet in v0.8.3 adds deterministic grouped review evidence for unknown, unapproved, and secret output terms without introducing persistence, rewriting, or external integrations.
```

Add focused tests to the checklist:

```bash
.venv/bin/python -m pytest tests/test_guardrail.py tests/test_api.py tests/test_mcp.py -q
```

- [ ] **Step 8: Review doc diffs**

Run:

```bash
git diff -- README.md README.zh-CN.md docs/api.md docs/mcp-tools.md docs/architecture/deterministic-mcp-guardrail.md docs/product/v0.8-maintenance-log.md CHANGELOG.md
```

Expected: documentation describes `review_packet` as additive evidence only, with no claims of automatic rewrite or external integration.

- [ ] **Step 9: Commit docs**

Run:

```bash
git add README.md README.zh-CN.md docs/api.md docs/mcp-tools.md docs/architecture/deterministic-mcp-guardrail.md docs/product/v0.8-maintenance-log.md CHANGELOG.md
git commit -m "docs: document guardrail review packet"
```

---

### Task 4: Release Gate and Push

**Files:**
- Verify the whole repository.

- [ ] **Step 1: Run Ruff**

Run:

```bash
.venv/bin/python -m ruff check .
```

Expected: `All checks passed!`

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

Expected: branch is ahead of origin by the new v0.8.3 commits and has no uncommitted changes.

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
- Any unresolved risk. The expected unresolved risk is that `review_packet` is evidence only; real queues, rewrite flows, and ERP/email integrations remain host responsibilities.

---

## Self-Review

- Spec coverage: The plan implements the v0.8.3 spec fields, grouping rules, API/MCP exposure, docs, and release verification.
- Open-item scan: The plan contains no unresolved markers.
- Type consistency: The runtime field is consistently named `review_packet`; groups use `class`, `action`, `reason`, `suggested_host_action`, and `terms`.
- Scope boundary: The plan does not add persistence, automatic rewriting, redaction, external calls, or a new policy DSL.
