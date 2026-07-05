# Release Checklist

## v0.8 Source Batch Development Scope

This source batch adds local Policy Pack intent guardrails, deterministic intent parameter validation, configurable output guardrail policy modes, review packet evidence, and a CLI surface for output guardrail checks.

Included in the working tree:

- Policy Pack Standard v0.1 with `policy.json`, `intents.csv`, validation, example packs, and manifest conversion.
- CLI commands for Policy Pack initialization, validation, and intent enforcement.
- API and MCP Policy Pack validation surfaces plus `policy_pack_path` support for `enforce_intent`.
- `OMNIGLYPH_POLICY_PACK_ROOT` path restriction for API/MCP Policy Pack usage.
- Dependency-free `parameters_schema` validation for intent parameters.
- Output guardrail policy modes for unknown, unapproved, and secret terms with `allow`, `review`, and `block` actions.
- `review_packet` evidence for risky output terms grouped by class and action.
- Review packet hardening for direct unapproved and policy-allowed unknown branches.
- `omniglyph enforce-output` for local JSON output guardrail evidence.
- v0.8 closeout and draft release notes under `docs/product/v0.8-closeout.md` and `docs/release-notes-v0.8-source-batch-draft.md`.

Release gate for this source batch:

- `scripts/release_check.sh` passes locally or in CI.
- Python tests include Policy Pack, parameter schema, language security, guardrail, CLI guardrail, API, MCP, and config coverage.
- MCP `tools/list` smoke test includes the Policy Pack and output guardrail tool surfaces.
- Package build, Twine metadata check, artifact audit, wheel smoke test, and demo output check pass.
- Package version remains `0.7.0b0` until a real v0.8 package release decision is made.
- No automatic rewriting, command execution, persistent approval queue, or external workflow integration is implied by the new evidence surfaces.

## v0.7.0-beta Development Scope

This release prepares OmniGlyph as a broader local-first Agent checkpoint layer: symbol facts, lexical guardrails, language security, Lexicon Pack operations, and release hardening.

Included in the working tree:

- MCP tools for lookup, explanation, normalization, namespace listing, Lexicon Pack validation, output guardrails, Unicode security scanning, language input scanning, DLP output scanning, intent enforcement, and audit explanations.
- Backward-compatible `scan_code_symbols` alias exposed in `tools/list`.
- Lexicon Pack Standard v0.1 with `pack.json`, `terms.csv`, validation, dry-run import, namespace replacement, and metadata fields for sensitivity/review status.
- Language Security Gateway helpers for prompt-injection checks, DLP redaction, lexicon-backed secret redaction, and deterministic intent sandbox decisions.
- DLP findings that avoid echoing raw secret values.
- Shared API/MCP Lexicon Pack root restriction through `OMNIGLYPH_LEXICON_PACK_ROOT`.
- Recursive code scanner error reporting for non-UTF-8 or unreadable files.
- Hardened `scripts/release_check.sh` covering tests, Ruff, mypy, whitespace checks, MCP smoke, package build, Twine metadata checks, artifact audit, wheel smoke, and demo verification.
- Clean wheel smoke verification that installs the built wheel into a fresh temporary virtualenv and checks CLI/MCP entry points.
- Artifact audit that checks wheel/sdist contents, dependency metadata, console entry points, and forbidden local artifacts before release, with quiet output in the main release gate and default artifact names derived from `pyproject.toml`.
- Python 3.10-compatible release tooling through a `tomllib`/`tomli` TOML parser fallback.

Release gate for v0.7.0-beta:

- `scripts/release_check.sh` passes locally or in CI.
- MCP `tools/list` smoke test returns all 16 MCP tools.
- `git diff --check` passes without trailing whitespace or conflict marker issues.
- Package build succeeds and `twine check dist/*` passes.
- Built wheel installs into a fresh temporary virtualenv and passes CLI/MCP smoke checks.
- Artifact audit passes for the freshly built wheel and sdist.
- DLP reports do not include full matched secret values in findings.
- `scan-code --fail-on warning` exits non-zero for suspicious Unicode findings or scan errors.

## v0.6.0-beta Development Scope

This release turns OES into a reusable project protocol and adds the first enterprise-facing audit slice.

Included in the working tree:

- Shared OES helpers under `src/omniglyph/oes.py`.
- Unicode Security Pack metadata for source-backed `unicode-confusable` findings.
- `explain_code_security` helper, API endpoint, and MCP tool.
- `POST /api/v1/security/scan` and MCP `scan_unicode_security`.
- Software-development domain pack under `examples/domain-packs/software_development.csv`.
- Structured audit events through `src/omniglyph/audit.py`, `/api/v1/audit/explain`, `/api/v1/audit/security-scan`, and MCP `audit_explain`.

Release gate for v0.6.0-beta:

- Full test suite passes.
- MCP `tools/list` smoke test returns all ten MCP tools.
- Package build succeeds.
- `twine check dist/*` passes.
- Security findings remain review-only and do not mutate source code automatically.

## v0.5.0-beta Development Scope

This release starts the OmniGlyph Explanation Standard runtime layer.

Included in the working tree:

- OES v0.1 specification under `docs/specs/omniglyph-explanation-standard.md`.
- `explain_glyph` and `explain_term` helpers returning `schema: "oes:0.1"` payloads.
- HTTP endpoints for glyph and term explanations.
- MCP tools for glyph and term explanations.
- Existing lookup, normalization, guardrail, and code-symbol scanning behavior preserved.

Release gate for v0.5.0-beta:

- Full test suite passes.
- MCP `tools/list` smoke test returns all seven MCP tools.
- OES tests cover matched glyph, matched term, and explicit unknown values.

## v0.4.0-beta Development Scope

This release hardens OmniGlyph for version-consistent, reproducible, faster, and deeper Unicode-security beta usage.

Included in the working tree:

- Runtime metadata aligned on `0.4.0b0` across package version, API health, and MCP initialize responses.
- Optional expected SHA-256 validation for local source registration and source downloads.
- CLI `--expected-sha256` options for UnicodeData, Unihan, and private domain pack ingestion.
- SQLite indexes for glyph-property and lexical lookup hot paths.
- Code-symbol linter warnings for fullwidth/halfwidth forms and NFKC normalization changes.
- Release-facing README, API, PyPI, and MCP Registry metadata updates.

Release gate for v0.4.0-beta:

- Full test suite passes.
- MCP `tools/list` smoke test returns all five MCP tools.
- Package build succeeds.
- `twine check dist/*` passes.
- Public upload credentials are available for TestPyPI/PyPI.

## v0.3.1-beta Development Scope

This upcoming release focuses on MCP ecosystem readiness for Claude Desktop, Claude Code, and MCP server directories.

Included in the working tree:

- Hardened Claude Desktop MCP integration guide.
- New Claude Code MCP integration guide.
- New MCP server card suitable for MCP directory/registry submissions.
- New MCP safety notes documenting read-only tool boundaries.
- README links updated for MCP tools and safety documentation.

Release gate for v0.3.1-beta:

- Full test suite passes.
- `tools/list` stdio smoke test returns all five MCP tools.
- Documentation references `lookup_glyph`, `lookup_term`, `normalize_tokens`, `validate_output_terms`, and `scan_code_symbols`.

## v0.3.0-beta Development Scope

This upcoming release adds the first developer-facing dogfooding use case: OmniGlyph Code Linter.

Included in the working tree:

- Core code-symbol scanner for invisible Unicode format characters, Bidi controls, unexpected controls, and cross-script homoglyph risks.
- CLI command: `omniglyph scan-code PATH --format text|json --fail-on never|warning`.
- MCP tool: `scan_code_symbols` for coding agents.
- Poisoned-code demo generator under `examples/poisoned-code/`.
- Use-case documentation under `docs/use-cases/code-linter.md`.

Release gate for v0.3.0-beta:

- Full test suite passes.
- Demo generator plus `scan-code` smoke test finds `U+0430`, `U+200B`, and `U+202E`.
- Generated poisoned sample is not committed to the repository.

## v0.2.0-beta Scope

This release is an beta-quality local symbol fact base for AI agents.

Included:

- UnicodeData parser and explicit ingestion command.
- Unihan tab-separated parser and explicit ingestion command.
- SQLite `source_snapshot`, `glyph_node`, and append-only `glyph_property` schema.
- FastAPI `GET /api/v1/glyph`, `GET /api/v1/term`, `POST /api/v1/normalize`, and `POST /api/v1/guardrail/validate-output` endpoints.
- Agent-friendly response fields: `unicode`, `lexical`, `domain_traits`, raw `properties`, and `sources`.
- Minimal stdio MCP server exposing `lookup_glyph`, `lookup_term`, `normalize_tokens`, and `validate_output_terms`.
- Dockerfile, docker-compose file, GitHub Actions test workflow, benchmark script, and migration SQL.

Excluded:

- CLDR ingestion.
- Full production MCP compliance testing across clients.
- Access control for private domain packs.
- PostgreSQL/pgvector runtime.
- OCR/image symbol recognition.
- Semantic graph and semantic computation engine.
- Policy-based output blocking, automatic rewriting, and human approval workflows.

## Pre-Release Commands

Create an isolated Python environment:

```bash
UV_CACHE_DIR=.uv-cache uv venv .venv --python 3.11
UV_CACHE_DIR=.uv-cache uv pip install -e '.[dev]'
```

Run tests:

```bash
scripts/release_check.sh
```

Run fixture ingestion:

```bash
rm -rf data
PYTHONPATH=src .venv/bin/python -m omniglyph.cli ingest-unicode --source tests/fixtures/UnicodeData.sample.txt --source-version fixture
PYTHONPATH=src .venv/bin/python -m omniglyph.cli ingest-unihan --source tests/fixtures/Unihan.sample.txt --source-version fixture
```

Run benchmark:

```bash
PYTHONPATH=src .venv/bin/python scripts/benchmark_lookup.py --db data/omniglyph.sqlite3 --glyph 铝 --iterations 1000
```

Run MCP smoke test:

```bash
printf '{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n' | PYTHONPATH=src .venv/bin/python -m omniglyph.mcp_server
```

Docker verification, on a machine with Docker installed:

```bash
docker build -t omniglyph:0.2.0-beta .
docker run --rm -p 8000:8000 -v "$PWD/data:/app/data" omniglyph:0.2.0-beta
```

## Release Gate

A v0.2.0-beta release is allowed only when:

- `LICENSE` is no longer a placeholder.
- `docs/legal/data-sources.md` exists.
- `CHANGELOG.md` includes the release entry.
- `.venv/bin/python -m pytest -v` passes.
- Fixture ingestion and benchmark pass.
- Docker commands are either verified or explicitly marked unverified due to missing Docker runtime.
- Output guardrail endpoint and MCP tool are covered by tests.


## Docker Runtime Status for This Workspace

Docker is not installed in the local macOS execution environment (`docker not found`), but Docker verification passed on the N100 server (`yami-n100`, Docker 28.2.2). The image `omniglyph:0.2.0-beta` built successfully, the container started, an empty database returned 404 instead of 500, and fixture ingestion inside the mounted `/app/data` volume served `铝` via `/api/v1/glyph`.


## Real Data Verification Notes

Verified in this workspace against live Unicode UCD latest paths:

- `download-unicode` downloaded `UnicodeData.txt` with SHA-256 `2e1efc1dcb59c575eedf5ccae60f95229f706ee6d031835247d843c11d96470c`.
- `ingest-unicode --source data/raw/UnicodeData.txt --source-version latest` ingested 40,569 glyph records after skipping surrogate code points.
- `Unihan_Readings.txt` from `Unihan.zip` ingested 291,227 Unihan properties.
- `Unihan_DictionaryLikeData.txt` from `Unihan.zip` ingested 156,251 Unihan properties.
- Querying `铝` returned `U+94DD` and `lexical.pinyin = lǚ`; `basic_meaning` remained null because the verified Unihan files did not provide `kDefinition` for that code point.
- Benchmark on the resulting SQLite database: 1,000 lookups for `铝`, P95 approximately `0.143ms`.


## N100 Server Verification

Verified on `yami-n100` (`Linux 6.8.0-106-generic`, Python 3.12.3, Docker 28.2.2):

- Synced source tree to `~/omniglyph-beta`.
- Created `.venv` and installed `.[dev]`.
- Ran full test suite: `21 passed in 2.06s`.
- Built Docker image: `omniglyph:0.2.0-beta`.
- Ran container on port `8000` with mounted `data/` volume.
- Empty DB lookup returned `404 Not Found`, not `500`.
- Imported mounted fixture inside container and verified `GET /api/v1/glyph?char=%E9%93%9D` returns `U+94DD`.


## v0.2.0-beta Feature Progress

The four core Agent-ready normalization features have been implemented in the working tree:

- Private Domain Pack CSV ingestion.
- `GET /api/v1/term` term lookup.
- `POST /api/v1/normalize` batch normalization with compact mode.
- MCP `lookup_term` and `normalize_tokens` tools.

A fifth Sandwich Architecture guardrail feature has also been added: `POST /api/v1/guardrail/validate-output` and MCP `validate_output_terms`.

These features should be re-verified on N100/Docker before cutting the next release tag.


## Release Check Scripts

Run the full local release check from an activated environment:

```bash
scripts/release_check.sh
```

Run the demo check after installing console scripts:

```bash
scripts/demo_check.sh
```


## v0.2.0-beta N100 Verification

Verified on `yami-n100` after release hardening:

- Synced v0.2.0-beta candidate to `~/omniglyph-beta`.
- Python 3.12 virtualenv install succeeded.
- Full test suite passed: `34 passed in 2.91s`.
- Cross-border demo produced expected canonical IDs for `aluminum profile`, `tempered glass`, `FOB`, and `MOQ`.
- Docker image built successfully: `omniglyph:0.2.0-beta`.
- Docker container started on host port `8001`.
- `GET /api/v1/health` returned `{"status":"ok","service":"omniglyph","version":"0.2.0b0"}`.
- Docker healthcheck reached `healthy`.
- Container fixture ingestion succeeded: 5 Unicode glyph records and 9 domain entries.
- `POST /api/v1/normalize?mode=compact` returned canonical IDs for `铝`, `FOB`, and `tempered glass`, with `unknown` preserved.
