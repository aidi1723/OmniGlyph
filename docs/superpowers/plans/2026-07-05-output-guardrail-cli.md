# Output Guardrail CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `omniglyph enforce-output` as a JSON CLI wrapper around existing output guardrail enforcement.

**Architecture:** Keep runtime behavior in `omniglyph.guardrail` unchanged and add only CLI argument parsing, repository initialization, and JSON output in `src/omniglyph/cli.py`. Tests seed a temporary SQLite repository and run the CLI in a subprocess with `OMNIGLYPH_SQLITE_PATH`.

**Tech Stack:** Python 3.11, argparse, subprocess-based pytest tests, existing `GlyphRepository`, existing release gate `scripts/release_check.sh`.

---

## File Structure

- Modify: `src/omniglyph/cli.py`
  - Import `enforce_grounded_output`.
  - Add `enforce-output` subcommand with repeated `--term`, optional `--actor-id`, optional `--policy`.
  - Parse `--policy` as JSON object and use `parser.error` for invalid input.
  - Print the returned guardrail result as formatted JSON.
- Create: `tests/test_cli_guardrail.py`
  - Seed temporary domain repositories.
  - Run `python -m omniglyph.cli enforce-output` through subprocess.
  - Assert JSON output, policy handling, audit output, and invalid policy errors.
- Modify: `README.md`
  - Add an English CLI example in the output guardrail section.
- Modify: `README.zh-CN.md`
  - Add the matching Chinese CLI example.
- Modify: `CHANGELOG.md`
  - Add one v0.8.5 line.
- Modify: `docs/product/v0.8-maintenance-log.md`
  - Add one v0.8.5 maintenance note.

---

### Task 1: CLI Runtime and Tests

**Files:**
- Modify: `src/omniglyph/cli.py`
- Create: `tests/test_cli_guardrail.py`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/test_cli_guardrail.py`:

```python
import json
import os
import subprocess
import sys
from pathlib import Path

from omniglyph.domain_pack import parse_domain_pack
from omniglyph.repository import GlyphRepository, SourceSnapshot


def seeded_domain_database(tmp_path):
    database_path = tmp_path / "test.sqlite3"
    repository = GlyphRepository(database_path)
    repository.initialize()
    source_id = repository.add_source_snapshot(SourceSnapshot("Private Domain Pack", "file://domain", "fixture", "sha-domain", "private", "domain"))
    repository.insert_lexical_entries(list(parse_domain_pack(Path("tests/fixtures/domain_pack.csv"), "private_building_materials")), source_id)
    return database_path


def run_cli(tmp_path, *args):
    env = os.environ.copy()
    env["OMNIGLYPH_SQLITE_PATH"] = str(seeded_domain_database(tmp_path))
    return subprocess.run(
        [sys.executable, "-m", "omniglyph.cli", *args],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def test_enforce_output_cli_blocks_unknown_terms_by_default(tmp_path):
    result = run_cli(tmp_path, "enforce-output", "--term", "FOB", "--term", "HS 7604.99X")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["schema"] == "omniglyph.guardrail:0.1"
    assert payload["mode"] == "strict_source_grounding"
    assert payload["decision"] == "block"
    assert payload["unknown"] == ["HS 7604.99X"]
    assert payload["review_packet"]["summary"]["actions"] == ["block"]


def test_enforce_output_cli_accepts_policy_json(tmp_path):
    result = run_cli(
        tmp_path,
        "enforce-output",
        "--term",
        "FOB",
        "--term",
        "HS 7604.99X",
        "--policy",
        '{"unknown_action":"review"}',
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["mode"] == "policy_source_grounding"
    assert payload["decision"] == "review"
    assert payload["review_packet"]["summary"]["actions"] == ["review"]


def test_enforce_output_cli_includes_audit_for_actor_id(tmp_path):
    result = run_cli(
        tmp_path,
        "enforce-output",
        "--term",
        "FOB",
        "--actor-id",
        "agent:quote",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["decision"] == "allow"
    assert payload["audit"]["actor"] == {"id": "agent:quote"}
    assert payload["audit"]["action"] == "enforce_grounded_output"


def test_enforce_output_cli_rejects_invalid_policy_json(tmp_path):
    result = run_cli(tmp_path, "enforce-output", "--term", "FOB", "--policy", "{bad")

    assert result.returncode == 2
    assert "--policy must be a JSON object" in result.stderr


def test_enforce_output_cli_rejects_non_object_policy_json(tmp_path):
    result = run_cli(tmp_path, "enforce-output", "--term", "FOB", "--policy", "[]")

    assert result.returncode == 2
    assert "--policy must be a JSON object" in result.stderr
```

- [ ] **Step 2: Run tests and verify they fail for missing command**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_guardrail.py -q
```

Expected: tests fail because `enforce-output` is not a recognized CLI command.

- [ ] **Step 3: Add guardrail import**

In `src/omniglyph/cli.py`, add:

```python
from omniglyph.guardrail import enforce_grounded_output
```

- [ ] **Step 4: Add `enforce-output` parser**

In `main()`, after the existing `enforce-intent` parser block, add:

```python
    enforce_output = subcommands.add_parser("enforce-output")
    enforce_output.add_argument("--term", action="append", required=True)
    enforce_output.add_argument("--actor-id")
    enforce_output.add_argument("--policy")
```

- [ ] **Step 5: Add `enforce-output` dispatch**

In `main()`, after the existing `elif args.command == "enforce-intent":` block and before `lookup`, add:

```python
    elif args.command == "enforce-output":
        policy = None
        if args.policy is not None:
            try:
                policy = json.loads(args.policy)
            except json.JSONDecodeError as exc:
                parser.error(f"--policy must be a JSON object: {exc.msg}")
            if not isinstance(policy, dict):
                parser.error("--policy must be a JSON object")
        repository = GlyphRepository(settings.sqlite_path)
        repository.initialize()
        report = enforce_grounded_output(repository, args.term, actor_id=args.actor_id, policy=policy)
        print(json.dumps(report, ensure_ascii=False, indent=2))
```

- [ ] **Step 6: Run CLI guardrail tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_guardrail.py -q
```

Expected: all CLI guardrail tests pass.

- [ ] **Step 7: Run focused Ruff**

Run:

```bash
.venv/bin/python -m ruff check src/omniglyph/cli.py tests/test_cli_guardrail.py
```

Expected: `All checks passed!`

- [ ] **Step 8: Commit CLI runtime**

Run:

```bash
git add src/omniglyph/cli.py tests/test_cli_guardrail.py
git commit -m "feat: add output guardrail cli"
```

---

### Task 2: Documentation and Maintenance Notes

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/product/v0.8-maintenance-log.md`

- [ ] **Step 1: Update English README**

In the output guardrail section of `README.md`, after the paragraph that mentions `review_packet`, add:

````markdown
CLI workflows can call the same enforcement path:

```bash
omniglyph enforce-output --term FOB --term "HS 7604.99X" --policy '{"unknown_action":"review"}'
```
````

- [ ] **Step 2: Update Chinese README**

In the matching output guardrail section of `README.zh-CN.md`, after the paragraph that mentions `review_packet`, add:

````markdown
CLI 工作流也可以调用同一条输出守门路径：

```bash
omniglyph enforce-output --term FOB --term "HS 7604.99X" --policy '{"unknown_action":"review"}'
```
````

- [ ] **Step 3: Update changelog**

Add this line under the current unreleased v0.8 entries in `CHANGELOG.md`:

```markdown
- Add `omniglyph enforce-output` for local JSON output guardrail enforcement with optional policy and audit evidence.
```

- [ ] **Step 4: Update maintenance log**

Add this note under `## Maintenance Notes` in `docs/product/v0.8-maintenance-log.md`:

```markdown
- Output Guardrail CLI in v0.8.5 exposes `enforce_grounded_output` as `omniglyph enforce-output` with repeated `--term`, optional `--policy`, and optional `--actor-id`.
```

- [ ] **Step 5: Review doc diff**

Run:

```bash
git diff -- README.md README.zh-CN.md CHANGELOG.md docs/product/v0.8-maintenance-log.md
```

Expected: docs mention CLI usage only and do not claim API, MCP, or runtime behavior changed.

- [ ] **Step 6: Commit docs**

Run:

```bash
git add README.md README.zh-CN.md CHANGELOG.md docs/product/v0.8-maintenance-log.md
git commit -m "docs: document output guardrail cli"
```

---

### Task 3: Release Gate and Push

**Files:**
- Verify the whole repository.

- [ ] **Step 1: Run focused verification**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_guardrail.py tests/test_guardrail.py -q
.venv/bin/python -m ruff check src/omniglyph/cli.py tests/test_cli_guardrail.py
```

Expected:

- CLI and guardrail tests pass.
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

Expected: branch is ahead of origin by the v0.8.5 commits and has no uncommitted changes.

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
- Remaining risks. Expected remaining risk: `enforce-output` is an evidence command; shell workflows must inspect JSON to decide whether to fail on `block` or `review`.

---

## Self-Review

- Spec coverage: The plan covers CLI command shape, policy parsing, audit output, docs, maintenance notes, and release verification.
- Open-item scan: The plan contains no unresolved markers.
- Type consistency: The CLI command is consistently named `enforce-output`; the runtime function remains `enforce_grounded_output`.
- Scope boundary: The plan does not change API, MCP, guardrail runtime semantics, response schemas, or exit behavior for `block` / `review`.
