# PyPI Publish Checklist

This checklist prepares OmniGlyph for PyPI publication so it can be referenced by MCP registry metadata.

## Package Identity

- PyPI name: `omniglyph`
- Current package version: `0.5.0b0`
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
/tmp/omniglyph-wheel-test/bin/pip install dist/omniglyph-0.5.0b0-py3-none-any.whl
printf '{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n' | /tmp/omniglyph-wheel-test/bin/omniglyph-mcp
```

Expected tools:

- `lookup_glyph`
- `lookup_term`
- `explain_glyph`
- `explain_term`
- `normalize_tokens`
- `validate_output_terms`
- `scan_code_symbols`

## Publish to TestPyPI First

```bash
.venv/bin/python -m twine upload --repository testpypi dist/*
```

Install from TestPyPI in a clean environment and rerun the MCP smoke test.

## Publish to PyPI

Only after TestPyPI succeeds:

```bash
.venv/bin/python -m twine upload dist/*
```

## MCP Registry Follow-Up

After PyPI publication:

1. Confirm the PyPI project page renders the README and includes `mcp-name: io.github.aidi1723/omniglyph`.
2. Confirm `package-registry/server.json` references the exact published version.
3. Submit the MCP registry PR using `docs/ecosystem/mcp-registry-submission.md`.

## Release Candidate Status

Local verification passed; public upload is pending TestPyPI/PyPI credentials:

- TestPyPI: `https://test.pypi.org/project/omniglyph/0.5.0b0/`
- PyPI: `https://pypi.org/project/omniglyph/0.5.0b0/`
- Local package build and metadata checks pass.
- Local wheel install smoke test passes.
- TestPyPI upload attempt reached TestPyPI but failed because no API token was configured.
- Clean PyPI install verification should be completed after upload.
- Installed `omniglyph-mcp` should return all seven MCP tools via `tools/list`.
