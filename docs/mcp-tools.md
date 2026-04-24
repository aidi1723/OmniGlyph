# OmniGlyph MCP Tools

OmniGlyph exposes a minimal stdio MCP server for local agent workflows.

Run:

```bash
omniglyph-mcp
```

## Tool: `lookup_glyph`

Input:

```json
{"char":"铝"}
```

Returns glyph facts from `/api/v1/glyph` equivalent data.

## Tool: `lookup_term`

Input:

```json
{"text":"FOB"}
```

Returns lexical/domain term data.

## Tool: `normalize_tokens`

Input:

```json
{"tokens":["铝","FOB","tempered glass","unknown"],"mode":"compact"}
```

Compact output:

```json
{
  "known": {
    "铝": "glyph:U+94DD",
    "FOB": "trade:fob",
    "tempered glass": "material:tempered_glass"
  },
  "unknown": ["unknown"]
}
```

## Tool: `validate_output_terms`

Input:

```json
{"terms":["FOB","tempered glass","HS 7604.99X"]}
```

Output:

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

Use this as the output guardrail layer in Sandwich Architecture. Unknown generated terms should be reviewed, regenerated, or blocked before they reach customers or production systems.

## Agent Rule

Before interpreting unknown symbols, trade terms, or building-material terms, call OmniGlyph first. Treat `unknown` and `null` as missing facts, not as permission to hallucinate.
