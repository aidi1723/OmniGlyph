# Project Status and Maturity

OmniGlyph is currently an early beta infrastructure project.

It is suitable for experimentation, local agent workflows, RAG preprocessing, code-symbol linting, OCR/text cleanup prototypes, and deterministic symbol lookup. It is not yet a full production semantic-computation engine.

## Current Maturity

- Stage 1 Symbol Fact Base: usable beta.
- Stage 2 Agent Lexical Intelligence: partially implemented.
- Stage 3 Semantic Topology: planned.
- Stage 4 Native Semantic Computation: planned.

## What Works Today

- UnicodeData ingestion and glyph lookup.
- Unihan property ingestion for CJK-friendly lexical facts.
- Private domain pack CSV ingestion.
- `GET /api/v1/glyph`, `GET /api/v1/term`, and `POST /api/v1/normalize` APIs.
- MCP stdio server with five tools:
  - `lookup_glyph`
  - `lookup_term`
  - `normalize_tokens`
  - `validate_output_terms`
  - `scan_code_symbols`
- Code-symbol linting for zero-width characters, Bidi controls, unexpected controls, and cross-script homoglyph risks.
- PyPI distribution and MCP Registry publication.

## Best-Fit Users

OmniGlyph is useful for:

- local-first or privacy-sensitive Agent developers
- RAG pipeline builders who need deterministic preprocessing
- CJK / multilingual workflow builders
- code-review Agent developers concerned about Unicode spoofing
- OCR/text cleanup pipelines that need traceable symbol facts

## Not a Good Fit Yet

OmniGlyph is not yet ideal for:

- users expecting a general-purpose LLM or multimodal model
- teams needing a fully managed production SaaS
- workflows requiring automatic text rewriting policies
- semantic graph reasoning across all world concepts
- image/OCR symbol recognition without a separate OCR layer

## Known Limitations

- Community adoption is still early.
- Current output guardrail is known/unknown validation, not full policy orchestration.
- Homoglyph detection is rule-based; Unicode confusables data is planned.
- No automatic source-code mutation or rewrite is performed.
- Stage 3/4 semantic graph and computation layers are roadmap items, not current production features.

## Design Principle

Missing facts should remain missing. OmniGlyph intentionally avoids generating definitions or guessing unsupported facts because the project exists to reduce hallucination at the symbol and terminology layer.
