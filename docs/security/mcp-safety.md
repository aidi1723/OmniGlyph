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
| `explain_code_security` | no | provided text | no | no | no |
| `normalize_tokens` | yes | provided tokens | no | no | no |
| `validate_output_terms` | yes | provided terms | no | no | no |
| `enforce_grounded_output` | yes | provided terms | no | no | no |
| `scan_code_symbols` | no | provided text | no | no | no |
| `scan_unicode_security` | no | provided text | no | no | no |
| `scan_language_input` | no | provided text | no | no | no |
| `scan_output_dlp` | optional for secret lexicon terms | provided text | no | no | no |
| `enforce_intent` | no | provided manifest | no | no | no |
| `audit_explain` | yes for glyph/term | provided text | no | no | no |

## Data Handling

- MCP inputs are processed locally in the server process.
- The server does not send tool inputs to external services.
- The server does not persist MCP request payloads.
- Lookup results come from the local SQLite database and imported source snapshots.
- Unknown values remain `unknown` or `null`; the server does not generate definitions.
- Audit events are returned to the caller but are not persisted by the MCP server.
- Guardrail decisions are deterministic allow/block evidence for checked terms; they do not rewrite output automatically.
- Language Security Gateway tools return scan, redaction, or intent decisions only. They do not execute commands, send network requests, or persist secrets.

## Recommended Deployment

- Run OmniGlyph MCP from a trusted local virtual environment.
- Import only data sources whose licenses and provenance you understand.
- Keep private domain packs separated from global Unicode facts.
- Use filesystem permissions to protect private SQLite databases.
- Prefer read-only mounted data volumes in containers when possible.

## Agent Policy

Recommended system instruction for MCP clients:

```text
OmniGlyph is a deterministic lookup, explanation, scanning, source-grounding, and language-security tool. Use it to verify symbols, terms, generated output terms, suspicious Unicode code characters, untrusted natural-language input, outbound text, and requested action intents. Do not ask it to execute code, modify files, browse the web, or invent missing definitions. Treat unknown results as missing facts and treat guardrail or language-security `block` decisions as a stop condition for delivery or execution.
```

## Known Limitations

- `scan_code_symbols` and `scan_unicode_security` detect suspicious Unicode patterns, but they are not complete security scanners.
- `scan_language_input` and `scan_output_dlp` are deterministic security checks, not complete prompt-injection or DLP products.
- `enforce_intent` validates manifest policy but does not replace OS sandboxing, IAM, approval workflows, or endpoint security.
- Confusable detection uses a minimal bundled map in the current beta; full Unicode confusables ingestion is a future enhancement.
- The server trusts the local database. Data-source integrity depends on explicit ingestion and source tracking.
