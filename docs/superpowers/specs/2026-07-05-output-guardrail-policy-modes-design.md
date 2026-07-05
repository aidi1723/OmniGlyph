# Output Guardrail Policy Modes v0.8.2 Design

## Objective

Output Guardrail Policy Modes makes `enforce_grounded_output` configurable without changing its default strict behavior.

Today the output guardrail blocks whenever generated output contains unknown or unapproved terms. That is safe, but too rigid for enterprise workflows where some unknown terms should route to review while known secret terms should stay blocked. v0.8.2 adds a small policy object that lets host systems choose `allow`, `review`, or `block` behavior for specific output-term classes.

## Scope

This batch adds:

- Optional `policy` input for `enforce_grounded_output`.
- Policy-aware decisions for unknown, unapproved, and secret terms.
- Severity summary derived from the strongest action.
- API and MCP support through existing guardrail surfaces.
- Tests and documentation updates.

This batch does not add:

- A new Guardrail Pack format.
- Automatic rewriting or redaction.
- ERP, CRM, email, or webhook integration.
- A general policy DSL.
- CLI changes.

## Policy Shape

Policy object:

```json
{
  "unknown_action": "review",
  "unapproved_action": "block",
  "secret_action": "block"
}
```

Allowed actions:

- `allow`
- `review`
- `block`

Default policy:

```json
{
  "unknown_action": "block",
  "unapproved_action": "block",
  "secret_action": "block"
}
```

The default preserves current strict-source-grounding behavior.

## Term Classes

Output validation currently reports `known`, `unknown`, and `unapproved` statuses. v0.8.2 adds policy use of sensitivity for known terms:

- `unknown`: no local term record exists.
- `unapproved`: term exists but `review_status` is not `approved`.
- `secret`: term exists, is approved, and has `sensitivity=secret`.
- `known`: term exists, is approved, and is not secret.

Secret terms remain known in `validate_output_terms`, but `enforce_grounded_output` can block or review them based on policy.

## Runtime Behavior

`validate_output_terms(repository, terms)` remains a reporting function and does not accept policy.

`enforce_grounded_output(repository, terms, actor_id=None, policy=None)` applies policy after validation:

1. Validate each term against the repository.
2. Classify each detail as `known`, `unknown`, `unapproved`, or `secret`.
3. Map each non-safe class to a configured action.
4. Final `decision` is the strongest action in this order: `block` > `review` > `allow`.
5. Final `status` remains `pass` if all terms are safe, otherwise `warn`.
6. Add `severity`:
   - `none` when final action is `allow` and no risky detail exists.
   - `low` when risky details are allowed by policy.
   - `medium` when final action is `review`.
   - `high` when final action is `block`.

Example review result:

```json
{
  "schema": "omniglyph.guardrail:0.1",
  "mode": "policy_source_grounding",
  "decision": "review",
  "status": "warn",
  "severity": "medium",
  "unknown": ["HS 7604.99X"],
  "limits": ["Unknown terms require review before output is trusted."]
}
```

## Error Handling

Invalid policy values should not crash runtime surfaces. Unknown actions fall back to `block`, and the result includes a policy warning:

```json
{
  "policy_warnings": ["unknown_action must be one of allow, block, review; using block."]
}
```

This keeps API and MCP calls deterministic and conservative.

## API and MCP

API:

- `POST /api/v1/guardrail/enforce-output` accepts optional `policy`.

MCP:

- `enforce_grounded_output` accepts optional `policy`.

Both surfaces return the same payload shape as Python.

## Compatibility

- Calling `enforce_grounded_output` with no policy keeps current `block` behavior for unknown and unapproved terms.
- Existing tests for strict blocking should continue to pass.
- `validate_output_terms` remains unchanged.
- API/MCP callers that do not send `policy` see the same result semantics, plus a new `severity` field.

## Testing

Focused tests:

- `tests/test_guardrail.py`
  - default unknown terms still block.
  - `unknown_action=review` returns `decision=review`.
  - `unknown_action=allow` returns `decision=allow` with `severity=low`.
  - unapproved terms can be reviewed or blocked by policy.
  - approved secret terms can be blocked by policy.
  - invalid action values fall back to block with `policy_warnings`.
- `tests/test_api.py`
  - API accepts policy and returns review.
- `tests/test_mcp.py`
  - MCP accepts policy and returns review.

Final verification:

```bash
scripts/release_check.sh
```

## Acceptance Criteria

- Default output guardrail behavior remains strict and backward compatible.
- Policy modes work across Python, API, and MCP.
- Risk details remain source-backed and auditable.
- Invalid policy inputs are handled conservatively.
- No new runtime dependencies are introduced.
- Full release gate passes before push.
