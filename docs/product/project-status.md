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
- Standard Lexicon Pack directories with `pack.json`, `terms.csv`, validation, dry-run import, and namespace replacement.
- `GET /api/v1/glyph`, `GET /api/v1/term`, `POST /api/v1/normalize`, OES explanation, Unicode security scan, and audit APIs.
- MCP stdio server with seventeen tools in the current source branch:
  - `lookup_glyph`
  - `lookup_term`
  - `explain_glyph`
  - `explain_term`
  - `explain_code_security`
  - `normalize_tokens`
  - `list_namespaces`
  - `validate_lexicon_pack`
  - `validate_output_terms`
  - `enforce_grounded_output`
  - `scan_code_symbols`
  - `scan_unicode_security`
  - `scan_language_input`
  - `scan_output_dlp`
  - `enforce_intent`
  - `validate_action_policy`
  - `audit_explain`
- Code-symbol linting for zero-width characters, Bidi controls, unexpected controls, source-backed confusables, fullwidth/halfwidth forms, NFKC changes, and cross-script homoglyph risks.
- Software-development domain pack example under `examples/domain-packs/software_development.csv`.
- Strict source-grounding enforcement for checked output terms through deterministic `allow` / `block` decision evidence.
- Language Security Gateway checks for prompt-injection input, outbound DLP redaction, and manifest-based intent sandbox decisions.
- Approved `sensitivity=secret` lexicon entries can feed output DLP redaction when requested by the host.
- Structured audit events that report actor, action, input, source IDs, findings, and unknown limits.
- PyPI distribution and MCP Registry publication.

## Experimental LogosGate Status

LogosGate is incubating inside OmniGlyph as an experimental action-policy firewall. It is not a universal ethics engine. The MVP validates agent action-plan text against explicit JSON policies and returns deterministic `allow`, `warn`, `review`, or `block` decisions with structured evidence.

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
- Current output guardrail supports known/unknown validation and strict source-grounding decisions for checked terms, but not full policy orchestration.
- Current Language Security Gateway is a deterministic checkpoint layer, not a complete prompt-injection, DLP, IAM, or OS sandboxing product.
- Homoglyph detection is rule-based with a minimal confusables map; full Unicode confusables data ingestion is planned.
- OmniGlyph Explanation Standard v0.1 has runtime wrappers for glyph, term, and code-security explanations; broader CLDR and concept graph integrations are still planned.
- No automatic source-code mutation or rewrite is performed.
- Stage 3/4 semantic graph and computation layers are roadmap items, not current production features.

## Design Principle

Missing facts should remain missing. OmniGlyph intentionally avoids generating definitions or guessing unsupported facts because the project exists to reduce hallucination at the symbol and terminology layer.

## External Evaluation Adjustments

Recent external-style evaluation framed OmniGlyph as a possible Unicode/glyph semantic project. The useful parts are being adopted with stricter wording:

- **Adopted:** Homoglyph detection, invisible-character scanning, and Unicode security workflows are first-class practical use cases.
- **Adopted:** Agent symbol grounding remains the central positioning, but as deterministic lookup and validation rather than broad semantic understanding.
- **Adopted:** Math, science, and programming symbols are strong candidates for curated packs because they are dense, ambiguous, and common in agent workflows.
- **Deferred:** Symbol knowledge graphs belong to Stage 3 and should not be described as current capability.
- **Rejected as current claim:** Raw visual glyph recognition, OCR, automatic symbol-to-concept mapping, and generative dictionary definitions are outside the current beta scope.

The current project should be described as useful beta infrastructure, not as a finished universal symbol-intelligence engine.
