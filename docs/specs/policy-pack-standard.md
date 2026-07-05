# OmniGlyph Policy Pack Standard v0.1

Policy Packs let teams define deterministic agent intent rules without embedding policy in prompts or application code.

Each pack is a directory:

```text
my-policy-pack/
  policy.json
  intents.csv
```

## `policy.json`

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
  "description": "Role and approval rules for agent tool intents."
}
```

Rules:

- `schema` must be `omniglyph.policy_pack:0.1`.
- `policy_id` should stay stable across versions.
- `namespace` should start with `private_` for user-owned packs.
- `version` should change whenever intent rules change.

## `intents.csv`

Required columns:

```csv
intent_id,canonical_phrase,decision,risk_level,requires_approval,allowed_roles,audit_required,parameters_schema
```

Example:

```csv
network.restart,restart network service,review,high,true,admin,true,"{""type"":""object""}"
ticket.create,create support ticket,allow,low,false,admin;operator,true,"{}"
system.delete_root,delete root filesystem,block,critical,false,,true,"{}"
```

Field rules:

- `intent_id`: canonical intent requested by an agent.
- `canonical_phrase`: human-readable audit phrase.
- `decision`: one of `allow`, `review`, or `block`.
- `risk_level`: one of `low`, `medium`, `high`, or `critical`.
- `requires_approval`: boolean string: `true`, `false`, `yes`, `no`, `1`, or `0`.
- `allowed_roles`: semicolon-separated role names. Empty role lists are only useful for explicit `block` intents.
- `audit_required`: boolean string with the same accepted values as `requires_approval`.
- `parameters_schema`: JSON object used for deterministic runtime parameter validation.

Supported `parameters_schema` keywords:

- `type`: `object`, `string`, `number`, `integer`, `boolean`, or `array`
- `required`: required object fields
- `properties`: object field schemas
- `enum`: exact allowed values
- `minLength`, `maxLength`: string bounds
- `minimum`, `maximum`: numeric bounds
- `items`: array item schema

Unsupported keywords such as `$ref`, `oneOf`, `anyOf`, `pattern`, and `format` are ignored in v0.8.1. OmniGlyph does not execute expressions, mutate parameters, inject defaults, or coerce types.

## Runtime Behavior

Policy Packs are converted into the same manifest shape used by `enforce_intent`.

Decision precedence:

1. Unknown intent returns `block`.
2. Explicit `decision=block` returns `block`.
3. Role mismatch returns `block`.
4. Parameter mismatch returns `block` with `status: "invalid_parameters"`.
5. `decision=review` or `requires_approval=true` returns `review`.
6. Otherwise the intent returns `allow`.

OmniGlyph never executes commands. It returns deterministic evidence for a host app, MCP client, policy gateway, or human reviewer.

Invalid parameter response excerpt:

```json
{
  "decision": "block",
  "status": "invalid_parameters",
  "limits": ["Intent parameters do not match parameters_schema."],
  "parameter_findings": [
    {"path": "$.service", "rule": "type", "message": "Expected string."}
  ]
}
```

## CLI

Create a starter pack:

```bash
omniglyph init-policy-pack my-policy --namespace private_acme --policy-id company.acme.agent_policy --name "ACME Agent Intent Policy"
```

Validate:

```bash
omniglyph validate-policy-pack my-policy
```

Enforce:

```bash
omniglyph enforce-intent network.restart --policy-pack my-policy --actor-role admin --parameters '{"service":"network"}'
```

## API and MCP

API:

- `POST /api/v1/policy/validate-pack`
- `POST /api/v1/language-security/enforce-intent` with either `manifest` or `policy_pack_path`

MCP:

- `validate_policy_pack`
- `enforce_intent` with either `manifest` or `policy_pack_path`

When `OMNIGLYPH_POLICY_PACK_ROOT` is set, API and MCP only accept pack paths inside that root.
