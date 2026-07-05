# Output Guardrail CLI v0.8.5 Design

## Objective

Output Guardrail CLI exposes the existing `enforce_grounded_output` runtime through the `omniglyph` command line.

Python, API, and MCP callers can already enforce source-grounded output decisions with policy modes and review packets. Local scripts, CI jobs, release workflows, and agent wrappers still need a direct CLI surface. v0.8.5 adds `omniglyph enforce-output` as a thin JSON-emitting wrapper around the existing guardrail runtime.

## Scope

This batch adds:

- A new CLI subcommand: `omniglyph enforce-output`.
- Repeated `--term` arguments for candidate output terms.
- Optional `--actor-id` for audit evidence.
- Optional `--policy` JSON object for existing output policy modes.
- JSON output matching `enforce_grounded_output`.
- CLI tests and user-facing docs.

This batch does not add:

- New guardrail policy keys or action values.
- New API or MCP behavior.
- New response schema fields.
- Automatic rewriting, redaction, persistence, queues, or external integrations.
- Database writes beyond reading the configured local SQLite repository.
- New runtime dependencies.

## CLI Shape

Example:

```bash
omniglyph enforce-output \
  --term FOB \
  --term "HS 7604.99X" \
  --actor-id agent:quote \
  --policy '{"unknown_action":"review"}'
```

Output is formatted JSON:

```json
{
  "schema": "omniglyph.guardrail:0.1",
  "mode": "policy_source_grounding",
  "decision": "review",
  "status": "warn",
  "severity": "medium",
  "known": {
    "FOB": "trade:fob"
  },
  "unknown": ["HS 7604.99X"],
  "review_packet": {
    "status": "needs_review"
  }
}
```

The output is the exact dictionary returned by `enforce_grounded_output`, serialized with `json.dumps(..., ensure_ascii=False, indent=2)`.

## Arguments

`--term`

- May be provided more than once.
- Required at least once.
- Each value is passed as one candidate term.
- The CLI does not split comma-separated terms or parse model output text.

`--actor-id`

- Optional string.
- Passed to `enforce_grounded_output` unchanged.
- When present, the result includes the existing `audit` payload.

`--policy`

- Optional JSON string.
- Must parse as a JSON object.
- Passed to `enforce_grounded_output` unchanged.
- Invalid JSON exits through `argparse` error handling with a non-zero status.
- JSON values that are not objects also exit through `argparse` error handling.
- Invalid action values inside the object remain runtime policy warnings, preserving v0.8.2 behavior.

## Runtime Behavior

The command performs these steps:

1. Parse CLI arguments.
2. Parse `--policy` when present.
3. Initialize `GlyphRepository(settings.sqlite_path)`.
4. Call `repository.initialize()`.
5. Call `enforce_grounded_output(repository, args.term, actor_id=args.actor_id, policy=policy)`.
6. Print formatted JSON.

The command does not infer terms, load lexicon packs, mutate output text, or write review queues.

## Exit Behavior

- `0` when CLI parsing succeeds and `enforce_grounded_output` returns a result.
- Non-zero through `argparse` when required `--term` is missing.
- Non-zero through `argparse` when `--policy` is invalid JSON.
- Non-zero through `argparse` when `--policy` parses to a non-object value.

Guardrail decisions such as `block` or `review` do not make the CLI exit non-zero in v0.8.5. The command is an evidence generator; shell workflows can inspect JSON and decide their own failure policy.

## Compatibility

- Existing CLI commands remain unchanged.
- API and MCP surfaces remain unchanged.
- `enforce_grounded_output` runtime remains unchanged.
- The response schema remains `omniglyph.guardrail:0.1`.
- No new dependencies are introduced.

## Testing

Focused tests:

- `tests/test_cli_guardrail.py`
  - CLI blocks unknown terms by default and emits JSON with `decision=block`.
  - CLI accepts policy JSON and emits `decision=review`.
  - CLI includes audit payload when `--actor-id` is present.
  - CLI rejects invalid policy JSON.
  - CLI rejects policy JSON that is not an object.

Existing guardrail/API/MCP tests should continue to pass because runtime behavior is not changed.

## Documentation

Update:

- `README.md`: add an `enforce-output` example near output guardrail docs.
- `README.zh-CN.md`: add the same example in Chinese.
- `docs/api.md` or `docs/mcp-tools.md` do not need changes because API/MCP behavior is unchanged.
- `docs/product/v0.8-maintenance-log.md`: record v0.8.5 CLI surface.
- `CHANGELOG.md`: add v0.8.5 line.

## Verification

Focused verification:

```bash
.venv/bin/python -m pytest tests/test_cli_guardrail.py tests/test_guardrail.py -q
.venv/bin/python -m ruff check src/omniglyph/cli.py tests/test_cli_guardrail.py
```

Final verification:

```bash
scripts/release_check.sh
```

## Acceptance Criteria

- `omniglyph enforce-output` returns the same JSON evidence as `enforce_grounded_output`.
- CLI policy parsing is deterministic and rejects malformed or non-object JSON.
- `block` and `review` decisions do not automatically fail the command.
- No API, MCP, or guardrail runtime behavior changes are introduced.
- Docs and maintenance logs describe the new CLI surface.
- Full release gate passes before push.
