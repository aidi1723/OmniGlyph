#!/usr/bin/env bash
set -euo pipefail

rm -rf data
omniglyph ingest-unicode --source tests/fixtures/UnicodeData.sample.txt --source-version fixture
omniglyph ingest-domain-pack --source examples/domain-packs/building_materials.csv --namespace private_building_materials --source-version example
python examples/scripts/run_cross_border_demo.py
