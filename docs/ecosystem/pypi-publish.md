# PyPI Publish Checklist

This checklist records the OmniGlyph PyPI publication flow so it can be repeated safely and referenced by MCP registry metadata.

## Package Identity

- PyPI name: `omniglyph`
- Current package version: `0.7.0b0`
- MCP server name: `io.github.aidi1723/omniglyph`
- Console scripts:
  - `omniglyph`
  - `omniglyph-mcp`

## Preflight

Run from the repository root:

```bash
UV_CACHE_DIR=.uv-cache uv venv .venv --python 3.11
UV_CACHE_DIR=.uv-cache uv pip install -e '.[dev]'
```

Run the full local release gate:

```bash
scripts/release_check.sh
```

The release gate performs:

- Python tests
- Ruff
- mypy
- `git diff --check`
- MCP `tools/list` smoke test
- package build with `python -m build --no-isolation`
- `twine check dist/*`
- artifact content audit
- clean wheel install smoke test
- cross-border demo output check

## Manual Build Commands

Use these only when debugging a failed release gate:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src
git diff --check
PYTHON=.venv/bin/python scripts/mcp_smoke_test.sh .venv/bin/omniglyph-mcp
.venv/bin/python -m build --no-isolation
.venv/bin/python -m twine check dist/*
.venv/bin/python scripts/artifact_audit.py --quiet
PYTHON=.venv/bin/python bash scripts/wheel_smoke_test.sh
```

## Local Wheel Smoke Test

The release gate runs the scripted smoke test automatically:

```bash
PYTHON=.venv/bin/python bash scripts/wheel_smoke_test.sh
```

Expected tools:

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

## Publish to TestPyPI First

Use exact filenames so old artifacts in `dist/` are not uploaded accidentally:

```bash
.venv/bin/python -m twine upload --repository testpypi dist/omniglyph-0.7.0b0.tar.gz dist/omniglyph-0.7.0b0-py3-none-any.whl
```

Install from TestPyPI in a clean environment and rerun the MCP smoke test.

## Publish to PyPI

Only after TestPyPI succeeds:

Use exact filenames so old artifacts in `dist/` are not uploaded accidentally:

```bash
TWINE_NON_INTERACTIVE=1 TWINE_USERNAME=__token__ TWINE_PASSWORD="$PYPI_TOKEN" .venv/bin/python -m twine upload dist/omniglyph-0.7.0b0.tar.gz dist/omniglyph-0.7.0b0-py3-none-any.whl
```

## MCP Registry Follow-Up

After PyPI publication:

1. Confirm the PyPI project page renders the README and includes `mcp-name: io.github.aidi1723/omniglyph`.
2. Confirm `package-registry/server.json` references the exact published version.
3. Submit the MCP registry PR using `docs/ecosystem/mcp-registry-submission.md`.

## v0.7.0b0 Release Status

Prepared in source, not uploaded yet.

- Package metadata version is `0.7.0b0`.
- Full `scripts/release_check.sh` gate passes locally.
- Current branch verification includes `136 passed`, MCP smoke with 16 tools, package build, Twine metadata check, artifact audit, clean wheel smoke, and cross-border demo check.
- Use exact filenames when uploading `0.7.0b0` artifacts.

## Previous v0.6.0b0 Release Status

Published on PyPI on 2026-04-25:

- TestPyPI: `https://test.pypi.org/project/omniglyph/0.6.0b0/`
- PyPI: `https://pypi.org/project/omniglyph/0.6.0b0/`
- Local package build and metadata checks pass.
- Local wheel install smoke test passes.
- Formal PyPI upload completed for `omniglyph-0.6.0b0.tar.gz` and `omniglyph-0.6.0b0-py3-none-any.whl`.
- A stale `omniglyph-0.5.0b0.tar.gz` artifact was also uploaded because `dist/*` was used during manual publication. Future uploads should use exact filenames.
- Clean PyPI install verification passed with `omniglyph==0.6.0b0`.
- Installed `omniglyph-mcp` returns the v0.6 MCP tools via `tools/list`.
- Packaged `software_development` domain pack loads from the published wheel.
