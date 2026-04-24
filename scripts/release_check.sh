#!/usr/bin/env bash
set -euo pipefail

python -m pytest -v
PYTHONPATH=src python examples/scripts/run_cross_border_demo.py >/tmp/omniglyph-demo-output.json
python - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path('/tmp/omniglyph-demo-output.json').read_text())
known = payload['normalization']['known']
assert known['aluminum profile'] == 'material:aluminum_profile'
assert known['FOB'] == 'trade:fob'
assert 'Bangkok' in payload['normalization']['unknown']
print('demo output ok')
PY
