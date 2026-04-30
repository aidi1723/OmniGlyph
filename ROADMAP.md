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

Partially implemented. This is the practical focus because it gives developers and coding agents a concrete, testable use case: finding symbol-level bugs and spoofing risks that humans and LLMs often miss.

Goals:

- Unicode confusables data ingestion. Initial minimal pack shipped in `0.6.0b0`.
- Stronger homoglyph detection and mapping. Initial source-backed `unicode-confusable` findings shipped in `0.6.0b0`.
- Fullwidth/halfwidth detection. Implemented.
- NFC/NFKC normalization diff reports. Implemented for single-character findings.
- Trojan Source / Bidi rule pack. Initial Bidi control detection implemented.
- Domain spoofing and username validation helpers.
- Math/science/programming symbol starter pack for `∂`, `∇`, `λ`, `σ`, `∑`, and similar dense technical symbols.
- Optional `--suggest-fix` reports without automatic mutation.
- LogosGate experimental runtime:
  - JSON policy model.
  - Deterministic action validation.
  - `omniglyph logos validate`.
  - `validate_action_policy` MCP tool.
  - Example policies for code safety, marketing integrity, and trade compliance.

## v0.5.x — Text Audit Workflows

Partially implemented. This track expands the code-symbol linter into OES-shaped explanations and structured audit evidence.

Goals:

- OmniGlyph Explanation Standard v0.1 for source-backed glyph, term, concept, and safety explanations. Implemented as docs plus `omniglyph.oes` helpers.
- OES-shaped `explain_glyph`, `explain_term`, and `explain_code_security` responses.
- Unicode confusables data ingestion and source-backed confusable findings. Initial minimal pack implemented.
- Audit events that show actor, action, input, status, source IDs, findings, and unknown limits.
- CLDR fixture ingestion for emoji, script, language, and locale labels.
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
- software development domain pack example
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
