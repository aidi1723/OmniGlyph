# OmniGlyph World Protocol Pack Standard v0.1

World Protocol Packs define deterministic, source-backed protocol rules that an Agent host can call before allowing a goal, action, intent, or output to continue.

This standard is not a universal ethics engine. It is a machine-readable rule-pack format for checked runtime boundaries.

Each pack is a directory:

```text
my-protocol-pack/
  protocol.json
```

## `protocol.json`

```json
{
  "schema": "omniglyph.protocol_pack:0.1",
  "protocol_id": "root.civilization.starter",
  "name": "Civilization Root Protocol Starter",
  "version": "0.1.0",
  "layer": "root",
  "owner": "omniglyph",
  "license": "Apache-2.0",
  "description": "Starter deterministic protocol checks for source-grounded agent behavior.",
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

- `schema`: must be `omniglyph.protocol_pack:0.1`.
- `protocol_id`: stable machine ID for the protocol.
- `name`: human-readable protocol name.
- `version`: protocol pack version.
- `layer`: one of `root`, `jurisdiction`, `industry`, `enterprise`, or `scenario`.
- `owner`: maintaining person, company, or community.
- `license`: source or usage license.
- `rules`: list of rule objects.

Required rule fields:

- `rule_id`: stable machine ID.
- `category`: one of `physical_reality`, `life_safety`, `social_coordination`, or `symbolic_cognition`.
- `severity`: one of `info`, `warn`, or `block`.
- `statement`: source-backed rule statement.
- `match`: deterministic matching definition.
- `decision`: one of `allow`, `warn`, `block`, or `unknown`.
- `confidence`: numeric value from `0` to `1`.
- `source`: source evidence object with `source_id`, `source_name`, `source_version`, and `license`.

## Match Types

v0.1 supports intentionally small deterministic matchers:

- `keyword_any`: matches when any configured keyword appears in the checked text.
- `keyword_all`: matches when every configured keyword appears in the checked text.
- `exact_intent`: matches when `kind` is `intent` and the checked text exactly equals the configured intent.

## Runtime Decision

`check_protocol` returns:

- `block` if any matched rule blocks.
- `warn` if no rule blocks and any matched rule warns.
- `unknown` if no rule matches.
- `allow` if matched rules only allow.

`unknown` is not a permission grant. The host Agent runtime must decide whether unknown means human review, block, fallback, or another policy.

## CLI

Create a starter pack:

```bash
omniglyph init-protocol-pack my-protocol --protocol-id root.local --name "Local Root Protocol"
```

Validate a pack:

```bash
omniglyph validate-protocol-pack my-protocol
```

Check text:

```bash
omniglyph check-protocol --protocol examples/protocol-packs/root_starter --kind output --text "unsupported reference"
```

## Boundaries

World Protocol Pack v0.1 checks configured deterministic rules only. It does not automatically update law, infer ethics, execute commands, or prove global Agent alignment.
