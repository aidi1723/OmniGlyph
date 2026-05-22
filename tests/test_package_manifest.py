import tarfile
from pathlib import Path

import pytest


def test_manifest_includes_test_fixtures_examples_and_scripts():
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / "MANIFEST.in"

    assert manifest_path.exists()
    manifest = manifest_path.read_text(encoding="utf-8")
    assert "recursive-include tests/fixtures" in manifest
    assert "recursive-include examples" in manifest
    assert "recursive-include scripts" in manifest


def test_built_sdist_includes_test_fixtures_examples_and_scripts_when_present():
    root = Path(__file__).resolve().parents[1]
    sdist_path = root / "dist" / "omniglyph-0.7.0b0.tar.gz"
    if not sdist_path.exists():
        return
    if sdist_path.stat().st_mtime < (root / "MANIFEST.in").stat().st_mtime:
        pytest.skip("sdist was built before MANIFEST.in changed")

    with tarfile.open(sdist_path) as archive:
        names = set(archive.getnames())

    assert "omniglyph-0.7.0b0/tests/fixtures/Unihan.sample.txt" in names
    assert "omniglyph-0.7.0b0/examples/scripts/run_cross_border_demo.py" in names
    assert "omniglyph-0.7.0b0/scripts/mcp_smoke_test.sh" in names
