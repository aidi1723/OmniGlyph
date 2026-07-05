# Guardrail Review Packet v0.8.3 Design

## Objective

Guardrail Review Packet makes `enforce_grounded_output` easier to operate after it returns `review` or `block`.

v0.8.2 added policy modes for unknown, unapproved, and secret terms. That gives host systems the right decision, but a caller still has to inspect `details`, infer why each term needs attention, and build its own review queue payload. v0.8.3 adds a deterministic `review_packet` summary that groups risky terms by class and action so API, MCP, and Python callers can route review work without guessing.

## Scope

This batch adds:

- A `review_packet` field to `enforce_grounded_output` results when at least one risky term exists.
- Grouped review evidence for `unknown`, `unapproved`, and `secret` terms.
- Per-group action, reason, suggested host action, and affected terms.
- Source and canonical metadata when the repository has it.
- API and MCP payload documentation updates.
- Tests for Python, API, and MCP surfaces.

This batch does not add:

- Automatic output rewriting.
- Redaction or mutation of generated text.
- Persistent review queues.
- ERP, CRM, email, webhook, or ticket-system integration.
- A new Guardrail Pack format or policy DSL.
- External network calls.

## Review Packet Shape

`review_packet` is a runtime evidence object, not a workflow engine.

Example:

```json
{
  "status": "needs_review",
  "summary": {
    "term_count": 2,
    "group_count": 2,
    "actions": ["block", "review"],
    "classes": ["unknown", "secret"]
  },
  "groups": [
    {
      "class": "unknown",
      "action": "review",
      "reason": "Term is not present in the local fact base.",
      "suggested_host_action": "Route to human review or regenerate with verified terms only.",
      "terms": [
        {
          "term": "HS 7604.99X",
          "canonical_id": null
        }
      ]
    },
    {
      "class": "secret",
      "action": "block",
      "reason": "Term is approved but marked secret.",
      "suggested_host_action": "Block delivery and remove or redact the sensitive term.",
      "terms": [
        {
          "term": "Floor Price",
          "canonical_id": "company:floor_price",
          "entry_type": "confidential_term",
          "sensitivity": "secret",
          "review_status": "approved",
          "source_id": "...",
          "source_name": "Private Domain Pack"
        }
      ]
    }
  ]
}
```

The top-level `decision`, `severity`, `limits`, `details`, `known`, `unknown`, `source_ids`, and optional `audit` fields remain the source of truth for existing callers.

## Runtime Behavior

`validate_output_terms(repository, terms)` remains unchanged. It reports known, unknown, and unapproved terms without policy.

`enforce_grounded_output(repository, terms, actor_id=None, policy=None)` keeps the v0.8.2 decision flow:

1. Validate terms.
2. Classify details as `known`, `unknown`, `unapproved`, or `secret`.
3. Map non-safe classes to policy actions.
4. Compute strongest decision.
5. Compute limits and severity.
6. Build `review_packet` when any detail class is `unknown`, `unapproved`, or `secret`.

Fully safe output does not include `review_packet`. This keeps the success payload compact.

## Term Classes

Review packet groups use the same classes as policy modes:

- `unknown`: no local term record exists.
- `unapproved`: term exists but `review_status` is not `approved`.
- `secret`: term exists, is approved, and has `sensitivity=secret`.

`known` terms are not included in `review_packet` because they do not require host action.

## Grouping Rules

Groups are deterministic:

1. Preserve class priority: `unknown`, `unapproved`, `secret`.
2. Within each class, use the action configured by policy.
3. Preserve input term order within each group.
4. Omit empty groups.
5. Deduplicate repeated terms within the same class while preserving first-seen order.

The summary fields are derived from groups:

- `term_count`: total risky terms included after deduplication.
- `group_count`: number of non-empty groups.
- `actions`: unique group actions ordered by decision strength: `block`, `review`, `allow`.
- `classes`: group classes in emitted order.

## Suggested Host Actions

Suggested host actions are fixed strings. They are not LLM-generated and should not mention facts outside the repository evidence.

Initial mapping:

- `unknown` + `block`: "Block delivery until the term is reviewed, removed, or added to an approved source."
- `unknown` + `review`: "Route to human review or regenerate with verified terms only."
- `unknown` + `allow`: "Deliver only if the host policy accepts unsupported terms."
- `unapproved` + `block`: "Block delivery until the term is approved or removed."
- `unapproved` + `review`: "Route to the source owner or reviewer before delivery."
- `unapproved` + `allow`: "Deliver only if the host policy accepts unapproved terms."
- `secret` + `block`: "Block delivery and remove or redact the sensitive term."
- `secret` + `review`: "Route to an authorized reviewer before delivery."
- `secret` + `allow`: "Deliver only if the host policy explicitly permits sensitive terms."

## API and MCP

API:

- `POST /api/v1/guardrail/enforce-output` returns `review_packet` when risky terms exist.

MCP:

- `enforce_grounded_output` returns the same `review_packet` payload as Python and API.

No request schema changes are required because the packet is derived from existing `terms` and optional `policy`.

## Audit Behavior

The existing audit payload remains compatible:

- `unknowns` continues to list unknown and unapproved terms.
- `limits` continues to summarize policy constraints.
- `findings` remains empty for this guardrail path in v0.8.3.

`review_packet` is included in the main result only. It is not copied into the audit event in this batch to avoid changing the audit schema too broadly.

## Compatibility

- Existing callers can ignore `review_packet`.
- Strict default behavior remains unchanged.
- Policy behavior remains unchanged.
- The response schema version remains `omniglyph.guardrail:0.1` because the change is additive.
- No new dependencies are introduced.

## Testing

Focused tests:

- `tests/test_guardrail.py`
  - default unknown terms include a `review_packet` with `unknown` + `block`.
  - policy review mode includes `unknown` + `review`.
  - fully known output omits `review_packet`.
  - mixed unknown and secret terms produce deterministic grouped packet.
  - repeated risky terms are deduplicated inside a group.
- `tests/test_api.py`
  - API response includes review packet for risky output.
- `tests/test_mcp.py`
  - MCP response includes review packet for risky output.

Final verification:

```bash
scripts/release_check.sh
```

## Acceptance Criteria

- `enforce_grounded_output` remains deterministic and source-backed.
- Review packet is present only when host action evidence is useful.
- Review packet groups risky terms by class and policy action.
- Python, API, and MCP surfaces expose the same payload shape.
- No automatic rewrite, redaction, persistence, or external integration is introduced.
- Full release gate passes before push.
