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

## Tool: `explain_code_security`

Input:

```json
{"text":"vаlue = 1\n","source_name":"agent.py"}
```

Returns an OES v0.1 payload for source-code Unicode security findings. Unsafe code snippets use `status: "unsafe"` and put the rule evidence under `safety.findings`.

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

## Tool: `enforce_grounded_output`

Input:

```json
{"terms":["FOB","HS 7604.99X"],"actor_id":"agent:quote"}
```

Output:

```json
{
  "schema": "omniglyph.guardrail:0.1",
  "mode": "strict_source_grounding",
  "decision": "block",
  "status": "warn",
  "known": {"FOB": "trade:fob"},
  "unknown": ["HS 7604.99X"],
  "source_ids": ["..."],
  "limits": ["Unknown terms must be reviewed or removed before model output is trusted."],
  "audit": {
    "schema": "omniglyph.audit:0.1",
    "actor": {"id": "agent:quote"},
    "action": "enforce_grounded_output"
  }
}
```

Use this as the stricter Deterministic MCP Guardrail mode. `validate_output_terms` reports known and unknown terms; `enforce_grounded_output` turns that evidence into an allow/block decision.

## Tool: `scan_code_symbols`

Input:

```json
{"text":"vаlue = 1\n","source_name":"agent.py"}
```

Returns a code-symbol scan report for invisible Unicode controls, Bidi controls, and cross-script homoglyph risks. Use it before an agent edits copied code, reviews suspicious diffs, or explains compiler errors that may be caused by hidden characters.

## Tool: `scan_unicode_security`

Input:

```json
{"text":"vаlue = 1\n","source_name":"agent.py"}
```

Returns the same scan engine with Unicode Security Pack fields designed for developer review:

```json
{
  "status": "warn",
  "summary": {"risk_level": "medium", "rule_counts": {"unicode-confusable": 1}},
  "findings": [
    {
      "rule_id": "unicode-confusable",
      "confusable_with": "a",
      "suggested_action": "review",
      "auto_fixable": false,
      "source_id": "source:unicode-confusables:minimal"
    }
  ]
}
```

## Tool: `audit_explain`

Input:

```json
{"actor_id":"user:alice","kind":"term","text":"FOB"}
```

Returns:

```json
{
  "result": {"schema": "oes:0.1", "status": "matched", "canonical_id": "trade:fob"},
  "audit": {
    "schema": "omniglyph.audit:0.1",
    "actor": {"id": "user:alice"},
    "action": "explain_term",
    "source_ids": ["..."],
    "unknowns": []
  }
}
```

Use this when an enterprise workflow needs evidence that an agent queried OmniGlyph before acting.

## Agent Rule

Before interpreting unknown symbols, trade terms, or building-material terms, call OmniGlyph first. Treat `unknown` and `null` as missing facts, not as permission to hallucinate.
