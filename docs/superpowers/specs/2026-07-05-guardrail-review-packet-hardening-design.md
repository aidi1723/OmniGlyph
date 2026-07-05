# Guardrail Review Packet Hardening v0.8.4 Design

## Objective

Guardrail Review Packet Hardening closes the remaining test and maintainability gaps from v0.8.3 without changing public behavior.

The v0.8.3 review packet is working and published across Python, API, MCP, and documentation. Code review identified two follow-up items: the packet tests do not directly lock `unapproved` and policy-`allow` branches, and action precedence is represented in two places. v0.8.4 adds focused branch coverage and uses one action precedence source for both final decisions and review-packet summaries.

## Scope

This batch adds:

- Focused tests for `review_packet` when an unapproved term is routed to review.
- Focused tests for `review_packet` when an unknown term is allowed by policy.
- A single action precedence constant used by both decision and summary logic.
- Maintenance log and changelog notes.

This batch does not add:

- New API, MCP, or CLI request fields.
- A new response schema version.
- New runtime dependencies.
- Automatic rewriting, redaction, persistence, queues, or external integrations.
- New policy modes or term classes.

## Runtime Behavior

Public behavior remains unchanged:

- `enforce_grounded_output` still returns `allow`, `review`, or `block`.
- `review_packet` still appears only when at least one risky term exists.
- `review_packet.summary.actions` remains ordered by decision strength: `block`, `review`, `allow`.
- `validate_output_terms` remains policy-free.

The internal implementation should replace duplicated precedence logic with one constant, for example:

```python
ACTION_PRECEDENCE = ("block", "review", "allow")
```

`_strongest_action(actions)` and `_review_packet_summary(groups)` should both use that constant. This keeps future action-order changes from drifting between decision and summary code.

## Tests

Focused tests in `tests/test_guardrail.py`:

- `test_enforce_grounded_output_review_packet_includes_unapproved_terms`
  - Seed a draft term.
  - Call `enforce_grounded_output(..., policy={"unapproved_action": "review"})`.
  - Assert `decision == "review"`.
  - Assert the packet group class is `unapproved`, action is `review`, reason is the unapproved reason, and term metadata includes canonical ID and `review_status`.
- `test_enforce_grounded_output_review_packet_records_allowed_unknown_terms`
  - Call `enforce_grounded_output(..., policy={"unknown_action": "allow"})`.
  - Assert `decision == "allow"` and `severity == "low"`.
  - Assert `review_packet.summary.actions == ["allow"]`.
  - Assert suggested host action is the fixed unsupported-term allow guidance.

Regression tests:

- Existing v0.8.3 review-packet tests continue to pass.
- Existing policy-mode tests continue to pass.
- API and MCP tests continue to pass without changes because the external payload shape is unchanged.

## Documentation

Only maintenance-level documentation changes are needed:

- `CHANGELOG.md`: add a hardening line for unapproved/allow review-packet coverage and shared action precedence.
- `docs/product/v0.8-maintenance-log.md`: add a v0.8.4 note under maintenance notes.

README, API, MCP, and architecture docs do not need behavior changes because payload shape and user-facing semantics are unchanged.

## Compatibility

- The response schema remains `omniglyph.guardrail:0.1`.
- Existing callers see the same payload shape.
- Existing strict defaults remain unchanged.
- Existing policy object keys and action values remain unchanged.
- No database, pack, or artifact format changes are introduced.

## Verification

Focused verification:

```bash
.venv/bin/python -m pytest tests/test_guardrail.py tests/test_api.py tests/test_mcp.py -q
.venv/bin/python -m ruff check src/omniglyph/guardrail.py tests/test_guardrail.py
```

Final verification:

```bash
scripts/release_check.sh
```

## Acceptance Criteria

- Unapproved review-packet behavior is directly covered by tests.
- Policy-allowed risky terms are directly covered by tests.
- Action precedence is represented by one shared constant.
- No public API/MCP/CLI behavior changes are introduced.
- Maintenance notes reflect the hardening batch.
- Full release gate passes before push.
