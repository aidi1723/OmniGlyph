# World Protocol Pack v0.1 Design

## Purpose

World Protocol Pack v0.1 turns the "world dictionary" idea into a small, testable OmniGlyph capability: a versioned rule-pack format plus deterministic runtime checks for agent goals, actions, and outputs.

The feature does not claim to be a final global ethics authority. It creates a source-backed checkpoint that a host agent runtime can call before it proceeds.

## Positioning

OmniGlyph's core remains the Global Symbol Ground Truth Layer. World Protocol Pack is a higher-level protocol layer built on that base.

```text
Unicode and symbol facts
  -> Lexicon Pack and OES evidence
  -> World Protocol Pack rules
  -> Agent guardrail decision
```

The public language should use careful claims:

- Say "deterministic protocol checks for checked inputs."
- Say "source-backed rules with explicit limits."
- Say "host runtimes can force calls through MCP, API, or gateway policy."
- Do not say "guarantees all agents never lose control."
- Do not say "defines final universal human values."

## MVP Scope

v0.1 focuses on one concrete deliverable: **OmniGlyph World Protocol Pack**.

It includes:

- a `protocol.json` file format
- a bundled starter root protocol example
- a validator for protocol packs
- a runtime checker that returns `allow`, `warn`, `block`, or `unknown`
- API and MCP exposure
- audit-friendly evidence fields

It excludes:

- automatic web learning
- automatic legal or ethical reasoning
- autonomous rule updates
- cryptographic signing
- global registry governance
- execution of blocked or allowed actions

Those exclusions are intentional. They keep v0.1 aligned with OmniGlyph's current deterministic architecture.

## Data Model

A protocol pack is a directory:

```text
root-protocol/
  protocol.json
```

The v0.1 schema is:

```json
{
  "schema": "omniglyph.protocol_pack:0.1",
  "protocol_id": "root.civilization.v0",
  "name": "Civilization Root Protocol Starter",
  "version": "0.1.0",
  "layer": "root",
  "owner": "omniglyph",
  "license": "Apache-2.0",
  "description": "Starter protocol checks for source-grounded agent behavior.",
  "rules": [
    {
      "rule_id": "symbolic.truth.no_fabricated_sources",
      "category": "symbolic_cognition",
      "severity": "block",
      "statement": "Do not present unsupported sources, data, or references as verified facts.",
      "match": {
        "type": "keyword_any",
        "keywords": ["fabricated citation", "fake source", "unsupported reference"]
      },
      "decision": "block",
      "confidence": 0.9,
      "source": {
        "source_id": "source:omniglyph:protocol-starter",
        "source_name": "OmniGlyph Protocol Starter",
        "source_version": "0.1.0",
        "license": "Apache-2.0"
      }
    }
  ]
}
```

Required top-level fields:

- `schema`
- `protocol_id`
- `name`
- `version`
- `layer`
- `owner`
- `license`
- `rules`

Allowed `layer` values:

- `root`
- `jurisdiction`
- `industry`
- `enterprise`
- `scenario`

Required rule fields:

- `rule_id`
- `category`
- `severity`
- `statement`
- `match`
- `decision`
- `confidence`
- `source`

Allowed `category` values:

- `physical_reality`
- `life_safety`
- `social_coordination`
- `symbolic_cognition`

Allowed `severity` values:

- `info`
- `warn`
- `block`

Allowed `decision` values:

- `allow`
- `warn`
- `block`
- `unknown`

v0.1 matching intentionally starts small:

- `keyword_any`: match when any keyword is present in the checked text.
- `keyword_all`: match when every keyword is present in the checked text.
- `exact_intent`: match when a canonical intent equals a configured string.

## Runtime Check

The core runtime function should accept:

```json
{
  "text": "The agent candidate goal, action, or output.",
  "kind": "output",
  "protocol_path": "examples/protocol-packs/root_starter",
  "actor_id": "agent:demo"
}
```

Allowed `kind` values:

- `goal`
- `action`
- `output`
- `intent`

The response shape should be:

```json
{
  "schema": "omniglyph.protocol_check:0.1",
  "decision": "block",
  "status": "warn",
  "kind": "output",
  "matched_rules": [
    {
      "rule_id": "symbolic.truth.no_fabricated_sources",
      "category": "symbolic_cognition",
      "severity": "block",
      "decision": "block",
      "statement": "Do not present unsupported sources, data, or references as verified facts.",
      "confidence": 0.9,
      "source_id": "source:omniglyph:protocol-starter"
    }
  ],
  "unknown": [],
  "sources": [
    {
      "source_id": "source:omniglyph:protocol-starter",
      "source_name": "OmniGlyph Protocol Starter",
      "source_version": "0.1.0",
      "license": "Apache-2.0"
    }
  ],
  "limits": [
    "World Protocol Pack v0.1 checks only configured deterministic rules.",
    "The host runtime remains responsible for extraction, tool permissions, and human review."
  ]
}
```

Decision aggregation:

- If any matched rule has `decision: "block"`, return `block`.
- Else if any matched rule has `decision: "warn"`, return `warn`.
- Else if no rules match, return `unknown`.
- Else return `allow`.

The `unknown` decision is not a permission grant. The host runtime should decide whether unknown means review, block, or fallback.

## API and MCP

API endpoints:

- `POST /api/v1/protocol/validate-pack`
- `POST /api/v1/protocol/check`

MCP tools:

- `validate_protocol_pack`
- `check_protocol`

CLI commands:

- `omniglyph init-protocol-pack PATH --protocol-id root.civilization.v0 --name "Civilization Root Protocol Starter"`
- `omniglyph validate-protocol-pack PATH`
- `omniglyph check-protocol --protocol PATH --kind output --text "..."`

The MCP and API payloads should share the same schemas as the Python runtime.

## Integration With Existing OmniGlyph

World Protocol Pack should reuse existing project patterns:

- Use OES-style source and limit fields.
- Use `audit_explain` style actor evidence when an `actor_id` is provided.
- Follow Lexicon Pack directory conventions.
- Keep rule validation separate from runtime checking.
- Never execute host actions or shell commands.

The feature should not replace `scan_language_input`, `scan_output_dlp`, or `enforce_intent`. It complements them:

- Language Security Gateway checks prompt-injection and data leakage patterns.
- Intent Sandbox checks explicit allowed intents.
- World Protocol Pack checks source-backed protocol rules.

## Testing Strategy

Unit tests should cover:

- valid protocol pack validation
- missing required top-level fields
- invalid rule decision
- `keyword_any` matching
- `keyword_all` matching
- `exact_intent` matching
- decision aggregation
- API endpoints
- MCP tools list and tool calls
- CLI validation and check commands

Smoke tests should update the expected MCP tool list count after adding the two protocol tools.

## Documentation

Docs should include:

- `docs/specs/world-protocol-pack-standard.md`
- README positioning paragraph
- `docs/mcp-tools.md` tool entries
- `docs/api.md` API entries
- `docs/architecture/world-protocol-layer.md`

The docs must state that v0.1 is a deterministic protocol-check layer, not a global guarantee of agent alignment.

## Implementation Order

1. Add protocol pack parser and validator.
2. Add runtime checker and decision aggregation.
3. Add example root starter pack.
4. Add API endpoints.
5. Add MCP tools.
6. Add CLI commands.
7. Update docs and smoke tests.
8. Run full tests, MCP smoke test, package build, and metadata check.

## Success Criteria

The feature is complete when:

- users can validate a protocol pack
- users can run a protocol check from Python, API, MCP, and CLI
- the response includes matched rules, sources, limits, and deterministic decision
- full test suite passes
- MCP smoke test includes the new protocol tools
- docs avoid overclaiming global safety guarantees
