# Claude Desktop MCP Integration

OmniGlyph exposes a local stdio MCP server for Claude Desktop. It gives Claude deterministic symbol lookup, domain-term normalization, output guardrail checks, and code-symbol scanning without sending data to a remote OmniGlyph service.

## 1. Install OmniGlyph

From the project root:

```bash
UV_CACHE_DIR=.uv-cache uv venv .venv --python 3.11
UV_CACHE_DIR=.uv-cache uv pip install -e '.[dev]'
```

For a future packaged install, the intended shape is:

```bash
pipx install omniglyph
```

## 2. Import Example Data

```bash
.venv/bin/omniglyph ingest-unicode --source tests/fixtures/UnicodeData.sample.txt --source-version fixture
.venv/bin/omniglyph ingest-domain-pack --source examples/domain-packs/building_materials.csv --namespace private_building_materials --source-version example
```

## 3. Configure Claude Desktop

Add OmniGlyph to the Claude Desktop MCP configuration file.

Local development configuration:

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

Restart Claude Desktop after editing the config.

## 4. Smoke Test

From the project root:

```bash
printf '{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n' | .venv/bin/omniglyph-mcp
```

Expected tools:

- `lookup_glyph`
- `lookup_term`
- `explain_glyph`
- `explain_term`
- `explain_code_security`
- `normalize_tokens`
- `validate_output_terms`
- `scan_code_symbols`
- `scan_unicode_security`
- `audit_explain`

## 5. Recommended Claude Prompt

```text
Before interpreting unknown Unicode symbols, trade terms, suspicious source code characters, or enterprise audit-sensitive checks, call OmniGlyph first. Treat unknown results as missing facts, not as permission to guess.
```

## 6. Example Tool Uses

Look up a glyph:

```json
{"char":"铝"}
```

Normalize domain tokens:

```json
{"tokens":["铝","FOB","tempered glass","unknown"],"mode":"compact"}
```

Scan suspicious code text:

```json
{"text":"vаlue = 1\n","source_name":"agent.py"}
```

## Safety Boundary

OmniGlyph MCP is read-only by design. It does not execute shell commands, edit files, call external APIs by default, or automatically rewrite model output. See `docs/security/mcp-safety.md`.
