# Security, Dictionary, and Audit Workflow

This workflow is the first v0.6 moat slice: a developer or agent can scan Unicode risks, explain domain terms, and emit an audit event showing what was checked and what remains unknown.

## 1. Scan Unicode Security

```bash
omniglyph scan-code src/ --format json
```

Findings include fields that are meant to be readable without Unicode expertise:

- `rule_id`: stable rule such as `unicode-confusable`
- `confusable_with`: the visible ASCII-like character when known
- `why_it_matters`: short developer explanation
- `suggested_action`: usually `review`
- `auto_fixable`: false by default because OmniGlyph does not mutate source code automatically
- `source_id`: provenance for the rule or Unicode database

For agents, prefer the MCP tool `scan_unicode_security`.

## 2. Explain with OES

Use OES when the result needs to be passed between systems:

```json
{"text":"vаlue = 1\n","source_name":"agent.py"}
```

Call `explain_code_security` and read:

- `schema`: `oes:0.1`
- `status`: `unsafe` when findings exist
- `safety.risk_level`: `none`, `medium`, or `high`
- `safety.findings`: source-backed Unicode findings
- `sources`: source records for the findings
- `limits`: what the scan does not prove

## 3. Load Software Development Terms

The starter pack lives at:

```text
examples/domain-packs/software_development.csv
```

It is also packaged as `omniglyph.domain_packs/software_development.csv` for wheel installs.

Ingest it with:

```bash
omniglyph ingest-domain-pack --source examples/domain-packs/software_development.csv --namespace public_software_development
```

It includes terms such as `API`, `SDK`, `MCP`, `RAG`, `SQL injection`, `XSS`, `Unicode confusable`, and `Trojan Source`.

## 4. Emit Audit Evidence

When an enterprise workflow needs traceability, call `/api/v1/audit/explain` or MCP `audit_explain`.

Example:

```json
{"actor_id":"user:alice","kind":"term","text":"API"}
```

The audit event records:

- who queried: `actor.id`
- what was checked: `input`
- what happened: `status` and `canonical_id`
- what sources supported it: `source_ids`
- what remains unresolved: `unknowns`
- what safety findings appeared: `findings`
