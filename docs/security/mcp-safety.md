# MCP Safety Notes

OmniGlyph is designed as a local, deterministic, read-only fact layer for agents.

## Security Posture

The stdio MCP server exposes lookup and scanning tools only. It does not provide tools for shell execution, file modification, network calls, credential access, browser automation, or database mutation.

## Tool Boundaries

| Tool | Reads local DB | Reads provided text | Writes files | Executes shell | Network by default |
| --- | --- | --- | --- | --- | --- |
| `lookup_glyph` | yes | no | no | no | no |
| `lookup_term` | yes | no | no | no | no |
| `explain_glyph` | yes | no | no | no | no |
| `explain_term` | yes | provided text | no | no | no |
| `normalize_tokens` | yes | provided tokens | no | no | no |
| `validate_output_terms` | yes | provided terms | no | no | no |
| `scan_code_symbols` | no | provided text | no | no | no |

## Data Handling

- MCP inputs are processed locally in the server process.
- The server does not send tool inputs to external services.
- The server does not persist MCP request payloads.
- Lookup results come from the local SQLite database and imported source snapshots.
- Unknown values remain `unknown` or `null`; the server does not generate definitions.

## Recommended Deployment

- Run OmniGlyph MCP from a trusted local virtual environment.
- Import only data sources whose licenses and provenance you understand.
- Keep private domain packs separated from global Unicode facts.
- Use filesystem permissions to protect private SQLite databases.
- Prefer read-only mounted data volumes in containers when possible.

## Agent Policy

Recommended system instruction for MCP clients:

```text
OmniGlyph is a deterministic lookup, explanation, and scanning tool. Use it to verify symbols, terms, and suspicious Unicode code characters. Do not ask it to execute code, modify files, browse the web, or invent missing definitions. Treat unknown results as missing facts.
```

## Known Limitations

- `scan_code_symbols` detects suspicious Unicode patterns, but it is not a complete security scanner.
- Homoglyph detection is rule-based in the current beta; full Unicode confusables data is a future enhancement.
- The server trusts the local database. Data-source integrity depends on explicit ingestion and source tracking.
