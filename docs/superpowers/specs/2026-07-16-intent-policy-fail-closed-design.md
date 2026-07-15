# OmniGlyph Intent Policy Fail-Closed Design

## Status

- Date: 2026-07-16
- Target: post-`0.8.0b0` local hardening branch
- Scope: inline intent manifest and Policy Pack execution validation
- Compatibility: preserve valid Python, CLI, API, and MCP intent-enforcement behavior
- Review revision: close validation-snapshot, malformed-CSV, and adapter type gaps

## Context

Before the first implementation pass, Policy Pack validation and loading used
separate paths. `validate_policy_pack()` detected invalid decisions, risk levels,
booleans, schemas, and duplicate intent IDs, while `load_policy_pack()` parsed rows
directly without calling that validator. CLI, API, and MCP enforcement loaded packs
directly, so an operator could execute an invalid pack without first validating it.

Inline manifests have a related fail-open boundary. Unknown decisions fall through
to `allow`, a string `allowed_roles` value is treated as a membership container,
and non-object intent entries raise runtime exceptions. These behaviors conflict
with the documented deterministic guardrail model.

Implementation review found four remaining boundary gaps after the first pass:

- `load_policy_pack()` validated files and then reopened them, allowing the loaded
  authorization data to differ from the validated snapshot;
- an array or object `decision` raised `TypeError` during set membership;
- CSV rows with fields beyond the header caused `AttributeError` inside validation;
- API and MCP rejected a top-level non-object manifest before core fail-closed
  validation could return deterministic blocked evidence.

## Goals

1. Make malformed or ambiguous intent policies fail closed at every execution entry.
2. Keep valid historical inline manifests compatible, including omitted `decision`.
3. Make Policy Pack loading enforce the same validation already exposed to users.
4. Return deterministic errors instead of tracebacks or HTTP 500 responses.
5. Cover Python, CLI, API, and MCP behavior with regression tests.
6. Build a loaded Policy Pack only from the exact parsed objects that passed validation.

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

Decision validation must check the value type before enum membership so arbitrary
JSON values, including arrays and objects, produce a finding instead of an exception.

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

The function must not raise for malformed JSON-compatible caller data.

### 2. Strict Policy Pack Loading

Policy Pack inspection reads and parses each source file once. The public
`validate_policy_pack()` report and `load_policy_pack()` both use the same internal
inspection result; the loader constructs `PolicyPack` directly from the metadata
and intents in that validated snapshot. It must not reopen the files after a pass.

A failed inspection raises `ValueError` from `load_policy_pack()` with a stable
`invalid policy pack:` prefix and the report's validation errors. CSV rows with
values beyond the declared header are validation failures, not parser exceptions.
Valid pack return types and manifest output remain unchanged.

This closes the gap for invalid decisions, risk levels, boolean fields, schemas,
missing columns, malformed JSON, and duplicate intent IDs without duplicating rules.

### 3. Entry-Point Error Semantics

- Python `load_policy_pack()`: raise `ValueError` for an invalid pack.
- CLI `enforce-intent`: convert the loader error to an argparse usage error, exit 2,
  and do not print a traceback.
- API policy-path enforcement: return HTTP 400 with the stable validation message.
- MCP policy-path enforcement: return JSON-RPC `-32602` with the stable validation message.
- Inline API/MCP enforcement: accept any JSON manifest value at the transport model
  boundary and return the deterministic blocked `invalid_manifest` result for
  invalid values because malformed policy evidence is a guardrail decision, not a
  transport failure. The exactly-one-of manifest/policy-path rule remains unchanged.

### 4. Documentation

Update the Policy Pack standard and Language Security Gateway documentation to say
that enforcement validates policies automatically and fails closed. Add a dated
second-stage closeout report with root-cause evidence, behavior changes, tests,
compatibility, and remaining risks.

## Error Handling

- Validation collects all deterministic manifest findings in input order.
- Invalid manifest content never reaches `_find_intent()`.
- Non-string decisions never reach set membership or decision evaluation.
- Policy Pack loading never reparses a successfully inspected file snapshot.
- Structurally malformed CSV is reported through the same stable invalid-pack path.
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
11. A Policy Pack changed after inspection cannot replace the validated runtime snapshot.
12. Non-string decisions return blocked findings without exceptions.
13. CSV rows with extra columns fail validation and loading without tracebacks.
14. API and MCP top-level array manifests return blocked `invalid_manifest` evidence.

Each behavior starts with a focused failing regression test. After focused tests,
run the full test suite, Ruff, mypy, privacy scan, MCP smoke, package build, Twine,
artifact audit, clean-wheel smoke, and demo verification.

## Acceptance Criteria

- No manifest that violates the listed validation rules, and no invalid Policy Pack,
  can produce `allow` or `review`.
- No malformed intent entry can raise through Python, API, or MCP boundaries.
- Loader output is constructed from the same parsed metadata and intents that passed
  validation, with no post-validation file read.
- Malformed CSV structure is a deterministic validation error at every entry point.
- Valid existing intent tests remain unchanged and pass.
- All four enforcement entry types have regression coverage.
- Public command names, routes, MCP tool names, and valid response behavior remain stable.
- Full release verification passes and the second-stage closeout report is linked from project status.
