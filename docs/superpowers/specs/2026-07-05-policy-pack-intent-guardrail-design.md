# Policy Pack / Intent Guardrail v0.8 Design

## Objective

OmniGlyph v0.8 will promote the existing inline intent manifest into a reusable Policy Pack format for deterministic agent intent guardrails.

The goal is to let users keep role, approval, and audit rules in versioned files while preserving the current safety boundary: OmniGlyph evaluates intent policy and returns `allow`, `review`, or `block`; it never executes commands or performs side effects.

## Stakeholders

- Agent application developers who need a local-first policy check before tool calls.
- Security reviewers who need deterministic evidence for why an intent was allowed, sent to review, or blocked.
- OmniGlyph maintainers who need the new feature to fit the existing Lexicon Pack, API, MCP, CLI, and release-gate patterns.

## Scope

This release adds:

- A Policy Pack directory format with `policy.json` and `intents.csv`.
- A new `omniglyph.policy_pack` module for init, load, validate, path restriction, and namespace listing helpers.
- CLI commands for `init-policy-pack`, `validate-policy-pack`, and deterministic intent enforcement.
- API and MCP support for validating Policy Packs and enforcing an intent from a pack path.
- Backward compatibility for the existing inline `manifest` input.
- Documentation, examples, tests, and release-maintenance notes.

This release does not add:

- Command execution.
- A general-purpose policy DSL.
- Network or cloud policy storage.
- Database ingestion of Policy Packs.
- Dynamic expression evaluation in parameter schemas.

## Recommended Approach

Use an independent Policy Pack implementation, modeled after `src/omniglyph/lexicon_pack.py`.

This keeps the feature small and understandable while giving users a durable file format. It avoids the short-term trap of only expanding inline manifests, and it avoids the long-term risk of introducing a broad policy engine before the project has enough concrete use cases.

## Pack Layout

```text
my-policy-pack/
  policy.json
  intents.csv
```

## `policy.json`

Example:

```json
{
  "schema": "omniglyph.policy_pack:0.1",
  "policy_id": "company.acme.agent_policy",
  "namespace": "private_acme",
  "name": "ACME Agent Intent Policy",
  "version": "2026.07.05",
  "owner_type": "enterprise",
  "license": "private",
  "visibility": "private",
  "description": "Role and approval rules for ACME agent tool intents."
}
```

Rules:

- `schema` must be `omniglyph.policy_pack:0.1`.
- `policy_id` must be stable across versions.
- `namespace` should start with `private_` for user-owned packs.
- `version` should change whenever policy rules change.
- `owner_type`, `license`, and `visibility` follow the same practical conventions as Lexicon Packs.

## `intents.csv`

Required columns:

```csv
intent_id,canonical_phrase,decision,risk_level,requires_approval,allowed_roles,audit_required,parameters_schema
```

Example:

```csv
network.restart,restart network service,review,high,true,admin,true,"{""type"":""object"",""properties"":{""service"":{""type"":""string""}}}"
ticket.create,create support ticket,allow,low,false,admin;operator,true,"{}"
system.delete_root,delete root filesystem,block,critical,false,,true,"{}"
```

Field rules:

- `intent_id`: stable canonical intent, such as `network.restart`.
- `canonical_phrase`: human-readable phrase for audit output.
- `decision`: one of `allow`, `review`, or `block`.
- `risk_level`: one of `low`, `medium`, `high`, or `critical`.
- `requires_approval`: boolean string, one of `true`, `false`, `yes`, `no`, `1`, or `0`.
- `allowed_roles`: semicolon-separated role names. Empty means no role is allowed unless `decision` is `block`.
- `audit_required`: boolean string with the same accepted values as `requires_approval`.
- `parameters_schema`: JSON object used as evidence only in v0.8. OmniGlyph validates that it is an object but does not execute it or validate parameter values against it yet.

## Runtime Behavior

The runtime entry point remains deterministic:

```python
enforce_intent_manifest(intent_id, manifest, actor_role=None, parameters=None)
```

v0.8 adds a pack loader that turns a Policy Pack into the same manifest shape consumed by the existing enforcement function. The current inline manifest path remains supported.

Decision precedence:

1. Unknown intent returns `block` with status `unknown`.
2. Explicit `decision=block` returns `block`.
3. If `allowed_roles` is non-empty and `actor_role` is not included, return `block` with status `forbidden`.
4. If `decision=review` or `requires_approval=true`, return `review`.
5. Otherwise return `allow`.

The result includes policy metadata when loaded from a pack:

```json
{
  "schema": "omniglyph.intent_sandbox:0.1",
  "mode": "deterministic_execution_sandbox",
  "intent_id": "network.restart",
  "decision": "review",
  "status": "matched",
  "intent": {
    "intent_id": "network.restart",
    "canonical_phrase": "restart network service",
    "decision": "review",
    "risk_level": "high",
    "requires_approval": true,
    "allowed_roles": ["admin"],
    "audit_required": true,
    "parameters_schema": {}
  },
  "parameters": {"service": "network"},
  "limits": ["Intent requires approval before execution."],
  "policy": {
    "policy_id": "company.acme.agent_policy",
    "namespace": "private_acme",
    "version": "2026.07.05"
  }
}
```

Inline manifest results may omit `policy` unless the inline manifest provides equivalent metadata.

## CLI

Create a starter pack:

```bash
omniglyph init-policy-pack my-policy --namespace private_acme --policy-id company.acme.agent_policy --name "ACME Agent Intent Policy"
```

Validate:

```bash
omniglyph validate-policy-pack my-policy
```

Enforce from a pack:

```bash
omniglyph enforce-intent network.restart --policy-pack my-policy --actor-role admin --parameters '{"service":"network"}'
```

CLI output is JSON for validation and enforcement. Validation exits non-zero when the pack status is `fail`.

## API

Add:

- `POST /api/v1/policy/validate-pack` with `{ "path": "..." }`.

Extend:

- `POST /api/v1/language-security/enforce-intent` accepts either:
  - `manifest`, preserving v0.7 behavior.
  - `policy_pack_path`, loading and validating a pack before enforcement.

If both `manifest` and `policy_pack_path` are supplied, the API returns `400` to avoid ambiguous policy sources.

## MCP

Add tool:

- `validate_policy_pack`

Extend tool:

- `enforce_intent` accepts either `manifest` or `policy_pack_path`.

If both are supplied, MCP returns JSON-RPC invalid params. If a pack path is outside the configured policy root, MCP returns invalid params with the path restriction message.

## Path Restriction

Add `OMNIGLYPH_POLICY_PACK_ROOT`.

When configured, API and MCP pack validation/enforcement only allow paths inside that root. This mirrors `OMNIGLYPH_LEXICON_PACK_ROOT`.

The CLI does not restrict paths by default because local CLI users are explicitly choosing a file path.

## Error Handling

Policy Pack validation returns a structured report:

```json
{
  "schema": "omniglyph.policy_pack:0.1",
  "status": "fail",
  "policy": {
    "policy_id": null,
    "namespace": null,
    "name": null,
    "version": null
  },
  "summary": {
    "intent_count": 0,
    "allow_count": 0,
    "review_count": 0,
    "block_count": 0
  },
  "errors": ["policy.json is required"],
  "warnings": []
}
```

Validation errors are explicit and file-oriented:

- Missing `policy.json` or `intents.csv`.
- Invalid JSON in `policy.json`.
- Missing required metadata fields.
- Wrong schema.
- Missing required CSV columns.
- Empty required row fields.
- Invalid `decision`, `risk_level`, or boolean values.
- Invalid `parameters_schema` JSON or non-object schema values.

Loading a pack should only be used after validation passes. Runtime loaders may still raise `ValueError` for malformed files when called directly.

## File Responsibilities

- `src/omniglyph/policy_pack.py`: Policy Pack dataclass, init, load, validate, manifest conversion, path restriction, namespace helper.
- `src/omniglyph/language_security.py`: deterministic intent decision behavior and policy metadata passthrough.
- `src/omniglyph/cli.py`: CLI commands and JSON parameter parsing.
- `src/omniglyph/api.py`: API request model and endpoint wiring.
- `src/omniglyph/mcp_server.py`: MCP tool schema and dispatch wiring.
- `src/omniglyph/config.py`: `OMNIGLYPH_POLICY_PACK_ROOT` setting.
- `examples/policy-packs/agent_intents/`: runnable example pack.
- `docs/specs/policy-pack-standard.md`: user-facing standard.
- `docs/architecture/language-security-gateway.md`: mention Policy Pack-backed Intent Sandbox.
- `docs/product/v0.8-maintenance-log.md`: closeout and maintenance record.

## Testing

Focused tests:

- `tests/test_policy_pack.py`
  - validates a good pack.
  - reports malformed metadata and CSV rows.
  - loads pack metadata into manifest intent rows.
  - initializes a valid starter pack.
  - enforces allow, review, block, unknown, and forbidden decisions from pack-derived manifest.
- `tests/test_language_security.py`
  - preserves inline manifest compatibility.
  - confirms explicit `decision=block` precedence.
- `tests/test_api.py` or existing language-security API tests
  - validates Policy Pack endpoint.
  - enforces intent from `policy_pack_path`.
  - rejects simultaneous `manifest` and `policy_pack_path`.
- `tests/test_mcp.py`
  - exposes `validate_policy_pack`.
  - allows `enforce_intent` with `policy_pack_path`.
  - preserves inline manifest support.
- `tests/test_config.py`
  - loads `OMNIGLYPH_POLICY_PACK_ROOT`.

Final release-gate verification:

```bash
scripts/release_check.sh
```

## Acceptance Criteria

- Existing v0.7 inline intent enforcement tests still pass.
- A valid Policy Pack can be initialized, validated, loaded, and used for enforcement through Python, CLI, API, and MCP.
- Invalid packs fail with deterministic error messages and non-zero CLI validation status.
- API and MCP reject ambiguous policy source inputs.
- API and MCP enforce `OMNIGLYPH_POLICY_PACK_ROOT` when configured.
- Documentation explains the pack format, runtime behavior, and safety boundary.
- The full local release gate passes before GitHub push.

## Assumptions

- Policy Packs are local files controlled by the operator.
- v0.8 can validate that `parameters_schema` is a JSON object without validating runtime parameters against it.
- Database persistence for policies is not needed yet because policy enforcement is path-based and deterministic.
- The existing `omniglyph.intent_sandbox:0.1` result schema can remain unchanged for v0.8, with optional policy metadata added.

## Open Decisions Resolved

- Use a new `policy.json` file instead of reusing `pack.json`, so policy and lexicon pack formats remain visually distinct.
- Use CSV for intents to match existing Lexicon Pack ergonomics.
- Keep `allowed_commands` only for inline manifest backward compatibility; Policy Pack v0.8 does not need command lists because OmniGlyph never executes commands.
- Reject simultaneous inline `manifest` and `policy_pack_path` to keep audit provenance unambiguous.
