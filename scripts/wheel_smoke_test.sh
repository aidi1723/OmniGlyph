#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python3}"
WHEEL_PATH="${1:-}"

if [[ -z "${WHEEL_PATH}" ]]; then
  shopt -s nullglob
  wheels=(dist/omniglyph-*.whl)
  shopt -u nullglob
  if [[ ${#wheels[@]} -eq 0 ]]; then
    echo "No built OmniGlyph wheel found under dist/" >&2
    exit 1
  fi
  WHEEL_PATH="${wheels[${#wheels[@]}-1]}"
fi

SMOKE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/omniglyph-wheel-smoke.XXXXXX")"
trap 'rm -rf "${SMOKE_DIR}"' EXIT

"${PYTHON_BIN}" -m venv "${SMOKE_DIR}"
PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 "${SMOKE_DIR}/bin/python" -m pip install --no-deps "${WHEEL_PATH}" >/dev/null
"${SMOKE_DIR}/bin/omniglyph" --version >/dev/null
PYTHON="${SMOKE_DIR}/bin/python" scripts/mcp_smoke_test.sh "${SMOKE_DIR}/bin/omniglyph-mcp" >/dev/null

echo "wheel smoke ok: ${WHEEL_PATH}"
