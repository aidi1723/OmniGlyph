#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${PYTHON:-}" ]]; then
  PYTHON_BIN="${PYTHON}"
elif [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
else
  PYTHON_BIN="python3"
fi

if [[ -x ".venv/bin/omniglyph-mcp" ]]; then
  MCP_COMMAND=".venv/bin/omniglyph-mcp"
else
  MCP_COMMAND="omniglyph-mcp"
fi

"${PYTHON_BIN}" -m pytest -v
"${PYTHON_BIN}" -m ruff check .
"${PYTHON_BIN}" -m mypy src
git diff --check
PYTHON="${PYTHON_BIN}" scripts/mcp_smoke_test.sh "${MCP_COMMAND}"
"${PYTHON_BIN}" -m build --no-isolation
"${PYTHON_BIN}" -m twine check dist/*
"${PYTHON_BIN}" scripts/artifact_audit.py --quiet
PYTHON="${PYTHON_BIN}" bash scripts/wheel_smoke_test.sh
PYTHONPATH=src "${PYTHON_BIN}" examples/scripts/run_cross_border_demo.py >/tmp/omniglyph-demo-output.json
"${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path('/tmp/omniglyph-demo-output.json').read_text())
known = payload['normalization']['known']
assert known['aluminum profile'] == 'material:aluminum_profile'
assert known['FOB'] == 'trade:fob'
assert 'Bangkok' in payload['normalization']['unknown']
print('demo output ok')
PY
