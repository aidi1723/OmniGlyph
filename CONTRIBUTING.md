# Contributing to OmniGlyph

Thank you for helping improve OmniGlyph.

## Local Setup

```bash
UV_CACHE_DIR=.uv-cache uv venv .venv --python 3.11
UV_CACHE_DIR=.uv-cache uv pip install -e '.[dev]'
.venv/bin/python -m pytest -v
```

## Development Rules

- Canonical facts must be source-backed.
- Missing data must remain `null` or unknown; do not guess.
- LLMs may help write code, tests, docs, and candidate extraction tools, but must not write canonical definitions, pronunciations, source metadata, confidence scores, concept relations, or computable traits.
- Raw source artifacts must remain immutable.
- Do not commit `data/`, `.venv/`, `.uv-cache/`, `.pytest_cache/`, `__pycache__/`, or private customer files.

## Adding a Parser

1. Add a small synthetic fixture under `tests/fixtures/`.
2. Write parser tests first.
3. Preserve source provenance in repository writes.
4. Skip malformed rows without aborting full ingestion.
5. Add docs if the source introduces new license or attribution requirements.

## Adding a Domain Pack

- Use CSV or JSONL with explicit namespace.
- Keep private packs under `examples/` only if they are synthetic or safe to publish.
- Do not mix private terms into global Unicode/Unihan facts.
- Add tests for aliases, traits, and unknown tokens.

## Pull Request Checklist

- [ ] Tests pass with `.venv/bin/python -m pytest -v`.
- [ ] No generated local files are included.
- [ ] New canonical facts have source provenance.
- [ ] Documentation is updated for new commands or APIs.
- [ ] Release notes are updated if user-facing behavior changes.
