# Stage 1 Architecture

## Mission

Stage 1 builds the deterministic Symbol Fact Base for AI agents. It provides local, read-only, source-backed lookup for exact symbols and foundational lexical properties.

Stage 1 does not perform semantic reasoning. It prevents hallucination by giving agents a trusted place to ask:

```text
What is this symbol, according to traceable sources?
```

## Scope

Included:

- Unicode Character Database ingestion.
- Unihan ingestion for CJK properties.
- CLDR-ready source snapshot structure.
- Local database storage.
- Exact glyph lookup API.
- Source metadata in responses.
- NULL-safe records.

Excluded:

- AI-generated definitions.
- Automatic concept graph construction.
- Semantic computation.
- Unreviewed web scraping.
- Image OCR recognition.

## Subsystems

### Ingestion Pipeline

Responsible for acquiring structured source artifacts.

- Downloads full upstream files only.
- Stores raw source files under immutable source snapshots.
- Records source name, URL, version, retrieval timestamp, checksum, local path, and license notes.
- Does not filter, rewrite, summarize, or infer source content.

Initial source priority:

1. Unicode Character Database.
2. Unihan Database.
3. CLDR data.
4. Approved open dictionary dumps after license review.
5. Curated private domain packs.

### Normalization Reactor

Stage 1's reactor is deterministic normalization, not AI reasoning.

- Parses source rows.
- Maps fields into canonical nodes and property records.
- Emits NULL for unavailable fields.
- Skips malformed rows without stopping the whole ingestion job.
- Stores source provenance for every canonical property.
- Produces the same output for the same source snapshot.

### Omni-API

Responsible for stable read-only access by agents.

- Provides exact symbol lookup.
- Provides batch normalization in later Stage 1 releases.
- Returns structured JSON designed for tool calls.
- Does not mutate canonical data.
- Does not call generative AI for canonical values.

### Agent Adapter

Responsible for integrating Stage 1 with OpenClaw / AgentCore OS.

- Converts agent tool calls into Omni-API requests.
- Normalizes OCR or inquiry tokens in batch.
- Returns traceable records to the agent context.
- Keeps private query data local by default.

## Recommended Storage Model

Stage 1 may begin with SQLite for MVP and migrate to PostgreSQL for multi-agent deployment. Table design should remain PostgreSQL-compatible.

### `source_snapshot`

| Field | Type | Description |
| --- | --- | --- |
| `id` | UUID/TEXT | Source snapshot identifier. |
| `source_name` | TEXT | Human-readable source name. |
| `source_url` | TEXT | Download or reference URL. |
| `source_version` | TEXT | Release version or dump date. |
| `retrieved_at` | TIMESTAMP | Retrieval time. |
| `sha256` | TEXT | Raw artifact checksum. |
| `license` | TEXT | License or terms note. |
| `local_path` | TEXT | Immutable local file path. |

### `glyph_node`

| Field | Type | Description |
| --- | --- | --- |
| `uid` | UUID/TEXT | Stable glyph identifier. |
| `glyph` | TEXT | Exact symbol, such as `铝`. |
| `unicode_hex` | TEXT | Code point, such as `U+94DD`. |
| `unicode_version` | TEXT | Source Unicode version. |
| `name` | TEXT | Unicode character name when available. |
| `general_category` | TEXT | Unicode general category. |
| `script` | TEXT | Script property when available. |
| `block` | TEXT | Unicode block when available. |
| `created_at` | TIMESTAMP | Creation time. |
| `updated_at` | TIMESTAMP | Last update time. |

### `glyph_property`

| Field | Type | Description |
| --- | --- | --- |
| `id` | UUID/TEXT | Property row identifier. |
| `glyph_uid` | UUID/TEXT | Linked glyph. |
| `property_namespace` | TEXT | Source or domain namespace, such as `unicode` or `unihan`. |
| `property_name` | TEXT | Source-backed property name. |
| `property_value` | TEXT/JSON | Stored value. |
| `value_type` | TEXT | `string`, `number`, `json`, `list`, or `boolean`. |
| `language` | TEXT | BCP-47 language tag when applicable. |
| `source_id` | UUID/TEXT | Linked source snapshot. |
| `confidence` | REAL | Confidence score, normally `1.0` for official source fields. |

## API Contract

### Exact Glyph Lookup

Request:

```text
GET /api/v1/glyph?char=铝
```

Response principle:

```json
{
  "glyph": "铝",
  "unicode_hex": "U+94DD",
  "name": "CJK UNIFIED IDEOGRAPH-94DD",
  "properties": [
    {
      "namespace": "unihan",
      "name": "kMandarin",
      "value": "lǚ",
      "language": "zh-Latn-pinyin",
      "status": "canonical",
      "source_id": "..."
    }
  ],
  "unknowns": ["etymology_tree", "computable_traits"],
  "sources": [
    {
      "id": "...",
      "source_name": "Unicode Character Database",
      "source_version": "...",
      "source_field": "Name"
    }
  ]
}
```

### Batch Normalization

Deferred Stage 1.2 contract, not required for MVP v0.1. The endpoint is documented now so the v0.1 data model does not block it later.

Stage 1.2 target request:

```text
POST /api/normalize/batch
```

Request body:

```json
{
  "tokens": ["铝", "aluminium", "FOB", "กระจก"],
  "context": "cross_border_inquiry"
}
```

The `context` value is an optional routing hint. In Stage 1.2 it may select a mounted namespace such as `global`, `trade`, `building_materials`, or `ocr_cleanup`; unknown contexts must be ignored safely and must not change canonical global facts.

Response body should preserve per-token status:

```json
{
  "results": [
    {"token": "铝", "status": "matched", "type": "glyph"},
    {"token": "aluminium", "status": "matched", "type": "lexical_entry"},
    {"token": "FOB", "status": "matched", "type": "trade_abbreviation"},
    {"token": "กระจก", "status": "unknown", "type": null}
  ]
}
```

## Failure Discipline

- Invalid query input returns 400.
- Unknown but valid Unicode characters return 404 only if absent from the local base.
- Missing attributes inside known records return NULL or appear under `unknowns`.
- One malformed source row must not stop ingestion.
- Candidate or LLM-suggested data must never be returned as canonical.

## Performance Targets

- Single glyph lookup P95 under 20 ms on local development hardware.
- API must start without network access.
- Ingestion must be restartable and deterministic.
- Source downloads are explicit commands, never hidden API startup behavior. Ingestion commands must require either `--source` for local files or an explicit `download-source` command before parsing.

## Stage 1 Acceptance Checklist

- Unicode source snapshot stored with checksum.
- Unicode glyph records imported.
- Unihan properties imported for supported CJK records.
- `GET /api/v1/glyph` returns source-backed JSON.
- Missing fields are NULL-safe.
- Tests cover malformed source rows.
- No generative model writes canonical fields.
- Local deployment works without external runtime dependencies.


## Multi-Source Conflict Policy

Stage 1 uses append-only property records. New source facts must not overwrite existing source facts. If two sources provide different values for the same property, both values are stored with separate `source_id`, `confidence`, and retrieval metadata. Resolver logic may choose a preferred display value at API time, but raw canonical property rows remain source-separated.

Conflict handling rules:

- `glyph_node` stores stable identity fields only.
- `glyph_property` stores source-backed properties and may contain multiple values for the same glyph/property pair from different sources.
- Upserts are allowed only for deterministic identity rows and exact duplicate source-property rows.
- Source history is append-only through `source_snapshot`; updated upstream files create new snapshots, not replacements.

## Migration Policy

SQLite is the MVP runtime. PostgreSQL is the multi-agent and semantic-topology runtime. Schema design must keep these migration constraints:

- Use text UUIDs in SQLite that map directly to PostgreSQL `uuid`.
- Store JSON as text in SQLite and `jsonb` in PostgreSQL.
- Keep vector fields out of MVP tables until pgvector is introduced.
- Maintain migrations as versioned SQL files under `migrations/` once implementation begins.
- Never rely on SQLite-only behavior for conflict resolution.

## SQLite Concurrency Policy

MVP SQLite deployments must enable WAL mode and bounded busy timeouts for concurrent agent reads. Write-heavy ingestion should run as an explicit offline job, not during live agent query serving.
