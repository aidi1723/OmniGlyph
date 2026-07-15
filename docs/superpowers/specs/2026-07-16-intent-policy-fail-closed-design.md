# OmniGlyph Intent Policy Fail-Closed Design

## Status

- Date: 2026-07-16
- Target: post-`0.8.0b0` local hardening branch
- Scope: inline intent manifest and Policy Pack execution validation
- Compatibility: preserve valid Python, CLI, API, and MCP intent-enforcement behavior

## Context

Policy Pack validation and Policy Pack loading currently use separate paths.
`validate_policy_pack()` detects invalid decisions, risk levels, booleans, schemas,
and duplicate intent IDs, while `load_policy_pack()` parses rows directly without
calling that validator. CLI, API, and MCP enforcement load packs directly, so an
operator can execute an invalid pack without first validating it.

Inline manifests have a related fail-open boundary. Unknown decisions fall through
to `allow`, a string `allowed_roles` value is treated as a membership container,
and non-object intent entries raise runtime exceptions. These behaviors conflict
with the documented deterministic guardrail model.

## Goals

1. Make malformed or ambiguous intent policies fail closed at every execution entry.
2. Keep valid historical inline manifests compatible, including omitted `decision`.
3. Make Policy Pack loading enforce the same validation already exposed to users.
4. Return deterministic errors instead of tracebacks or HTTP 500 responses.
5. Cover Python, CLI, API, and MCP behavior with regression tests.

## Non-Goals

- No new policy decisions, risk levels, schema keywords, or execution capability.
- No removal of inline manifest support.
- No automatic repair of invalid Policy Packs.
- No authentication, authorization service, persistent approval queue, or command execution.
- No package publication, remote push, registry update, or production deployment.

## Design

### 1. Inline Manifest Validation

Add a dependency-free manifest validator at the language-security boundary. It
returns structured findings with `path`, `rule`, and `message` fields.

Validation rules:

- the manifest must be an object;
- optional `policy` must be an object;
- `intents` must be a list;
- every intent entry must be an object;
- every intent must have a non-empty string `intent_id`;
- `intent_id` values must be unique;
- optional `decision` must be `allow`, `review`, or `block`;
- optional `requires_approval` must be a boolean;
- optional `allowed_roles` must be a list of non-empty strings;
- optional `parameters_schema` must be an object.

Unknown fields remain ignored for backward compatibility. An omitted `decision`
continues to mean the historical default path: `review` when approval is required,
otherwise `allow`.

`enforce_intent_manifest()` validates the complete manifest before matching an
intent. Any finding returns:

```json
{
  "decision": "block",
  "status": "invalid_manifest",
  "limits": ["Intent manifest is invalid and cannot authorize actions."],
  "manifest_findings": []
}
```

The function must not raise for malformed caller data.

### 2. Strict Policy Pack Loading

`load_policy_pack()` will call `validate_policy_pack()` before reading runtime
metadata and intents. A failed report raises `ValueError` with a stable
`invalid policy pack:` prefix and the report's validation errors. Valid pack return
types and manifest output remain unchanged.

This closes the gap for invalid decisions, risk levels, boolean fields, schemas,
missing columns, malformed JSON, and duplicate intent IDs without duplicating rules.

### 3. Entry-Point Error Semantics

- Python `load_policy_pack()`: raise `ValueError` for an invalid pack.
- CLI `enforce-intent`: convert the loader error to an argparse usage error, exit 2,
  and do not print a traceback.
- API policy-path enforcement: return HTTP 400 with the stable validation message.
- MCP policy-path enforcement: return JSON-RPC `-32602` with the stable validation message.
- Inline API/MCP enforcement: return the deterministic blocked
  `invalid_manifest` result because malformed policy evidence is a guardrail
  decision, not a transport failure.

### 4. Documentation

Update the Policy Pack standard and Language Security Gateway documentation to say
that enforcement validates policies automatically and fails closed. Add a dated
second-stage closeout report with root-cause evidence, behavior changes, tests,
compatibility, and remaining risks.

## Error Handling

- Validation collects all deterministic manifest findings in input order.
- Invalid manifest content never reaches `_find_intent()`.
- Policy Pack parse and validation details may identify filenames, rows, and fields,
  but must not include secrets or a Python traceback.
- Valid unknown intent IDs keep the existing `block` / `unknown` response.
- Valid role, parameter, explicit block, review, and allow decisions remain unchanged.

## Test Strategy

1. Core enforcement blocks unknown decisions.
2. Core enforcement rejects string roles and does not permit substring matches.
3. Core enforcement blocks non-object intent entries without raising.
4. Core enforcement blocks duplicate inline intent IDs.
5. Core enforcement preserves valid manifests that omit `decision`.
6. `load_policy_pack()` rejects invalid and duplicate Policy Packs.
7. CLI invalid-pack enforcement exits 2 without traceback.
8. API invalid-pack enforcement returns HTTP 400.
9. MCP invalid-pack enforcement returns `-32602`.
10. API and MCP malformed inline manifests return blocked `invalid_manifest` evidence.

Each behavior starts with a focused failing regression test. After focused tests,
run the full test suite, Ruff, mypy, privacy scan, MCP smoke, package build, Twine,
artifact audit, clean-wheel smoke, and demo verification.

## Acceptance Criteria

- No malformed manifest or invalid Policy Pack can produce `allow` or `review`.
- No malformed intent entry can raise through Python, API, or MCP boundaries.
- Valid existing intent tests remain unchanged and pass.
- All four enforcement entry types have regression coverage.
- Public command names, routes, MCP tool names, and valid response behavior remain stable.
- Full release verification passes and the second-stage closeout report is linked from project status.
