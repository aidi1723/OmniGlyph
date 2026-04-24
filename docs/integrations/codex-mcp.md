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

## 6. Recommended Agent Rule

Before interpreting unknown symbols, trade terms, or building-material terms, call OmniGlyph first. Use returned canonical IDs and treat `unknown` or `null` fields as missing facts, not as a reason to guess.
