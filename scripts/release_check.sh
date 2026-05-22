#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python3}"

"${PYTHON_BIN}" -m pytest -v
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
