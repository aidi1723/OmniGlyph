# OmniGlyph Development Handbook

## Engineering Mission

Build a deterministic, local-first, source-traceable symbol infrastructure for AI agents.

Every engineering decision must serve one question:

```text
Can an agent safely use this value to make a downstream decision?
```

If the answer is no, the value must be excluded from canonical storage, marked as candidate data, or assigned lower confidence with explicit provenance.

## Core Principles

### 1. Facts Before Fluency

Readable prose is secondary. Structured, source-backed facts are primary.

Canonical data should prefer:

```json
{
  "property_name": "kMandarin",
  "property_value": "lǚ",
  "source_name": "Unihan",
  "source_version": "...",
  "source_field": "kMandarin"
}
```

over polished explanations without provenance.

### 2. LLMs Cannot Write Canonical Facts

LLMs may be used only for this allowlist:

- parser development
- documentation
- candidate extraction into non-canonical candidate tables
- duplicate detection suggestions
- natural-language explanations of already sourced facts
- workflow orchestration
- test fixture generation when fixtures are clearly marked synthetic

LLMs must not directly populate canonical definitions, pronunciations, etymologies, concept relations, computable traits, confidence scores, or source metadata.

### 3. Raw Sources Are Immutable

Downloaded source artifacts must be stored unchanged.

Required metadata:

- source name
- source URL
- source version or release date
- retrieval timestamp
- checksum
- license notes
- local path

### 4. NULL Is Safer Than Guessing

Sparse records are expected. A glyph with only Unicode code point and category is still useful.

Never backfill missing fields through intuition, model output, or unreviewed web snippets.

### 5. Separate Layers Cleanly

Do not collapse glyphs, words, and concepts into one table.

Required conceptual separation:

```text
glyph_node: exact written symbol
lexical_entry: language-specific word or term
concept_node: real-world concept
computable_trait: task-relevant structured property
```

### 6. Every Relationship Needs a Reason

Edges such as synonymy, variant relation, concept mapping, or risk implication must carry:

- source or rule ID
- confidence
- creation method
- reviewer status when applicable

### 7. Local-First Deployment

The default deployment target is private infrastructure. External services are optional accelerators, not runtime dependencies for core lookup.

## System Architecture

### Ingestion Pipeline

Purpose: acquire and preserve source artifacts.

Responsibilities:

- download full source datasets through explicit commands only
- verify checksums
- record source metadata
- store immutable raw files
- schedule source refreshes

Non-responsibilities:

- semantic inference
- AI enrichment
- business decision logic

### Normalization Reactor

Purpose: convert raw source records into canonical structures.

Responsibilities:

- parse source formats
- map fields to internal properties
- validate types
- emit NULL for missing values
- preserve source references
- produce deterministic output

Non-responsibilities:

- polishing definitions
- merging meanings without explicit rules
- creating unsupported concept links

### Omni-API

Purpose: expose stable local interfaces for agents.

Minimum endpoints:

```text
GET /api/v1/glyph?char=铝
POST /api/normalize/batch  # Stage 1.2, not MVP v0.1
GET /api/source/{source_id}
```

Future endpoints:

```text
GET /api/term?text=aluminium&lang=en
GET /api/concept/{id}
POST /api/compute/risk
```

### Agent Adapter Layer

Purpose: integrate with OpenClaw / AgentCore OS.

Responsibilities:

- tool-call schema for agents
- batch normalization helper
- OCR cleanup integration
- inquiry parsing integration
- trace display for agent decisions

## Data Model Guidelines

### `source_snapshot`

Stores source identity and immutable retrieval metadata.

Required fields:

```text
id
source_name
source_url
source_version
retrieved_at
sha256
license
local_path
```

### `glyph_node`

Stores exact symbols.

Required fields:

```text
uid
glyph
unicode_hex
unicode_version
name
general_category
script
block
created_at
updated_at
```

### `glyph_property`

Stores extensible source-backed properties.

Required fields:

```text
id
glyph_uid
property_namespace
property_name
property_value
value_type
language
source_id
confidence
```

### `lexical_entry`

Stores language-specific words, terms, abbreviations, and aliases.

Required fields:

```text
id
text
normalized_text
language
script
entry_type
source_id
confidence
```

### `concept_node`

Stores real-world concepts after Stage 2 begins.

Required fields:

```text
uid
canonical_label
concept_type
description
embedding
created_at
updated_at
```

### `concept_edge`

Stores explainable relationships.

Required fields:

```text
id
from_id
to_id
relation_type
source_id
rule_id
confidence
review_status
```

### `computable_trait`

Stores structured task-relevant attributes.

Required fields:

```text
id
concept_id
trait_namespace
trait_name
trait_value
value_type
source_id
rule_id
confidence
```

## Source Priority

Recommended source classes:

1. Official standards: Unicode, Unihan, CLDR.
2. Structured open dictionaries with clear licenses.
3. Curated private domain lexicons.
4. Reviewed expert annotations.
5. LLM candidates awaiting review.

Only classes 1–4 may write canonical facts. Class 5 must stay in candidate tables.

## MVP Development Flow

### Phase 0: Product Boundary Freeze

Deliverables:

- accepted data sources
- license notes
- schema v0.1
- API contract
- forbidden-data policy
- local deployment target

### Phase 1: Unicode Base

Deliverables:

- Unicode source downloader
- source snapshot table
- UnicodeData parser
- glyph lookup API
- tests for malformed rows and NULL fields

### Phase 2: Unihan Enrichment

Deliverables:

- Unihan parser
- CJK property ingestion
- pronunciation and definition properties
- variant and stroke properties
- source-backed API response expansion

### Phase 3: Agent Batch Normalization

Deliverables:

- batch input endpoint
- per-token normalization result
- unknown-token reporting
- provenance summary
- OpenClaw / AgentCore adapter prototype

### Phase 4: Private Domain Pack

Deliverables:

- building-material term schema
- logistics and trade abbreviation pack
- multilingual aliases for priority markets
- reviewed import workflow
- conflict detection report

### Phase 5: Concept and Trait Prototype

Deliverables:

- concept node model
- alias edges
- computable traits for materials and logistics
- explainable risk prototype

## API Response Rules

Every response should distinguish these categories:

```text
canonical: source-backed accepted fact
candidate: machine-suggested or unreviewed value
missing: known unknown / NULL
computed: derived by explicit rule or model path
```

Example response principle:

```json
{
  "glyph": "铝",
  "unicode_hex": "U+94DD",
  "properties": [
    {
      "name": "kMandarin",
      "value": "lǚ",
      "status": "canonical",
      "source": "Unihan"
    }
  ],
  "unknowns": ["etymology_tree", "computable_traits"]
}
```

## Testing Requirements

Minimum test coverage:

- parser accepts valid source rows
- parser skips malformed rows without crashing
- parser preserves NULL for absent fields
- ingestion is deterministic for the same source file
- API rejects invalid input
- API returns 404 for absent records
- API includes source metadata for canonical facts
- candidate data cannot appear as canonical data

## Security and Privacy Requirements

- Local lookup must not require external APIs.
- Private domain lexicons must not be uploaded by default.
- Query logs must be configurable and redactable.
- Sensitive customer or supplier terms must be separated from public source data.
- Agent integrations must expose trace IDs without leaking private payloads.

## Performance Targets

MVP local targets:

- single glyph lookup P95 under 20 ms
- batch normalization of 1,000 tokens under 1 second on local development hardware
- source ingestion resumable after malformed rows
- API startup without downloading remote data

Future private infrastructure targets:

- million-scale local symbol comparison jobs
- offline operation on N100-class nodes
- cached batch normalization for recurring product and inquiry corpora

## Definition of Done

A feature is done only when:

- source provenance is stored
- missing values are represented safely
- tests cover malformed and empty cases
- API output is stable and documented
- no LLM-generated value enters canonical storage
- local operation works without network dependency
- downstream agent usage is clear

## Anti-Patterns

Do not:

- scrape random dictionary pages as canonical truth
- merge glyph, word, and concept records into one entity
- hide source conflicts
- overwrite raw source artifacts
- use generated explanations as facts
- optimize UI before stabilizing API contracts
- add vectors before source-backed symbolic fields are reliable
- promise universal semantic computation before a vertical domain proves value


## Private Domain Isolation

Private domain packs must be mounted as separate namespaces rather than merged into global standards data.

Required isolation fields:

```text
namespace
visibility
owner
source_id
access_policy
```

Recommended namespaces:

```text
global_unicode
global_unihan
global_cldr
private_building_materials
private_trade_terms
private_customer_terms
```

Rules:

- Private terms may enrich API responses only when the caller has access to that namespace.
- Private facts must not overwrite global Unicode/Unihan/CLDR facts.
- API responses must show whether a field came from global standards or private domain packs.
- Export jobs must be able to exclude private namespaces.

## Engineering Infrastructure Requirements

Before the first runnable release, the repository must include:

- `Dockerfile` for local API serving.
- `docker-compose.yml` for API plus optional PostgreSQL.
- `.github/workflows/test.yml` or equivalent CI running tests.
- `LICENSE` for project code.
- `NOTICE.md` or `docs/legal/data-sources.md` for upstream data terms.
- `CHANGELOG.md` using semantic versioning.
- `migrations/` for versioned schema changes once code starts.

## Benchmark Requirements

MVP must include a benchmark script before performance claims are made. Minimum checks:

- single glyph lookup latency
- 1,000-token batch normalization latency once Stage 1.2 is implemented
- SQLite read concurrency under WAL mode
- ingestion throughput for sample and full Unicode files
