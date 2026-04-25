# OmniGlyph API Reference

Base URL for local development:

```text
http://127.0.0.1:8000
```

## `GET /api/v1/health`

Returns service status.

Response:

```json
{"status":"ok","service":"omniglyph","version":"0.6.0b0"}
```

## `GET /api/v1/glyph`

Query one Unicode character.

Request:

```text
GET /api/v1/glyph?char=铝
```

Responses:

- `200`: glyph found.
- `400`: `char` is not exactly one Unicode character.
- `404`: glyph not found in local database.

## `GET /api/v1/term`

Query a lexical/domain term or alias.

Request:

```text
GET /api/v1/term?text=FOB
```

Responses:

- `200`: term found.
- `404`: term not found.

## `GET /api/v1/explain/glyph`

Explain one Unicode character using OmniGlyph Explanation Standard v0.1.

Request:

```text
GET /api/v1/explain/glyph?char=铝
```

Response excerpt:

```json
{
  "schema": "oes:0.1",
  "status": "matched",
  "canonical_id": "glyph:U+94DD",
  "input": {"text": "铝", "kind": "glyph", "normalized": "铝"},
  "safety": {"risk_level": "none", "findings": []}
}
```

Unknown glyphs return `status: "unknown"` with an explicit `limits` entry instead of a generated definition.

## `GET /api/v1/explain/term`

Explain one lexical/domain term using OmniGlyph Explanation Standard v0.1.

Request:

```text
GET /api/v1/explain/term?text=FOB
```

Response excerpt:

```json
{
  "schema": "oes:0.1",
  "status": "matched",
  "canonical_id": "trade:fob",
  "input": {"text": "FOB", "kind": "term", "normalized": "fob"}
}
```

## `POST /api/v1/explain/code-security`

Wrap a Unicode security scan in an OES payload.

Request:

```json
{"text":"vаlue = 1\n","source_name":"agent.py"}
```

Response excerpt:

```json
{
  "schema": "oes:0.1",
  "status": "unsafe",
  "input": {"text": "agent.py", "kind": "code", "normalized": "agent.py"},
  "safety": {
    "risk_level": "medium",
    "findings": [
      {
        "rule_id": "unicode-confusable",
        "unicode_hex": "U+0430",
        "confusable_with": "a",
        "suggested_action": "review",
        "auto_fixable": false
      }
    ]
  }
}
```

## `POST /api/v1/security/scan`

Return a developer-friendly Unicode Security Pack report without wrapping it in OES.

Request:

```json
{"text":"vаlue = 1\n","source_name":"agent.py"}
```

Response excerpt:

```json
{
  "status": "warn",
  "summary": {
    "finding_count": 1,
    "risk_level": "medium",
    "rule_counts": {"unicode-confusable": 1}
  },
  "findings": [
    {
      "rule_id": "unicode-confusable",
      "confusable_with": "a",
      "why_it_matters": "Cyrillic small letter a can look like Latin small letter a in identifiers.",
      "source_id": "source:unicode-confusables:minimal"
    }
  ]
}
```

## `POST /api/v1/audit/explain`

Return an explanation plus an audit event that records who queried what, what sources were used, and what remained unknown.

Request:

```json
{"actor_id":"user:alice","kind":"term","text":"FOB"}
```

Response excerpt:

```json
{
  "result": {"schema": "oes:0.1", "status": "matched", "canonical_id": "trade:fob"},
  "audit": {
    "schema": "omniglyph.audit:0.1",
    "actor": {"id": "user:alice"},
    "action": "explain_term",
    "status": "matched",
    "source_ids": ["..."],
    "unknowns": []
  }
}
```

Supported `kind` values are `glyph`, `term`, and `code`.

## `POST /api/v1/audit/security-scan`

Return a Unicode Security Pack scan plus an audit event.

Request:

```json
{"actor_id":"agent:codex","text":"vаlue = 1\n","source_name":"agent.py"}
```

Response excerpt:

```json
{
  "result": {"status": "warn", "summary": {"risk_level": "medium"}},
  "audit": {
    "action": "scan_unicode_security",
    "source_ids": ["source:unicode-confusables:minimal"],
    "findings": [{"rule_id": "unicode-confusable"}]
  }
}
```

## `POST /api/v1/normalize`

Normalize glyphs and terms.

Request:

```json
{"tokens":["铝","FOB","tempered glass","unknown"]}
```

Full response:

```json
{
  "results": [
    {"input":"铝","status":"matched","type":"glyph","canonical_id":"glyph:U+94DD","summary":{"unicode":"U+94DD","pinyin":"lǚ"}},
    {"input":"FOB","status":"matched","type":"trade_term","canonical_id":"trade:fob","summary":{"term":"FOB"}},
    {"input":"unknown","status":"unknown","type":null,"canonical_id":null,"summary":{}}
  ]
}
```

Compact mode:

```text
POST /api/v1/normalize?mode=compact
```

```json
{"known":{"铝":"glyph:U+94DD","FOB":"trade:fob"},"unknown":["unknown"]}
```

## `POST /api/v1/guardrail/validate-output`

Validate generated output terms before an agent sends an email, writes an ERP field, or calls a downstream system.

This endpoint is intentionally deterministic: it only checks whether candidate terms exist in the local lexical/domain fact base. Unknown terms are returned as `warn`, not auto-rewritten.

Request:

```json
{"terms":["FOB","tempered glass","HS 7604.99X"]}
```

Response:

```json
{
  "status": "warn",
  "known": {
    "FOB": "trade:fob",
    "tempered glass": "material:tempered_glass"
  },
  "unknown": ["HS 7604.99X"],
  "details": [
    {"term":"FOB","status":"known","canonical_id":"trade:fob","entry_type":"trade_term","source_name":"building_materials_example"},
    {"term":"HS 7604.99X","status":"unknown","canonical_id":null}
  ]
}
```

Suggested agent behavior:

- `pass`: continue normally.
- `warn`: ask for verification, route to human review, or regenerate with stricter constraints.
- `unknown`: treat as missing local fact, not as permission to invent an explanation.
