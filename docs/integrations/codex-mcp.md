# Codex MCP Integration

This guide connects OmniGlyph to Codex-style agent workflows through the stdio MCP server.

## 1. Install OmniGlyph

From the project root:

```bash
UV_CACHE_DIR=.uv-cache uv venv .venv --python 3.11
UV_CACHE_DIR=.uv-cache uv pip install -e '.[dev]'
```

## 2. Import Example Data

```bash
.venv/bin/omniglyph ingest-unicode --source tests/fixtures/UnicodeData.sample.txt --source-version fixture
.venv/bin/omniglyph ingest-domain-pack --source examples/domain-packs/building_materials.csv --namespace private_building_materials --source-version example
.venv/bin/omniglyph ingest-domain-pack --source examples/domain-packs/software_development.csv --namespace public_software_development --source-version 0.1.0
```

For real Unicode data:

```bash
.venv/bin/omniglyph download-unicode
.venv/bin/omniglyph ingest-unicode --source data/raw/UnicodeData.txt --source-version latest
```

## 3. MCP Server Command

Use the installed console script:

```bash
/Users/aidi/万象文枢/.venv/bin/omniglyph-mcp
```

Or module mode:

```bash
/Users/aidi/万象文枢/.venv/bin/python -m omniglyph.mcp_server
```

## 4. Example MCP Configuration

Use this shape in a Codex-compatible MCP config file:

```json
{
  "mcpServers": {
    "omniglyph": {
      "command": "/Users/aidi/万象文枢/.venv/bin/omniglyph-mcp",
      "cwd": "/Users/aidi/万象文枢"
    }
  }
}
```

If using module mode:

```json
{
  "mcpServers": {
    "omniglyph": {
      "command": "/Users/aidi/万象文枢/.venv/bin/python",
      "args": ["-m", "omniglyph.mcp_server"],
      "cwd": "/Users/aidi/万象文枢",
      "env": {
        "PYTHONPATH": "/Users/aidi/万象文枢/src"
      }
    }
  }
}
```

## 5. Available Tools

### `lookup_glyph`

Input:

```json
{"char": "铝"}
```

Use when the agent needs deterministic Unicode/Unihan facts for one character.

### `lookup_term`

Input:

```json
{"text": "FOB"}
```

Use when the agent needs a private/domain term such as trade terms or building-material terms.

### `explain_glyph`

Input:

```json
{"char": "铝"}
```

Use when the agent needs an OES payload with source-backed glyph facts.

### `explain_term`

Input:

```json
{"text": "API"}
```

Use when the agent needs an OES payload for a domain term.

### `explain_code_security`

Input:

```json
{"text": "vаlue = 1\n", "source_name": "agent.py"}
```

Use when Unicode security findings should be returned under `safety.findings`.

### `normalize_tokens`

Input:

```json
{"tokens": ["铝", "FOB", "tempered glass", "unknown"], "mode": "compact"}
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

### `scan_unicode_security`

Input:

```json
{"text": "vаlue = 1\n", "source_name": "agent.py"}
```

Use before editing copied code or suspicious diffs. Findings include `confusable_with`, `why_it_matters`, `source_id`, and review guidance.

### `audit_explain`

Input:

```json
{"actor_id": "agent:codex", "kind": "term", "text": "API"}
```

Use when a workflow needs to show who checked a term, which source backed it, and what remained unknown.

## 6. Recommended Agent Rule

Before interpreting unknown symbols, trade terms, software-development terms, or suspicious Unicode source code, call OmniGlyph first. Use returned canonical IDs and treat `unknown` or `null` fields as missing facts, not as a reason to guess.
