# OmniGlyph Parameter Schema Fail-Closed Design

## Status

- Date: 2026-07-16
- Target: post-intent-policy hardening local branch
- Scope: validation of the documented lightweight `parameters_schema` subset
- Compatibility: preserve valid schemas and continue ignoring unknown keywords

## Context

OmniGlyph documents a lightweight parameter-schema subset for intent policies. The
runtime evaluator applies a supported keyword only when its value already has the
expected Python type. A malformed supported keyword is otherwise ignored. Policy
Pack validation checks only that `parameters_schema` is a JSON object, and inline
manifest validation applies the same shallow container check.

This creates a fail-open policy boundary. A caller can believe a required field,
property schema, type, enum, bound, or array item constraint is active while the
runtime silently skips it and returns `allow`.

Confirmed reproductions:

```text
required: "service"                         -> allow / matched
properties: []                              -> allow / matched
type: [] or type: "date"                    -> allow / matched
properties.mode.enum: "safe"                -> allow / matched
properties.n.minimum: "10"                  -> allow / matched
properties.values.items: []                 -> allow / matched
Policy Pack with required: "service"        -> validation pass, loader succeeds
```

## Goals

1. Reject malformed uses of every documented parameter-schema keyword.
2. Apply one recursive meta-validator across direct Python, inline manifest, and
   Policy Pack boundaries.
3. Return stable path-based findings without exceptions or fail-open evaluation.
4. Preserve valid schema behavior and the documented unknown-keyword compatibility.
5. Keep CLI, API, MCP, and package interfaces stable.

## Non-Goals

- No full JSON Schema implementation or third-party `jsonschema` dependency.
- No new schema keywords, coercion, defaults, expressions, or automatic repair.
- No validation of ignored unknown keyword values.
- No cross-keyword semantic rules such as requiring `type: object` when
  `properties` is present.
- No authentication, request-size middleware, JSON-RPC batch, signing, publication,
  remote push, or deployment.

## Design

### 1. Recursive Schema Meta-Validator

Add a dependency-free function in `parameter_schema.py`:

```python
def validate_parameter_schema(schema: object, path: str = "$") -> list[Finding]:
    ...
```

It returns the existing finding shape:

```json
{
  "path": "$.properties.service.type",
  "rule": "type",
  "message": "Schema type must be one of array, boolean, integer, number, object, string."
}
```

Findings use the fixed keyword order shown below; property schemas follow property
insertion order. Recursive property and item schemas reuse the same validator with
their full path.

### 2. Supported Keyword Rules

Only documented keywords are inspected:

- `type`: string and one of `object`, `string`, `number`, `integer`, `boolean`, or
  `array`;
- `required`: list whose members are non-whitespace strings;
- `properties`: object with non-whitespace string keys and object schema values; each
  value is recursively validated;
- `enum`: list; an empty list remains valid and matches no value;
- `minLength`, `maxLength`: non-negative integers, excluding booleans;
- `minimum`, `maximum`: integers or finite floats, excluding booleans;
- `items`: object schema that is recursively validated.

Unknown keywords remain ignored at every nesting level. Duplicate `required` or
`enum` values remain accepted because they do not weaken enforcement and rejecting
them would add a new compatibility rule unrelated to this fail-open defect.

### 3. Boundary Integration

`validate_intent_manifest()` calls the meta-validator for every object
`parameters_schema`. Findings retain the manifest base path, for example:

```text
$.intents[0].parameters_schema.properties.service.type
```

Any schema finding produces the existing deterministic result:

```json
{
  "decision": "block",
  "status": "invalid_manifest",
  "manifest_findings": []
}
```

Policy Pack row validation calls the same function after JSON parsing. A finding is
rendered as a stable row error with its schema path. The strict loader then uses the
existing `invalid policy pack:` `ValueError` path, so adapters preserve their current
semantics:

- CLI enforcement: argparse error and exit `2`;
- API policy path: HTTP `400`;
- MCP policy path: JSON-RPC `-32602`.

`validate_parameters()` widens its schema annotation from `dict[str, object]` to
`object` and performs a defensive meta-validation at `$.schema` before evaluating
parameter values. This protects direct Python callers even if they bypass manifest
and Policy Pack boundaries. Valid runtime parameter findings continue to use
parameter paths rooted at `$`.

### 4. Error Precedence

- Schema errors are policy-definition errors, not parameter-value errors.
- Inline enforcement returns `invalid_manifest` before intent matching, role checks,
  or parameter evaluation.
- Invalid Policy Packs fail validation and cannot load.
- Direct `validate_parameters()` returns schema findings before value findings.
- A valid schema with invalid parameters keeps `block / invalid_parameters`.

## Test Strategy

1. Meta-validator rejects every malformed supported-keyword type and invalid type
   name, including nested property and item schemas.
2. Meta-validator accepts the existing valid object, string, numeric, boolean, and
   array examples.
3. Unknown keywords remain ignored.
4. Direct `validate_parameters()` returns `$.schema` findings for invalid schemas.
5. Inline enforcement returns `block / invalid_manifest` with the full schema path.
6. Policy Pack validation and loading reject malformed nested schemas.
7. CLI invalid-pack enforcement exits `2` without a traceback.
8. API and MCP invalid inline manifests return blocked evidence.
9. API and MCP invalid policy paths keep HTTP `400` and JSON-RPC `-32602`.
10. Existing parameter matching and all release gates remain green.

Each behavior starts with a focused failing regression test. Final verification runs
the full test suite, Ruff, mypy, privacy scan, MCP smoke, package build, Twine check,
artifact audit, clean-wheel smoke, demo verification, and branch diff inspection.

## Acceptance Criteria

- No malformed documented schema keyword can be silently ignored and authorize an
  intent.
- One validator defines schema validity for Python, inline, and Policy Pack paths.
- Findings identify the exact invalid schema path.
- Valid schemas and unknown keyword compatibility remain unchanged.
- Public CLI commands, API routes, MCP tools, response shapes, and valid Policy Pack
  manifests remain stable.
- No push, tag, publication, registry update, deployment, or external-system change
  occurs without separate approval.
