# OmniGlyph v0.7.0 Beta Draft Release Notes

Status: draft for the current source branch.

This release is not published to PyPI yet. The latest published PyPI version remains `0.6.0b0`.

## Product Positioning

v0.7 clarifies OmniGlyph around three layers:

1. **Global Symbol Ground Truth Layer**
   - Local, source-backed facts for Unicode symbols, terms, suspicious glyph patterns, and private vocabulary.
   - Reduces character-, symbol-, and terminology-layer failures before model reasoning.

2. **Strict Enterprise Guardrails**
   - Source-grounded output checks through `validate_output_terms` and `enforce_grounded_output`.
   - Private Lexicon Packs for company terms, SKUs, aliases, confidential vocabulary, and approved business facts.

3. **Language-as-Code Security Gateway**
   - Input prompt-injection scanning.
   - Output DLP redaction.
   - Intent manifest enforcement for `allow`, `review`, or `block` decisions.

## New MCP Tools in Source Branch

The current v0.7 source branch exposes 14 MCP tools:

- `lookup_glyph`
- `lookup_term`
- `explain_glyph`
- `explain_term`
- `explain_code_security`
- `normalize_tokens`
- `validate_output_terms`
- `enforce_grounded_output`
- `scan_code_symbols`
- `scan_unicode_security`
- `scan_language_input`
- `scan_output_dlp`
- `enforce_intent`
- `audit_explain`

## Guardrail Updates

- Added `enforce_grounded_output` for strict source-grounding decisions.
- Guardrail decisions return `allow` or `block` with known terms, unknown terms, source IDs, limits, and optional audit evidence.
- Lexicon entries with `review_status` other than `approved` do not count as trusted guardrail facts.

## Language Security Gateway

- Added `scan_language_input` for prompt-injection directive checks and high-risk Unicode input patterns.
- Added `scan_output_dlp` for API keys, AWS access keys, email addresses, caller-provided secret terms, and approved lexicon secrets.
- Added `enforce_intent` for manifest-based action decisions.
- Intent checks never execute commands. They return policy evidence only.

## Lexicon Pack Standard

Added Lexicon Pack Standard v0.1:

```text
my-pack/
  pack.json
  terms.csv
```

New CLI commands:

```bash
omniglyph init-lexicon-pack my-pack --namespace private_acme --pack-id company.acme.trade_terms --name "ACME Trade Terms"
omniglyph validate-domain-pack my-pack
omniglyph ingest-domain-pack --source my-pack --dry-run
omniglyph ingest-domain-pack --source my-pack --replace-namespace
```

New lexical metadata:

- `sensitivity`
- `review_status`
- `pack_id`
- `pack_version`

## Boundaries

v0.7 does not claim:

- complete hallucination elimination
- complete prompt-injection immunity
- automatic shell command execution
- replacement for OS sandboxing, IAM, approval workflows, or endpoint security

The intended claim is narrower and stronger:

```text
OmniGlyph gives AI agents deterministic checkpoints for symbols, terms, outputs, secrets, and requested intents.
```

## Verification

Current branch verification:

- Python tests: `106 passed`
- MCP smoke test: 14 tools available
- Example Lexicon Pack validation: `status: pass`
- `git diff --check`: pass
