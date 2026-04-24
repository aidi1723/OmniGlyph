# OmniGlyph API Reference

Base URL for local development:

```text
http://127.0.0.1:8000
```

## `GET /api/v1/health`

Returns service status.

Response:

```json
{"status":"ok","service":"omniglyph","version":"0.2.0b0"}
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
