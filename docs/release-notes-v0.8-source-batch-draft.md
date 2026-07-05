# OmniGlyph v0.8.0 Beta Draft Release Notes

Status: release-prep draft for the current source branch.

Current source version: `0.8.0b0`.

This release candidate is not published to TestPyPI or PyPI yet. The latest published PyPI version remains `0.6.0b0`.

## Product Positioning

v0.8 turns OmniGlyph from a deterministic symbol and language-security checkpoint into a stronger local policy evidence layer for AI-agent workflows.

The intended claim is narrow:

```text
OmniGlyph gives host systems deterministic JSON evidence for agent intents, intent parameters, source-grounded output terms, risky terminology, and review routing.
```

It does not claim to execute actions, replace host approval systems, or remove the need for sandboxing and access control.

## Highlights

### Policy Pack intent guardrails

Policy Packs let teams define local deterministic agent intent rules without embedding policy in prompts or application code.

Policy Pack shape:

```text
my-policy-pack/
  policy.json
  intents.csv
```

New or expanded CLI commands:

```bash
omniglyph init-policy-pack examples/policy-packs/agent_intents
omniglyph validate-policy-pack examples/policy-packs/agent_intents
omniglyph enforce-intent network.restart --policy-pack-path examples/policy-packs/agent_intents --role sre
```

New or expanded API/MCP surfaces:

- `POST /api/v1/policy/validate-pack`
- `POST /api/v1/security/enforce-intent` with `policy_pack_path`
- MCP `validate_policy_pack`
- MCP `enforce_intent` with `policy_pack_path`

Compatibility:

- Inline manifests remain supported.
- API and MCP reject requests that provide both `manifest` and `policy_pack_path`.
- `OMNIGLYPH_POLICY_PACK_ROOT` can restrict API/MCP Policy Pack paths.

### Intent parameter validation

v0.8.1 adds deterministic runtime validation for `parameters_schema`.

Supported schema subset:

- `type`
- `required`
- `properties`
- `enum`
- `minLength`
- `maxLength`
- `minimum`
- `maximum`
- array `items`

Invalid parameters return a blocking policy result:

```json
{
  "decision": "block",
  "status": "invalid_parameters",
  "limits": ["Intent parameters do not match parameters_schema."],
  "parameter_findings": []
}
```

Unsupported schema keywords are ignored. OmniGlyph does not execute expressions, mutate parameters, inject defaults, or coerce types.

### Output guardrail policy modes

v0.8.2 adds policy modes to `enforce_grounded_output` so host systems can choose how to handle:

- unknown terms
- unapproved terms
- secret terms

Supported actions:

- `allow`
- `review`
- `block`

Strict blocking remains the default when no policy is provided.

### Guardrail Review Packet

v0.8.3 adds `review_packet` as deterministic host-review evidence for risky output terms.

The packet groups risky terms by class and action:

- `unknown`
- `unapproved`
- `secret`

It includes summary counts, classes, actions, source metadata when available, and suggested host actions.

v0.8.4 hardens this surface with direct coverage for unapproved terms and policy-allowed unknown terms, and consolidates action precedence into one runtime constant.

### Output guardrail CLI

v0.8.5 adds `omniglyph enforce-output` as a local JSON evidence command:

```bash
omniglyph enforce-output --term FOB --term "HS 7604.99X" --policy '{"unknown_action":"review"}'
```

The CLI returns the same output guardrail evidence as the Python runtime. `block` and `review` decisions do not make the CLI exit non-zero in this batch; shell workflows should inspect the JSON result and choose their own failure policy.

## MCP Tools in Source Branch

The current source branch exposes MCP tools for:

- glyph lookup
- term lookup
- OES explanations
- token normalization
- namespace listing
- Lexicon Pack validation
- output term validation
- output guardrail enforcement
- Unicode security scanning
- language input scanning
- output DLP scanning
- intent enforcement
- Policy Pack validation
- audit explanations

`scan_code_symbols` remains available as a backward-compatible alias for `scan_unicode_security`.

## Boundaries

v0.8 does not add:

- automatic rewriting
- command execution
- persistent approval queues
- database ingestion for Policy Packs
- ERP/email/webhook integrations
- IAM, OS sandboxing, or endpoint security replacement
- package registry publication
- MCP registry publication

Host applications are expected to treat OmniGlyph output as deterministic evidence and enforce their own workflow decisions.

## Verification

Final closeout verification:

- Python tests: `184 passed`
- Ruff: pass
- mypy: pass
- MCP smoke: 17 tools available
- Package build: `omniglyph-0.8.0b0.tar.gz` and `omniglyph-0.8.0b0-py3-none-any.whl`
- Twine metadata check: pass
- Artifact content audit: pass
- Clean wheel install with CLI/MCP smoke: pass
- Cross-border demo check: pass

## Release Notes for Maintainers

- Package version is now prepared as `0.8.0b0`.
- Before publishing, rebuild artifacts after a clean `scripts/release_check.sh` run.
- Publish to TestPyPI first using exact artifact filenames.
- Re-run CLI and MCP smoke checks from a clean wheel install before PyPI upload.
- Update MCP registry metadata only after the package release plan is settled.
