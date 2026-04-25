# OmniGlyph Explanation Standard v0.1

OmniGlyph Explanation Standard (OES) defines how OmniGlyph explains symbols, terms, dictionary facts, and Unicode security findings for AI agents.

The goal is not to write a human-style dictionary article. The goal is to return compact, source-backed, machine-computable explanations that agents can verify, compare, route, and reason over without inventing missing facts.

## Core Rule

Every explanation separates six layers:

1. **Input layer:** what the user or agent submitted.
2. **Basic fact layer:** objective encoded facts such as code point, Unicode name, script, block, and category.
3. **Lexical layer:** dictionary-like facts such as language, pronunciation, part of speech, definition, aliases, and etymology.
4. **Concept layer:** links from terms or symbols to cross-language concept IDs.
5. **Safety layer:** Unicode spoofing, invisible controls, normalization changes, and other symbol-risk findings.
6. **Source and limit layer:** provenance, confidence, license, missing facts, and unsupported claims.

The standard favors explicit `null`, `unknown`, and `limits` over generated or guessed explanations.

## Normative Principles

### 1. Facts Are Not Inferences

Unicode code point, character name, general category, source version, and SHA-256 are facts.

Cross-language meaning, domain role, risk interpretation, and concept identity are interpretations or inferences. They must carry confidence and source evidence.

### 2. Missing Means Missing

If a source does not provide a value, OmniGlyph returns `null` or `unknown`. It must not invent a pronunciation, etymology, definition, or concept link to make the payload look complete.

### 3. Sources Are Required

Every non-null factual or lexical value must be traceable to a source snapshot or a named bundled fixture. A source record must include source name, source version, license note, and confidence.

### 4. Security Findings Are Explanations, Not Mutations

Safety reports may suggest review or replacement, but OmniGlyph does not mutate source code or user text by default.

### 5. Human Text Is Secondary

Human-readable summaries are optional convenience fields. Structured fields are the contract.

## Explanation Object

All explanation APIs and MCP tools should converge toward this shape:

```json
{
  "schema": "oes:0.1",
  "input": {
    "text": "水",
    "kind": "glyph",
    "normalized": "水"
  },
  "status": "matched",
  "canonical_id": "glyph:U+6C34",
  "basic_facts": {
    "unicode_hex": "U+6C34",
    "name": "CJK UNIFIED IDEOGRAPH-6C34",
    "script": "Han",
    "block": "CJK Unified Ideographs",
    "general_category": "Lo"
  },
  "lexical": [
    {
      "language": "zh",
      "pronunciation": "shui3",
      "definition": "water",
      "part_of_speech": null,
      "etymology": null,
      "confidence": 1.0,
      "source_id": "source:unihan:fixture"
    }
  ],
  "concept_links": [
    {
      "concept_id": "concept:water_substance",
      "relation": "denotes",
      "confidence": 0.92,
      "source_id": "source:curated:water-demo"
    }
  ],
  "safety": {
    "risk_level": "none",
    "findings": []
  },
  "sources": [
    {
      "source_id": "source:unihan:fixture",
      "source_name": "Unihan Database",
      "source_version": "fixture",
      "license": "Unicode Terms of Use",
      "confidence": 1.0
    }
  ],
  "limits": []
}
```

## Status Values

- `matched`: OmniGlyph found a source-backed explanation.
- `partial`: OmniGlyph found some facts, but major fields are missing.
- `unknown`: OmniGlyph found no local source-backed match.
- `ambiguous`: OmniGlyph found multiple plausible matches and cannot safely choose one.
- `unsafe`: OmniGlyph found one or more safety findings that require review.

## Input Kinds

- `glyph`: one Unicode scalar value or one normalized character.
- `term`: a lexical item such as `water`, `FOB`, or `tempered glass`.
- `sequence`: multiple characters where sequence-level meaning may differ from individual glyphs.
- `code`: source-code text scanned for Unicode symbol risks.
- `text`: general text scanned or audited outside source-code assumptions.

## Canonical IDs

Canonical IDs should be stable and namespaced:

- `glyph:U+6C34`
- `term:zh:water`
- `concept:water_substance`
- `rule:unicode-confusable`
- `source:unicode:15.1.0`
- `source:cldr:45`
- `source:wiktionary:revision:123456`

Canonical IDs are not marketing labels. They are durable machine identifiers.

## Lexical Layer

Lexical entries may come from Unihan, CLDR, Wiktionary, or private domain packs. Each entry should include:

- `language`
- `term`
- `normalized_term`
- `part_of_speech`
- `pronunciation`
- `definition`
- `aliases`
- `etymology`
- `entry_type`
- `confidence`
- `source_id`

Definitions from open dictionaries are source-backed text, not universal truth. They should be treated as dictionary evidence.

## Concept Layer

Concept links connect words and symbols to shared semantic nodes.

Example:

```text
水 -> concept:water_substance
water -> concept:water_substance
H2O -> concept:water_substance
```

Concept links should include:

- `concept_id`
- `relation`
- `confidence`
- `source_id`
- optional `context`

Allowed relation values for v0.1:

- `denotes`
- `alias_of`
- `variant_of`
- `translation_of`
- `symbolizes`
- `has_property`
- `broader_than`
- `narrower_than`

## Safety Layer

Safety findings explain symbol-level risk.

```json
{
  "rule_id": "unicode-confusable",
  "severity": "warning",
  "character": "а",
  "unicode_hex": "U+0430",
  "name": "CYRILLIC SMALL LETTER A",
  "confusable_with": "a",
  "message": "Character may be mistaken for Latin small letter a.",
  "suggested_action": "review",
  "auto_fixable": false,
  "source_id": "source:unicode-confusables:latest"
}
```

Initial rule families:

- `unicode-bidi-control`
- `unicode-invisible-format`
- `unicode-control-character`
- `unicode-cross-script-homoglyph-risk`
- `unicode-fullwidth-halfwidth-form`
- `unicode-nfkc-normalization-change`
- `unicode-confusable`

Severity values:

- `info`
- `warning`
- `error`

Risk levels:

- `none`
- `low`
- `medium`
- `high`
- `critical`

## Source Policy

OES-compatible sources must preserve:

- `source_id`
- `source_name`
- `source_url`
- `source_version`
- `retrieved_at`
- `sha256`
- `license`
- `local_path`

For Wiktionary-like sources, preserve page URL and revision ID when available.

For private domain packs, preserve namespace and organization-specific license notes. Private packs must not overwrite global Unicode, CLDR, Unihan, or public dictionary facts.

## API Direction

Future APIs should be additive:

- `GET /api/v1/explain/glyph?char=水`
- `GET /api/v1/explain/term?text=water`
- `POST /api/v1/explain`
- `POST /api/v1/audit-text`

MCP tools should mirror these capabilities:

- `explain_glyph`
- `explain_term`
- `audit_text`
- existing `scan_code_symbols`

## v0.5 Scope Recommendation

The first OES implementation should stay small:

1. Add OES-shaped wrappers around existing glyph lookup and term lookup.
2. Add Unicode confusables ingestion and expose source-backed `unicode-confusable` findings.
3. Add CLDR fixture ingestion for a small set of emoji/script/language labels.
4. Keep Wiktionary as a fixture-backed prototype until the schema proves stable.
5. Add tests that assert missing values remain `null` or `unknown`.

## Non-Goals

OES v0.1 does not provide:

- full OCR or image glyph recognition
- automatic source-code mutation
- universal concept graph coverage
- generated dictionary definitions
- production access control for private dictionaries
- claims of absolute semantic truth

## Acceptance Criteria

OES v0.1 is ready when:

- explain outputs include `schema: "oes:0.1"`
- all non-null factual and lexical values can point to a source
- safety findings use stable rule IDs
- ambiguous and unknown values are explicit
- tests cover matched, partial, unknown, ambiguous, and unsafe examples
