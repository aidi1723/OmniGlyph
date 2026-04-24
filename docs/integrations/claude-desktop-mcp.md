# Claude Desktop MCP Integration

This guide shows the same stdio MCP server shape for Claude Desktop-style clients.

## Prerequisites

Install OmniGlyph locally:

```bash
UV_CACHE_DIR=.uv-cache uv venv .venv --python 3.11
UV_CACHE_DIR=.uv-cache uv pip install -e '.[dev]'
```

Import example data:

```bash
.venv/bin/omniglyph ingest-unicode --source tests/fixtures/UnicodeData.sample.txt --source-version fixture
.venv/bin/omniglyph ingest-domain-pack --source examples/domain-packs/building_materials.csv --namespace private_building_materials --source-version example
```

## MCP Server Configuration

Add a server entry similar to:

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

Restart the MCP client after changing configuration.

## Smoke Test

The client should discover three tools:

- `lookup_glyph`
- `lookup_term`
- `normalize_tokens`

Try:

```json
{"tokens": ["铝", "FOB", "tempered glass", "unknown"], "mode": "compact"}
```

Expected idea:

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

## Usage Boundary

OmniGlyph v0.2 beta features are for deterministic lookup and normalization. They do not replace LLM reasoning, translation, OCR, or business decision logic. Missing data must remain missing.
