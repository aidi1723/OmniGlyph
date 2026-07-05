# Changelog

## 0.8.0-beta - Unreleased

### Improvements

- Add Policy Pack standard (`policy.json` + `intents.csv`) for local deterministic agent intent rules.
- Add `omniglyph.policy_pack` with init, validation, loading, manifest conversion, and `OMNIGLYPH_POLICY_PACK_ROOT` path restriction support.
- Add CLI commands: `init-policy-pack`, `validate-policy-pack`, and `enforce-intent`.
- Add `POST /api/v1/policy/validate-pack` and support `policy_pack_path` in `/api/v1/language-security/enforce-intent`.
- Add MCP `validate_policy_pack` and support `policy_pack_path` in `enforce_intent`.
- Preserve inline intent manifest compatibility while adding explicit `decision=block` precedence and policy metadata passthrough.
- Add `examples/policy-packs/agent_intents` and `docs/specs/policy-pack-standard.md`.
- Add dependency-free `parameters_schema` runtime validation for intent parameters, returning `decision=block` and `status=invalid_parameters` on mismatch.
- Add output guardrail policy modes so unknown, unapproved, and secret terms can be allowed, reviewed, or blocked while strict blocking remains the default.
- Add guardrail review packets that group unknown, unapproved, and secret output terms into deterministic host-review evidence.

## 0.7.0-beta - Unreleased

### Improvements

- Harden v0.7 release gates: `scripts/release_check.sh` now prefers the project virtualenv, runs tests, Ruff, mypy, whitespace checks, MCP smoke, package build, Twine metadata checks, artifact audit, wheel smoke, and the cross-border demo in one command.
- Add `scripts/wheel_smoke_test.sh` to install the built wheel into a fresh temporary virtualenv and verify installed CLI/MCP entry points.
- Add `scripts/artifact_audit.py` to inspect built wheel/sdist contents, dependency metadata, entry points, required examples/scripts, and forbidden local artifacts, with quiet release logs and defaults derived from `pyproject.toml`.
- Add release tooling dependencies (`build`, `setuptools`, `twine`, and `tomli` on Python <3.11) to the `dev` extra so local release checks have the required packaging backend and validators.
- Expose the legacy `scan_code_symbols` MCP tool in `tools/list` as a deprecated alias, matching the documented backward-compatibility promise and MCP smoke expectations.
- Apply the same Lexicon Pack root restriction to MCP `validate_lexicon_pack` that the API already applies when `OMNIGLYPH_LEXICON_PACK_ROOT` is set.
- Redact DLP finding matches by default; findings now return `[REDACTED]`, match length, and SHA-256 instead of echoing full secret values.
- Make recursive `scan-code` resilient to non-UTF-8 or unreadable files by reporting `failed_files` instead of aborting the whole scan.
- Optimize `GlyphRepository` connection management with cached connections to reduce overhead under concurrent API usage.
- Merge duplicate `scan_code_symbols` and `scan_unicode_security` MCP tools into a single handler (`scan_code_symbols` retained as backward-compatible alias).
- Extract shared `explain_for_audit` helper to `omniglyph.explanation` module, eliminating duplication between API and MCP surfaces.
- Enhance prompt-injection detection to report all matching patterns instead of only the first match.
- Fix CLI `lookup` command to output formatted JSON instead of Python repr; return exit code 1 when not found.
- Add `get_app()` factory function for cleaner ASGI startup; Dockerfile updated to use `--factory` mode.
- Add `ruff` and `mypy` to dev dependencies with project-level configuration in `pyproject.toml`.
- Remove stale `src/omniglyph/logos/` directory (contained only orphaned `__pycache__` artifacts).

### Previous (carried forward)

- Align MCP tool call results with text content blocks containing JSON payloads for broader MCP client compatibility.
- Add environment-based runtime configuration for data directories, SQLite path, Unicode source URL, and optional Lexicon Pack root restrictions.
- Add API health metadata for the active SQLite database path and existence state.
- Add optional Lexicon Pack path sandboxing for `/api/v1/lexicon/validate-pack`.
- Fix output DLP finding offsets so redaction reports continue to reference the original text.
- Skip virtual environments, build outputs, VCS metadata, and cache directories during recursive code scans.
- Make demo and release check scripts safer and more portable by avoiding destructive `data` deletion and supporting configurable Python interpreters.
- Add source download timeout handling and release packaging coverage for fixtures, examples, and scripts.
- Refresh Claude Desktop MCP integration docs for the v0.7 tool set and data-directory configuration.

## 0.6.0-beta - 2026-04-25

- Add `omniglyph.oes` runtime helpers so OES is a project protocol, not only a document.
- Add Unicode Security Pack metadata for source-backed `unicode-confusable` findings with `confusable_with`, `why_it_matters`, `suggested_action`, and `auto_fixable`.
- Add OES-shaped `explain_code_security` runtime helper, API endpoint, and MCP tool.
- Add `POST /api/v1/security/scan` and MCP `scan_unicode_security` for developer-friendly scan reports.
- Add `examples/domain-packs/software_development.csv` with software and security terminology.
- Add `omniglyph.audit` event builder plus `/api/v1/audit/explain`, `/api/v1/audit/security-scan`, and MCP `audit_explain`.

## 0.5.0-beta - 2026-04-25

- Add OmniGlyph Explanation Standard v0.1 documentation for source-backed glyph, term, concept, and safety explanations.
- Add OES-shaped `explain_glyph` and `explain_term` runtime helpers.
- Add `GET /api/v1/explain/glyph` and `GET /api/v1/explain/term` API endpoints.
- Add MCP `explain_glyph` and `explain_term` tools.

## 0.4.0-beta - 2026-04-25

- Centralize runtime version metadata across package, API health metadata, and MCP initialize metadata.
- Add reproducible source integrity checks with optional expected SHA-256 validation for local and downloaded source artifacts.
- Add CLI `--expected-sha256` options for Unicode, Unihan, and private domain pack ingestion.
- Add SQLite lookup indexes for glyph properties, lexical terms, and lexical aliases.
- Extend code-symbol linting with fullwidth/halfwidth and NFKC normalization-change warnings.
- Refresh release-facing PyPI, MCP Registry, and API documentation for the `0.4.0b0` release candidate.

## 0.2.0-beta - Unreleased

- Add Stage 1 Symbol Fact Base skeleton.
- Add deterministic UnicodeData parsing and explicit ingestion.
- Add Unihan tab-separated property parsing and explicit ingestion.
- Add SQLite `source_snapshot`, `glyph_node`, and append-only `glyph_property` schema.
- Add read-only `/api/v1/glyph` FastAPI endpoint.
- Add agent-friendly `unicode`, `lexical`, `domain_traits`, raw `properties`, and `sources` response fields.
- Add minimal stdio MCP server with `lookup_glyph`, `lookup_term`, and `normalize_tokens` tools.
- Add private domain pack CSV ingestion.
- Add `GET /api/v1/term` and `POST /api/v1/normalize` APIs with compact mode.
- Add Dockerfile, docker-compose, GitHub Actions test workflow, migration SQL, benchmark script, notices, and data-source documentation.
- Add Sandwich Architecture documentation for input normalization and output guardrail workflows.
- Add minimal output guardrail API and MCP tool for deterministic known/unknown term validation.
- Add OmniGlyph Code Linter core scanner, CLI `scan-code`, MCP `scan_code_symbols`, and poisoned-code demo generator.
- Add Claude Desktop/Claude Code MCP readiness docs, MCP server card, and MCP safety notes.
- Add MCP Registry submission plan and draft `package-registry/server.json`.
- Prepare PyPI packaging metadata and publish checklist for MCP Registry submission.
- Publish and verify `omniglyph==0.3.2b0` on TestPyPI and PyPI.
- Publish `io.github.aidi1723/omniglyph` version `0.3.2-beta` to the MCP Registry.
