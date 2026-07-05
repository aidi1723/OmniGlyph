# OmniGlyph v0.7.0 Beta Draft Release Notes

Status: draft for the current source branch.

Current source version: `0.7.0b0`.

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

## MCP Tools in Source Branch

The current v0.7 source branch exposes 16 MCP tools:

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
- `audit_explain`

The legacy `scan_code_symbols` tool remains a backward-compatible alias for `scan_unicode_security`.

## Guardrail Updates

- Added `enforce_grounded_output` for strict source-grounding decisions.
- Guardrail decisions return `allow` or `block` with known terms, unknown terms, source IDs, limits, and optional audit evidence.
- Lexicon entries with `review_status` other than `approved` do not count as trusted guardrail facts.

## Lexicon Product Tools

- Added `list_namespaces` to show mounted lexical namespaces, entry counts, alias counts, pack IDs, and source names.
- Added `validate_lexicon_pack` to validate a `pack.json` + `terms.csv` directory through MCP.
- Added API endpoints:
  - `GET /api/v1/lexicon/namespaces`
  - `POST /api/v1/lexicon/validate-pack`

## Language Security Gateway

- Added `scan_language_input` for prompt-injection directive checks and high-risk Unicode input patterns.
- Added `scan_output_dlp` for API keys, AWS access keys, email addresses, caller-provided secret terms, and approved lexicon secrets.
- DLP findings redact matched sensitive values by default and return `[REDACTED]`, match length, and SHA-256 evidence instead of echoing secrets.
- Added `enforce_intent` for manifest-based action decisions.
- Intent checks never execute commands. They return policy evidence only.

## Code Scanner Hardening

- Recursive `scan-code` reports non-UTF-8 or unreadable files in `failed_files` instead of aborting the entire scan.
- `scan-code --fail-on warning` now returns a non-zero exit code for both suspicious Unicode findings and scan errors.

## Release Gate Hardening

- `scripts/release_check.sh` now runs Python tests, Ruff, mypy, whitespace checks, MCP smoke, package build, Twine metadata checks, artifact audit, wheel smoke, and the cross-border demo.
- Added `scripts/wheel_smoke_test.sh` to install the built wheel into a fresh temporary virtualenv and verify installed CLI/MCP entry points.
- Added `scripts/artifact_audit.py` to inspect wheel/sdist contents, dependency metadata, console entry points, and forbidden local artifacts, with quiet output for release logs and default artifact names derived from `pyproject.toml`.
- The release script prefers `.venv/bin/python` when available and falls back to `python3`.
- Release tooling dependencies are included in the `dev` extra: `build`, `setuptools`, `twine`, and `tomli` on Python <3.11.

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

- Python tests: `136 passed`
- Whitespace/conflict-marker check: pass
- MCP smoke test: 16 tools available
- Example Lexicon Pack validation: `status: pass`
- Build: `omniglyph-0.7.0b0.tar.gz` and `omniglyph-0.7.0b0-py3-none-any.whl`
- Twine metadata check: pass
- Artifact content audit: pass
- Clean wheel install with CLI/MCP smoke: pass
- Cross-border demo check: pass
