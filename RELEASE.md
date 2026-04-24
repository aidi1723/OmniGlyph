# Release Checklist

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
.venv/bin/python -m pytest -v
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
