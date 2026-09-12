#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${PYTHON:-}" ]]; then
  PYTHON_BIN="${PYTHON}"
elif [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
else
  PYTHON_BIN="python3"
fi

MCP_COMMAND="${PYTHON_BIN} -m omniglyph.mcp_server"

PROJECT_VERSION="$("${PYTHON_BIN}" -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')"
BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/omniglyph-release.XXXXXX")"
trap 'rm -rf "${BUILD_DIR}"' EXIT

"${PYTHON_BIN}" -m pytest -v
"${PYTHON_BIN}" -m ruff check .
"${PYTHON_BIN}" -m mypy src
git diff --check
PYTHON="${PYTHON_BIN}" scripts/mcp_smoke_test.sh "${MCP_COMMAND}"
"${PYTHON_BIN}" -m build --no-isolation --outdir "${BUILD_DIR}"
WHEEL_PATH="${BUILD_DIR}/omniglyph-${PROJECT_VERSION}-py3-none-any.whl"
SDIST_PATH="${BUILD_DIR}/omniglyph-${PROJECT_VERSION}.tar.gz"
test -f "${WHEEL_PATH}" && test -f "${SDIST_PATH}"
"${PYTHON_BIN}" -m twine check "${WHEEL_PATH}" "${SDIST_PATH}"
"${PYTHON_BIN}" scripts/artifact_audit.py --quiet --wheel "${WHEEL_PATH}" --sdist "${SDIST_PATH}"
PYTHON="${PYTHON_BIN}" bash scripts/wheel_smoke_test.sh "${WHEEL_PATH}"
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
