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

## Tool: `explain_glyph`

Input:

```json
{"char":"铝"}
```

Returns an OmniGlyph Explanation Standard v0.1 payload with `schema: "oes:0.1"`, source-backed basic facts, lexical facts when available, safety findings, sources, and explicit limits.

## Tool: `explain_term`

Input:

```json
{"text":"FOB"}
```

Returns an OES v0.1 payload for a lexical/domain term. Unknown terms return `status: "unknown"` and do not invent definitions.

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

## Tool: `scan_code_symbols`

Input:

```json
{"text":"vаlue = 1\n","source_name":"agent.py"}
```

Returns a code-symbol scan report for invisible Unicode controls, Bidi controls, and cross-script homoglyph risks. Use it before an agent edits copied code, reviews suspicious diffs, or explains compiler errors that may be caused by hidden characters.

## Agent Rule

Before interpreting unknown symbols, trade terms, or building-material terms, call OmniGlyph first. Treat `unknown` and `null` as missing facts, not as permission to hallucinate.
