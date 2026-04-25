# PyPI Publish Checklist

This checklist records the OmniGlyph PyPI publication flow so it can be repeated safely and referenced by MCP registry metadata.

## Package Identity

- PyPI name: `omniglyph`
- Current package version: `0.6.0b0`
- MCP server name: `io.github.aidi1723/omniglyph`
- Console scripts:
  - `omniglyph`
  - `omniglyph-mcp`

## Preflight

Run from the repository root:

```bash
rm -rf dist build src/omniglyph.egg-info
UV_CACHE_DIR=.uv-cache uv venv .venv --python 3.11
UV_CACHE_DIR=.uv-cache uv pip install -e '.[dev]'
.venv/bin/python -m pytest -q
```

Verify MCP stdio:

```bash
printf '{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n' | .venv/bin/omniglyph-mcp
```

## Build

Install build tooling:

```bash
UV_CACHE_DIR=.uv-cache uv pip install build twine
```

Build source distribution and wheel:

```bash
.venv/bin/python -m build
```

Check package metadata:

```bash
.venv/bin/python -m twine check dist/*
```

## Local Wheel Smoke Test

Use a clean temporary virtual environment:

```bash
python3 -m venv /tmp/omniglyph-wheel-test
/tmp/omniglyph-wheel-test/bin/pip install dist/omniglyph-0.6.0b0-py3-none-any.whl
printf '{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n' | /tmp/omniglyph-wheel-test/bin/omniglyph-mcp
```

Expected tools:

- `lookup_glyph`
- `lookup_term`
- `explain_glyph`
- `explain_term`
- `explain_code_security`
- `normalize_tokens`
- `validate_output_terms`
- `scan_code_symbols`
- `scan_unicode_security`
- `audit_explain`

## Publish to TestPyPI First

```bash
.venv/bin/python -m twine upload --repository testpypi dist/*
```

Install from TestPyPI in a clean environment and rerun the MCP smoke test.

## Publish to PyPI

Only after TestPyPI succeeds:

Use exact filenames so old artifacts in `dist/` are not uploaded accidentally:

```bash
TWINE_NON_INTERACTIVE=1 TWINE_USERNAME=__token__ TWINE_PASSWORD="$PYPI_TOKEN" .venv/bin/python -m twine upload dist/omniglyph-0.6.0b0.tar.gz dist/omniglyph-0.6.0b0-py3-none-any.whl
```

## MCP Registry Follow-Up

After PyPI publication:

1. Confirm the PyPI project page renders the README and includes `mcp-name: io.github.aidi1723/omniglyph`.
2. Confirm `package-registry/server.json` references the exact published version.
3. Submit the MCP registry PR using `docs/ecosystem/mcp-registry-submission.md`.

## Release Status

Published on PyPI on 2026-04-25:

- TestPyPI: `https://test.pypi.org/project/omniglyph/0.6.0b0/`
- PyPI: `https://pypi.org/project/omniglyph/0.6.0b0/`
- Local package build and metadata checks pass.
- Local wheel install smoke test passes.
- Formal PyPI upload completed for `omniglyph-0.6.0b0.tar.gz` and `omniglyph-0.6.0b0-py3-none-any.whl`.
- A stale `omniglyph-0.5.0b0.tar.gz` artifact was also uploaded because `dist/*` was used during manual publication. Future uploads should use exact filenames.
- Clean PyPI install verification passed with `omniglyph==0.6.0b0`.
- Installed `omniglyph-mcp` returns all ten MCP tools via `tools/list`.
- Packaged `software_development` domain pack loads from the published wheel.
