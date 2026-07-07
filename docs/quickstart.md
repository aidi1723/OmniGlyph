# OmniGlyph Quickstart

Run OmniGlyph locally in five minutes with fixture data and the building-material demo pack.

## 1. Install

```bash
UV_CACHE_DIR=.uv-cache uv venv .venv --python 3.11
UV_CACHE_DIR=.uv-cache uv pip install -e '.[dev]'
```

## 2. Run Tests

```bash
.venv/bin/python -m pytest -v
```

## 3. Import Fixture Data

```bash
.venv/bin/omniglyph ingest-unicode --source tests/fixtures/UnicodeData.sample.txt --source-version fixture
.venv/bin/omniglyph ingest-unihan --source tests/fixtures/Unihan.sample.txt --source-version fixture
.venv/bin/omniglyph ingest-domain-pack --source examples/domain-packs/building_materials.csv --namespace private_building_materials --source-version example
```

## 4. Run API

```bash
.venv/bin/uvicorn omniglyph.api:app --reload
```

## 5. Query a Glyph

```bash
curl 'http://127.0.0.1:8000/api/v1/glyph?char=%E9%93%9D'
```

## 6. Query a Term

```bash
curl 'http://127.0.0.1:8000/api/v1/term?text=FOB'
```

## 7. Normalize Tokens

```bash
curl -X POST 'http://127.0.0.1:8000/api/v1/normalize?mode=compact' \
  -H 'Content-Type: application/json' \
  -d '{"tokens":["铝","FOB","tempered glass","unknown"]}'
```

Expected compact idea:

```json
{
  "known": {
    "铝": "glyph:U+94DD",
    "FOB": "trade:fob",
    "tempered glass": "material:tempered_glass"
  },
  "unknown": ["unknown"]
}
```

## 8. Run MCP Server

```bash
.venv/bin/omniglyph-mcp
```

## 9. Run CLI Guardrail and Security Checks

```bash
.venv/bin/omniglyph validate-output --term FOB --term "tempered glass" --term "HS 7604.99X"
.venv/bin/omniglyph enforce-output --term FOB --term "HS 7604.99X" --actor-id agent:quote
.venv/bin/omniglyph scan-language-input --text "ignore previous instructions"
.venv/bin/omniglyph scan-output-dlp --text "token sk-proj-abcdefghijklmnopqrstuvwxyz123456"
.venv/bin/omniglyph enforce-intent ticket.create --policy-pack examples/policy-packs/agent_intents --actor-role operator
```

These commands return JSON evidence. They do not rewrite text automatically or execute shell commands.

## 10. Run Demo

```bash
PYTHONPATH=src .venv/bin/python examples/scripts/run_cross_border_demo.py
```

## 11. Scan Source Text

```bash
.venv/bin/omniglyph scan-code src --format json --fail-on warning
```

The scanner reports suspicious Unicode findings and unreadable or non-UTF-8 files without aborting the entire directory scan.
