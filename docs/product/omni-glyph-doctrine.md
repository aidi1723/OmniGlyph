# OmniGlyph Goals and Vision

## Project Definition

OmniGlyph（万象文枢）is the Symbol Ground Truth Layer for AI Agents.

It is not a traditional dictionary. Traditional dictionaries are designed for human eyes: entries, paragraphs, typography, examples, and browsing interfaces. OmniGlyph is designed for agent brains: deterministic lookup, structured properties, local execution, provenance, vectors, traits, and explainable semantic paths.

## Core Philosophy

> 字符即封装，语义即运算。

A character is not only a visual mark. It is a package of encoding, history, pronunciation, meaning, cultural context, domain usage, and computational traits. Once these layers are normalized and made traceable, agents can operate on symbols as structured facts instead of guessing from context.

## Ultimate Goal

Build a local-first global symbol infrastructure that allows AI agents to identify, normalize, relate, and compute over human civilization symbols with source-backed certainty.

The final system should let private agents handle multilingual inquiries, OCR noise, technical abbreviations, scripts, materials, logistics terms, ancient or specialized symbols, and domain concepts through a stable local interface.

## Why This Matters in the AGI Era

### 1. Deterministic Ground Truth for Probabilistic Models

Large language models predict likely text. They do not guarantee truth. When an agent encounters a rare glyph, mixed-language product term, obscure abbreviation, or malformed OCR output, direct model guessing is unsafe.

OmniGlyph provides a deterministic path:

```text
Unknown symbol → local lookup → source-backed properties → agent action
```

This turns symbol interpretation from probabilistic generation into verifiable data access.

### 2. Machine-Computable Data Instead of Human-Readable Pages

Existing dictionaries and encyclopedic resources are valuable, but many are optimized for browsers and humans: HTML, wiki markup, prose, ads, templates, and layout complexity.

OmniGlyph converts approved sources into agent-native structures:

- normalized JSON
- property records
- source snapshots
- confidence scores
- concept edges
- embeddings
- computable traits

The agent no longer needs to read a page. It can directly use structured fuel.

### 3. Private Infrastructure Moat

For OpenClaw, AgentCore OS, or other private agent systems, a local symbol fact base creates a durable moat:

- no external API latency
- no repeated token spend for basic symbol interpretation
- no leakage of sensitive query patterns
- high-frequency local normalization
- domain-specific extensions unavailable in general models
- cumulative private knowledge growth

OmniGlyph becomes the local knowledge heart of the agent system.

## Vision Architecture

### Glyph Layer

The objective symbol shell.

Answers:

```text
What is this exact symbol?
```

Includes Unicode code point, script, block, category, decomposition, variants, standard name, and source version.

### Lexical Layer

The human-language meaning layer.

Answers:

```text
How is this symbol or term pronounced, explained, and used?
```

Includes pronunciation, definitions, translations, aliases, abbreviations, language tags, part-of-speech data, etymology, and dictionary provenance.

### Concept Layer

The real-world concept layer.

Answers:

```text
What thing, idea, material, action, risk, or domain object does this point to?
```

Example:

```text
铝 / aluminum / aluminium / อลูมิเนียม
→ concept: aluminum_material
→ type: metal_material
→ domain: construction_profile
```

### Computation Layer

The task decision layer.

Answers:

```text
What can an agent calculate, warn, classify, or trigger from this concept?
```

Example:

```text
风暴 → weather_hazard
海运 → ocean_freight
玻璃 → fragile_material
weather_hazard + ocean_freight + fragile_material → high_breakage_risk
```

## Stage Roadmap

### Stage 1: Symbol Fact Base

**Goal:** Build the deterministic base.

**Scope:** Unicode, Unihan, CLDR, source snapshots, local lookup API, and strict provenance.

**Acceptance:** Given a supported Unicode character, OmniGlyph returns its standard properties with source metadata in milliseconds.

**Forbidden:** AI-generated definitions, guessed pronunciations, untraceable facts, and silent source mixing.

### Stage 2: Agent Lexical Intelligence

**Goal:** Move from isolated symbols to agent-ready lexical normalization.

**Scope:** Words, abbreviations, multilingual aliases, OCR fragments, batch APIs, reviewed candidate ingestion, and private mounted domain lexicons such as architectural profiles, glass specifications, HS codes, logistics terms, and trade abbreviations.

**Acceptance:** Given a mixed-language inquiry or product title, OmniGlyph can normalize symbols and known terms into structured records with sources and confidence, while keeping private business lexicons isolated from the global Unicode ground truth.

### Stage 3: Semantic Topology

**Goal:** Connect symbols and lexical forms to real-world concepts.

**Scope:** Concept nodes, alias edges, relation edges, multilingual equivalence, etymology paths, and graph traversal.

**Acceptance:** `水`, `water`, and `H₂O` can resolve to a shared concept node while preserving distinctions between glyph, word, formula, and concept.

### Stage 4: Semantic Computation

**Goal:** Let agents compute over structured semantic traits.

**Scope:** Computable traits, rules, vectors, graph traversal, risk models, and explainable decision paths.

**Acceptance:** Domain scenarios such as `风暴 + 海运 + 玻璃` produce a risk result with a transparent symbol-to-concept-to-rule path.

## Success Criteria

OmniGlyph succeeds if it becomes the first local service an agent calls before guessing symbol meaning.

The practical success criteria are:

- Agents can query it in milliseconds.
- Every canonical field is source-backed.
- Missing data is explicit as NULL.
- Batch normalization improves real workflows.
- Private domain lexicons compound over time.
- Semantic computation outputs are explainable.

## Product Boundaries

OmniGlyph is not:

- a general chatbot
- a public encyclopedia clone
- an AI-generated dictionary
- a pure vector database
- a web scraping project
- a replacement for human lexicography

OmniGlyph is:

- a source-backed symbol fact layer
- an agent-native lexical and concept normalization engine
- a local-first semantic infrastructure component
- a foundation for private agent systems and domain-specific computation
