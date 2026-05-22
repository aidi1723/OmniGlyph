#!/usr/bin/env bash
set -euo pipefail

DEMO_DATA_DIR="${OMNIGLYPH_DEMO_DATA_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/omniglyph-demo-data.XXXXXX")}"
export OMNIGLYPH_DATA_DIR="${DEMO_DATA_DIR}"
echo "Using demo data directory: ${OMNIGLYPH_DATA_DIR}"

omniglyph ingest-unicode --source tests/fixtures/UnicodeData.sample.txt --source-version fixture
omniglyph ingest-domain-pack --source examples/domain-packs/building_materials.csv --namespace private_building_materials --source-version example
python examples/scripts/run_cross_border_demo.py
