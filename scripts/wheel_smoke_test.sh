#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python3}"
WHEEL_PATH="${1:-}"

if [[ -z "${WHEEL_PATH}" ]]; then
  shopt -s nullglob
  version="$("${PYTHON_BIN}" -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')"
  WHEEL_PATH="dist/omniglyph-${version}-py3-none-any.whl"
  if [[ ! -f "${WHEEL_PATH}" ]]; then
    echo "Expected OmniGlyph wheel not found: ${WHEEL_PATH}" >&2
    exit 1
  fi
fi

SMOKE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/omniglyph-wheel-smoke.XXXXXX")"
trap 'rm -rf "${SMOKE_DIR}"' EXIT
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WHEEL_PATH="$(cd "$(dirname "${WHEEL_PATH}")" && pwd)/$(basename "${WHEEL_PATH}")"

# A clean environment is required. An inherited PYTHONPATH or editable checkout
# of the same version would make pip skip this wheel and omit its entry points.
"${PYTHON_BIN}" -m venv "${SMOKE_DIR}"
(
  cd "${SMOKE_DIR}"
  unset PYTHONPATH
  PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 "${SMOKE_DIR}/bin/python" -m pip install --no-deps --force-reinstall "${WHEEL_PATH}" >/dev/null
  PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 "${SMOKE_DIR}/bin/python" -m pip install 'fastapi>=0.110' 'httpx>=0.27' 'uvicorn[standard]>=0.27' >/dev/null
  OMNIGLYPH_DATA_DIR="${SMOKE_DIR}/data" OMNIGLYPH_SQLITE_PATH="${SMOKE_DIR}/data/omniglyph.sqlite3" \
    "${SMOKE_DIR}/bin/python" "${SCRIPT_DIR}/installed_smoke.py" "${SMOKE_DIR}/bin/omniglyph" "${SMOKE_DIR}/bin/omniglyph-mcp"
)

echo "wheel smoke ok: ${WHEEL_PATH}"
