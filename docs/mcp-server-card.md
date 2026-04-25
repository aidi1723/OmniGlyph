# OmniGlyph MCP Server Card

## Name

OmniGlyph

## Summary

A local-first Symbol Ground Truth MCP server for AI agents. OmniGlyph provides deterministic Unicode glyph lookup, private/domain term normalization, output term validation, and code-symbol linting for invisible Unicode and homoglyph risks.

## Repository

https://github.com/aidi1723/OmniGlyph

## License

Apache License 2.0

## Server Type

- Transport: stdio
- Runtime: Python 3.10+
- Network: not required by default
- Storage: local SQLite by default

## Install

Local development:

```bash
UV_CACHE_DIR=.uv-cache uv venv .venv --python 3.11
UV_CACHE_DIR=.uv-cache uv pip install -e '.[dev]'
```

Run:

```bash
.venv/bin/omniglyph-mcp
```

Future packaged install target:

```bash
pipx install omniglyph
omniglyph-mcp
```

## MCP Configuration

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

## Tools

### `lookup_glyph`

Looks up one Unicode character in the local symbol fact base.

Input:

```json
{"char":"铝"}
```

### `lookup_term`

Looks up a private or curated lexical/domain term.

Input:

```json
{"text":"FOB"}
```

### `explain_glyph`

Explains one Unicode character using OmniGlyph Explanation Standard v0.1.

Input:

```json
{"char":"铝"}
```

### `explain_term`

Explains a private or curated lexical/domain term using OmniGlyph Explanation Standard v0.1.

Input:

```json
{"text":"FOB"}
```

### `normalize_tokens`

Normalizes glyphs and domain terms into canonical IDs.

Input:

```json
{"tokens":["铝","FOB","tempered glass","unknown"],"mode":"compact"}
```

### `validate_output_terms`

Checks generated output terms against the local fact base before customer or downstream system delivery.

Input:

```json
{"terms":["FOB","tempered glass","HS 7604.99X"]}
```

### `scan_code_symbols`

Scans source code text for invisible Unicode controls, Bidi controls, unexpected controls, and cross-script homoglyph risks.

Input:

```json
{"text":"vаlue = 1\n","source_name":"agent.py"}
```

## Primary Use Cases

- Claude Desktop / Claude Code deterministic Unicode lookup
- code-symbol linting before agents edit copied or generated code
- RAG preprocessing for multilingual/domain terms
- output guardrail checks for generated trade/material terms
- local private domain glossary lookup

## Safety Notes

- Read-only MCP tools.
- No shell execution.
- No automatic file edits.
- No remote API calls by default.
- Local SQLite storage.
- Missing values remain explicit `null` or `unknown` rather than model guesses.

## Suggested Agent Instruction

```text
Use OmniGlyph before interpreting unknown Unicode symbols, domain terms, suspicious copied code, or generated output terms. Treat unknown results as missing facts, not as permission to hallucinate.
```
