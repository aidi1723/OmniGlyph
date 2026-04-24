# OmniGlyph（万象文枢）

[中文文档 / Chinese README](README.zh-CN.md)

> AI Agent 的全球符号真值层。  
> The Symbol Ground Truth Layer for AI Agents.

OmniGlyph is not a dictionary for human reading. It is a local-first, source-traceable, machine-computable symbol infrastructure for AI agents, automation systems, and future semantic operating layers.

Its core philosophy is:

> 字符即封装，语义即运算。

In the AGI era, agents need a deterministic substrate beneath probabilistic language models. OmniGlyph turns Unicode characters, scripts, multilingual terms, technical symbols, industry abbreviations, and eventually domain concepts into structured facts that agents can query, verify, and compute against.

## Why It Exists

Large language models are probabilistic engines. They are powerful, but they can hallucinate when facing obscure scripts, multilingual abbreviations, domain-specific symbols, malformed OCR, or specialized industrial terminology.

OmniGlyph provides the missing layer:

```text
Agent encounters symbol → calls local OmniGlyph → receives traceable structured fact → continues task
```

This converts dictionaries from pages that humans read into computation fuel that agents execute against.

## Strategic Positioning

OmniGlyph is designed as the local knowledge heart of private agent systems such as OpenClaw / AgentCore OS:

- **Deterministic:** Canonical facts come from traceable sources, not model guesses.
- **Structured:** Responses are JSON, vectors, traits, relations, and provenance, not noisy HTML pages.
- **Local-first:** Runs on private infrastructure such as an N100 matrix for speed, cost control, and confidentiality.
- **Composable (MCP-Ready):** Exposes standard Model Context Protocol servers for immediate use in OpenClaw, RAG pipelines, cross-border inquiry parsing, product standardization, and semantic computation.
- **Expandable:** Starts from Unicode and grows into industry concepts and computable traits.

## Long-Term Vision

OmniGlyph aims to become the Symbol Kernel for agentic systems:

```text
Glyph Layer → Lexical Layer → Concept Layer → Computation Layer
```

### 1. Glyph Layer

Answers: **What is this symbol?**

- Unicode code point
- character name
- script
- block
- category
- decomposition
- variants
- source version

### 2. Lexical Layer

Answers: **What does this symbol or term mean in human language?**

- pronunciation
- definitions
- part of speech
- multilingual aliases
- etymology
- dictionary references
- abbreviations
- simplified/traditional or variant forms

### 3. Concept Layer

Answers: **What real-world concept does this point to?**

Example:

```text
铝 → aluminum → chemical element → metal material → construction profile material
```

### 4. Computation Layer

Answers: **What can an agent infer or trigger from this concept in a task?**

Example:

```text
玻璃 + 海运 + 风暴
→ fragile_material + ocean_freight + weather_hazard
→ high_breakage_risk
→ packaging and insurance recommendation
```


## Tech Stack & Architecture

Designed for edge computing and heterogeneous hardware matrices:

- **Core Framework:** Python 3.10+ and FastAPI for high-concurrency local APIs.
- **Database:** SQLite for MVP and edge nodes, then PostgreSQL + pgvector for Stage 3 semantic topology.
- **Deployment:** Docker-native, optimized for low-power edge nodes such as Intel N100 and Apple Silicon nodes such as Mac mini M4 for vector processing.
- **Agent Integration:** Native MCP (Model Context Protocol) support for zero-config integration with OpenClaw, Claude Desktop, and custom agents.

## Quick Look: What OmniGlyph Returns

When an agent encounters a symbol like `铝` and queries OmniGlyph:

**Request:**

```text
GET /api/v1/glyph?char=铝
```

**Response:**

```json
{
  "glyph": "铝",
  "unicode": {
    "hex": "U+94DD",
    "name": "CJK UNIFIED IDEOGRAPH-94DD",
    "block": "CJK Unified Ideographs",
    "source": "UnicodeData 17.0.0"
  },
  "lexical": {
    "pinyin": "lǚ",
    "basic_meaning": null,
    "sources": {
      "pinyin": "Unihan Database"
    }
  },
  "domain_traits": {
    "trade_code": "HS 7604.21"
  },
  "metadata": {
    "confidence": 1.0,
    "retrieved_at": "2026-04-24T10:00:00Z"
  }
}
```

The key distinction is that global Unicode facts, Unihan lexical facts, and optional private domain traits are returned together but remain source-separated internally. Missing upstream facts remain `null`; for example, current Unihan readings provide `kMandarin` for `铝`, while `basic_meaning` may remain null unless another approved source supplies it. `domain_traits` appears only when an authorized private domain pack contributes matching properties.

## Development Stages

### Stage 1: Symbol Fact Base

Build the local, read-only, source-backed glyph and lexical base.

- Ingest Unicode Character Database, Unihan, CLDR, and approved open lexical sources.
- Normalize source facts into canonical records.
- Preserve NULL for unknown facts.
- Expose stable local APIs for exact symbol lookup.
- Absolutely prohibit AI-generated canonical definitions.

### Stage 2: Agent Lexical Intelligence

Extend from single symbols to words, abbreviations, multilingual aliases, OCR fragments, and domain terminology.

- Add property tables and source snapshots.
- Seamlessly mount private industry lexicons such as architectural profiles, glass specifications, HS codes, logistics terms, and trade abbreviations without polluting the global Unicode ground truth.
- Support batch normalization for agent workflows.
- Introduce reviewed LLM-assisted candidate extraction, but not direct canonical writes.

### Stage 3: Semantic Topology

Connect symbols, terms, and concepts into a graph.

- Separate glyph nodes from concept nodes.
- Add confidence-scored relationships.
- Link multilingual equivalents and technical notations.
- Enable explainable traversal from symbol to concept.

### Stage 4: Semantic Computation Engine

Use concept traits, vectors, graph relations, and rules to power task decisions.

- Convert industry concepts into computable traits.
- Combine rule engines with vector recall.
- Keep outputs explainable by source path and reasoning path.
- Use LLMs for explanation and orchestration, not as the canonical fact source.

## MVP Target

The first practical version should prove one closed loop:

```text
Cross-border inquiry / OCR / product text
→ symbol and term extraction
→ local OmniGlyph normalization
→ structured facts and traits
→ AgentCore decision or reply
```

MVP v0.1:

- Unicode + Unihan local ingestion.
- `GET /api/v1/glyph?char=铝`.
- SQLite or PostgreSQL storage.
- Source provenance for every property.
- No generative definitions.

MVP v0.2:

- CLDR display names and emoji/script annotations.
- Batch symbol normalization endpoint.
- First private building-material terminology pack.

MVP v0.3:

- Wiktionary or approved open dictionary ingestion.
- Domain term API for materials, logistics, trade terms, and specifications.
- AgentCore/OpenClaw integration adapter.

## Iron Laws

1. **No hallucination pollution:** Canonical facts must be source-backed.
2. **Data is code:** Every attribute may affect future agent decisions.
3. **Embrace NULL:** Missing facts are safer than guessed facts.
4. **Source before meaning:** Every value needs source name, version, field, and retrieval metadata.
5. **Local-first by default:** Private agent systems must be able to run without external dictionary APIs.
6. **LLM is assistant, not authority:** Models can propose candidates, but reviewed sources write canonical data.
7. **Explainability is mandatory:** Semantic computation must expose the path from input symbols to output decisions.

## Examples

Run the cross-border inquiry normalization demo:

```bash
PYTHONPATH=src python examples/scripts/run_cross_border_demo.py
```

Example output maps `aluminum profile`, `tempered glass`, `FOB`, and `MOQ` to canonical IDs while preserving unknown tokens such as `Bangkok` and `500 sets`.

## Documentation

- Project goals and vision: `docs/product/omni-glyph-doctrine.md`
- Development handbook: `docs/product/development-handbook.md`
- Stage 1 architecture: `docs/architecture/stage-1-architecture.md`
- Quickstart: `docs/quickstart.md`
- API reference: `docs/api.md`
- MCP tools: `docs/mcp-tools.md`
- Codex MCP integration: `docs/integrations/codex-mcp.md`
- Claude Desktop MCP integration: `docs/integrations/claude-desktop-mcp.md`



## Domain Pack and Normalization

OmniGlyph can mount private domain packs without polluting global Unicode/Unihan facts.

Import a CSV domain pack:

```bash
omniglyph ingest-domain-pack --source tests/fixtures/domain_pack.csv --namespace private_building_materials --source-version fixture
```

Look up a term:

```bash
curl 'http://127.0.0.1:8000/api/v1/term?text=FOB'
```

Normalize mixed glyphs and terms:

```bash
curl -X POST 'http://127.0.0.1:8000/api/v1/normalize?mode=compact' \
  -H 'Content-Type: application/json' \
  -d '{"tokens":["铝","FOB","tempered glass","unknown"]}'
```

Compact response example:

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

## MCP Server

OmniGlyph includes a minimal stdio MCP server exposing the `lookup_glyph` tool.

Run it locally after installing the package:

```bash
omniglyph-mcp
```

Example JSON-RPC request over stdio:

```json
{"jsonrpc":"2.0","id":1,"method":"tools/list"}
```

The MCP server reads from the same local SQLite symbol fact base used by `/api/v1/glyph`. It exposes `lookup_glyph`, `lookup_term`, and `normalize_tokens`.

## Local MVP Commands

Install development dependencies:

```bash
python -m pip install -e '.[dev]'
```

Use `uv` if the system Python environment is broken or missing Python 3.10+:

```bash
UV_CACHE_DIR=.uv-cache uv venv .venv --python 3.11
UV_CACHE_DIR=.uv-cache uv pip install -e '.[dev]'
.venv/bin/python -m pytest -v
```

Ingest the Unicode source fixture explicitly:

```bash
python -m omniglyph.cli ingest-unicode --source tests/fixtures/UnicodeData.sample.txt --source-version fixture
```

Ingest the Unihan source fixture explicitly:

```bash
python -m omniglyph.cli ingest-unihan --source tests/fixtures/Unihan.sample.txt --source-version fixture
```

Run the API:

```bash
uvicorn omniglyph.api:app --reload
```

Query one glyph:

```bash
curl 'http://127.0.0.1:8000/api/v1/glyph?char=铝'
```

Run the lookup benchmark after ingestion:

```bash
python scripts/benchmark_lookup.py --db data/omniglyph.sqlite3 --glyph 铝 --iterations 1000
```


## Release Check Scripts

Run the full local release check from an activated environment:

```bash
scripts/release_check.sh
```

Run the demo check after installing console scripts:

```bash
scripts/demo_check.sh
```


## License

OmniGlyph source code is licensed under the Apache License 2.0. Imported datasets, Unicode/Unihan/CLDR artifacts, and private domain packs are governed by their own licenses and are not relicensed by this project.

万象文枢（OmniGlyph）源代码采用 Apache License 2.0。导入的数据集、Unicode/Unihan/CLDR 原始数据以及私有领域词库遵循各自的授权条款，本项目不会对其重新授权。
