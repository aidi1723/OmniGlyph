# Policy Pack Parameter Guard v0.8.1 Design

## Objective

Policy Pack Parameter Guard adds deterministic runtime validation for intent parameters using the existing `parameters_schema` field in Policy Pack intents.

The goal is to move OmniGlyph intent checks from "is this intent allowed for this role?" to "is this intent allowed for this role with these parameters?" without introducing a general policy engine or external dependencies.

## Scope

This batch adds:

- A small schema validator for intent `parameters`.
- Runtime enforcement inside `enforce_intent_manifest`.
- Structured parameter findings in intent sandbox results.
- CLI/API/MCP behavior through the existing `parameters` argument.
- Tests, docs, and maintenance log updates.

This batch does not add:

- Full JSON Schema support.
- `$ref`, `oneOf`, `anyOf`, `allOf`, `pattern`, `format`, or custom expressions.
- Command execution.
- Parameter mutation, default injection, or coercion.
- External dependencies such as `jsonschema`.

## Supported Schema Subset

The validator supports only deterministic, local checks:

- `type`: `object`, `string`, `number`, `integer`, `boolean`, `array`
- `required`: list of required object fields
- `properties`: object field schemas
- `enum`: exact allowed values
- `minLength`, `maxLength`: string length bounds
- `minimum`, `maximum`: numeric bounds
- `items`: array item schema

Unknown schema keywords are ignored in v0.8.1. This keeps existing Policy Packs forward-compatible and avoids failing on metadata that a future release may understand.

## Runtime Behavior

`enforce_intent_manifest(intent_id, manifest, actor_role=None, parameters=None)` keeps its public signature.

Decision order:

1. Unknown intent returns `block`.
2. Explicit `decision=block` returns `block`.
3. Role mismatch returns `block`.
4. If `parameters_schema` is present and non-empty, validate `parameters`.
5. Parameter validation failure returns `block` with status `invalid_parameters`.
6. `decision=review` or `requires_approval=true` returns `review`.
7. Otherwise return `allow`.

Parameter validation failure result:

```json
{
  "schema": "omniglyph.intent_sandbox:0.1",
  "mode": "deterministic_execution_sandbox",
  "intent_id": "network.restart",
  "decision": "block",
  "status": "invalid_parameters",
  "parameters": {"service": 123},
  "limits": ["Intent parameters do not match parameters_schema."],
  "parameter_findings": [
    {
      "path": "$.service",
      "rule": "type",
      "message": "Expected string."
    }
  ]
}
```

Successful validation does not add `parameter_findings` unless the list is non-empty.

## Validator Shape

Add a focused helper module:

- `src/omniglyph/parameter_schema.py`

Public API:

```python
def validate_parameters(parameters: object, schema: dict[str, object]) -> list[dict[str, str]]:
    ...
```

The function returns an empty list for valid parameters and a list of findings for invalid parameters. It never raises for user-provided parameter values. Malformed schema should produce findings rather than crashing runtime enforcement.

Finding fields:

- `path`: JSON-ish path such as `$`, `$.service`, or `$.items[0]`
- `rule`: violated keyword such as `type`, `required`, `enum`, `minimum`
- `message`: concise human-readable explanation

## Compatibility

- Inline manifests and Policy Pack-derived manifests both use the same path.
- Existing manifests with no `parameters_schema` continue to behave exactly as before.
- Existing Policy Packs with `{}` as `parameters_schema` allow any object or omitted parameters.
- API and MCP already pass `parameters`; no new endpoint or MCP tool is needed.
- CLI already parses `--parameters`; no new CLI option is needed.

## Error Handling

Runtime parameter mismatch is a policy decision, not a server error:

- Python API returns a normal intent sandbox result.
- REST API returns HTTP 200 with `decision=block` and `status=invalid_parameters`.
- MCP returns a successful tool result containing the same JSON decision.
- CLI exits `0` because enforcement decisions are report payloads, not CLI execution failures.

Validation of Policy Pack files remains unchanged except that docs now describe the supported subset more precisely.

## Testing

Focused tests:

- `tests/test_parameter_schema.py`
  - accepts matching object parameters.
  - reports missing required fields.
  - reports string length and enum failures.
  - reports numeric bounds.
  - reports array item failures.
  - treats unknown schema keywords as non-fatal.
- `tests/test_language_security.py`
  - blocks invalid parameters after intent and role match.
  - allows valid parameters.
  - preserves behavior when no `parameters_schema` is present.
- `tests/test_policy_pack.py`
  - CLI enforcement reports `invalid_parameters` for a Policy Pack intent.
- `tests/test_api.py`
  - API returns `decision=block` and `status=invalid_parameters`.
- `tests/test_mcp.py`
  - MCP returns the same invalid-parameter payload.

Final verification:

```bash
scripts/release_check.sh
```

## Acceptance Criteria

- Invalid intent parameters are blocked deterministically across Python, CLI, API, and MCP.
- Existing intent enforcement behavior remains compatible for manifests without `parameters_schema`.
- Policy Pack docs explain the supported schema subset and non-goals.
- No new runtime dependency is added.
- Full release gate passes before push.
