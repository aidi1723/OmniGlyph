# OmniGlyph Roadmap

OmniGlyph is an early-stage local Symbol Ground Truth Layer for AI agents. This roadmap separates current beta capabilities from longer-term semantic-computation goals.

## v0.3.x — Open-Source Maturity and MCP Readiness

Status: in progress / beta.

Goals:

- PyPI package distribution.
- MCP Registry publication.
- Claude Desktop / Claude Code / Codex integration docs.
- Code-symbol linter for invisible Unicode, Bidi controls, and homoglyph risks.
- CI hardening for tests, package build, metadata checks, and MCP smoke tests.
- Community contribution templates and issue triage.

## v0.4.x — Unicode Security Rules

Planned. This is the next practical focus because it gives developers and coding agents a concrete, testable use case: finding symbol-level bugs and spoofing risks that humans and LLMs often miss.

Goals:

- Unicode confusables data ingestion.
- Stronger homoglyph detection and mapping.
- Fullwidth/halfwidth detection.
- NFC/NFKC normalization diff reports.
- Trojan Source / Bidi rule pack.
- Domain spoofing and username validation helpers.
- Math/science/programming symbol starter pack for `∂`, `∇`, `λ`, `σ`, `∑`, and similar dense technical symbols.
- Optional `--suggest-fix` reports without automatic mutation.

## v0.5.x — Text Audit Workflows

Planned. This track expands the code-symbol linter into general text/security audit pipelines.

Goals:

- `omniglyph audit-text` CLI.
- JSONL / CSV / TSV field scanning.
- OCR text audit examples.
- Community Notes / social-text Unicode audit demo.
- Phishing-text and suspicious-link Unicode audit examples.
- Summary reports by rule, field, and record.

## Stage 2 — Agent Lexical Intelligence

Partially implemented.

Current:

- private domain pack CSV ingestion
- `lookup_term`
- `normalize_tokens`
- `validate_output_terms`

Planned:

- policy-based output validation
- severity scoring
- allowlist/blocklist packs
- domain-specific review workflows

## Stage 3 — Semantic Topology

Long-term research track.

Goals:

- multilingual concept graph
- etymology and source relation graph
- PostgreSQL + pgvector runtime
- graph query and visualization tools

## Stage 4 — Native Semantic Computation

Long-term research track.

Goals:

- computable traits
- semantic collision/risk rules
- explainable semantic computation traces
- domain-specific recommendation engines
