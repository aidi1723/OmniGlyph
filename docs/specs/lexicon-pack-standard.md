# OmniGlyph Lexicon Pack Standard v0.1

Lexicon packs let individuals and companies mount private vocabulary into OmniGlyph without polluting the global Unicode fact layer.

Each pack is a directory:

```text
my-company-pack/
  pack.json
  terms.csv
```

## `pack.json`

```json
{
  "schema": "omniglyph.lexicon_pack:0.1",
  "pack_id": "company.acme.trade_terms",
  "namespace": "private_acme",
  "name": "ACME Trade Terms",
  "version": "2026.04.26",
  "owner_type": "enterprise",
  "license": "private",
  "visibility": "private",
  "description": "Company-specific terms for quote and customer workflows."
}
```

Rules:

- `schema` must be `omniglyph.lexicon_pack:0.1`.
- `namespace` should start with `private_` for user-owned packs.
- `pack_id` should be stable across versions.
- `version` should change whenever the pack changes.

## `terms.csv`

Required columns:

```csv
term,canonical_id,entry_type,language,aliases,definition,traits,sensitivity,review_status
```

Example:

```csv
FOB,trade:fob,trade_term,en,Free On Board;离岸价,Free On Board incoterm,"{""incoterm"":true}",normal,approved
底价,company:floor_price,confidential_term,zh,floor price;minimum price,Internal minimum selling price,"{""dlp"":true}",secret,approved
```

Field rules:

- `term`: primary text to match.
- `canonical_id`: stable machine ID, such as `company:floor_price`.
- `entry_type`: category such as `trade_term`, `material`, `product_spec`, or `confidential_term`.
- `language`: BCP-47-like language tag, or `und` when unknown.
- `aliases`: semicolon-separated aliases.
- `definition`: source-backed or owner-approved definition.
- `traits`: JSON object for machine-readable attributes.
- `sensitivity`: one of `normal`, `internal`, `secret`.
- `review_status`: one of `draft`, `approved`, `deprecated`.

## Runtime Behavior

- `approved` entries may be used by output guardrails.
- `draft` and `deprecated` entries can be looked up but do not count as trusted guardrail facts.
- `secret` entries can be included in output DLP redaction through API/MCP options.
- Pack metadata is stored with lexical entries as `pack_id` and `pack_version`.

## CLI

Create a starter pack:

```bash
omniglyph init-lexicon-pack my-pack --namespace private_acme --pack-id company.acme.trade_terms --name "ACME Trade Terms"
```

Validate before import:

```bash
omniglyph validate-domain-pack my-pack
```

Preview import:

```bash
omniglyph ingest-domain-pack --source my-pack --dry-run
```

Import or replace a namespace:

```bash
omniglyph ingest-domain-pack --source my-pack --replace-namespace
```
