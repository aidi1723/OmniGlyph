# Claude Code MCP Integration

This guide connects OmniGlyph to Claude Code-style workflows through the local stdio MCP server.

## Install for Local Development

```bash
UV_CACHE_DIR=.uv-cache uv venv .venv --python 3.11
UV_CACHE_DIR=.uv-cache uv pip install -e '.[dev]'
```

## MCP Server Command

Use the console script:

```bash
/absolute/path/to/OmniGlyph/.venv/bin/omniglyph-mcp
```

Or module mode:

```bash
/absolute/path/to/OmniGlyph/.venv/bin/python -m omniglyph.mcp_server
```

## Project MCP Config Shape

Use this shape in a Claude Code-compatible MCP config:

```json
{
  "mcpServers": {
    "omniglyph": {
      "command": "/absolute/path/to/OmniGlyph/.venv/bin/omniglyph-mcp",
      "cwd": "/absolute/path/to/OmniGlyph"
    }
  }
}
```

Module-mode fallback:

```json
{
  "mcpServers": {
    "omniglyph": {
      "command": "/absolute/path/to/OmniGlyph/.venv/bin/python",
      "args": ["-m", "omniglyph.mcp_server"],
      "cwd": "/absolute/path/to/OmniGlyph",
      "env": {
        "PYTHONPATH": "/absolute/path/to/OmniGlyph/src"
      }
    }
  }
}
```

## Coding-Agent Use Case

Ask Claude Code to call `scan_code_symbols` before debugging copied code, invisible syntax errors, suspicious diffs, or homoglyph risks.

Example suspicious text:

```json
{"text":"def calculate_vаlue(x):\n    return x * 2\n","source_name":"bug.py"}
```

Expected finding:

```json
{
  "rule_id": "unicode-cross-script-homoglyph-risk",
  "unicode_hex": "U+0430",
  "name": "CYRILLIC SMALL LETTER A"
}
```

## Agent Rule

Use OmniGlyph as a deterministic symbol-perception layer. Claude Code should still reason about fixes, but it should not guess what a suspicious physical character is.
