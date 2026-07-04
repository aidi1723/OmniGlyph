import os
from pathlib import Path


def test_release_check_uses_project_python_and_release_gates():
    script = Path("scripts/release_check.sh").read_text(encoding="utf-8")

    assert '.venv/bin/python' in script
    assert '-m ruff check .' in script
    assert '-m mypy src' in script
    assert 'scripts/mcp_smoke_test.sh' in script
    assert '-m build --no-isolation' in script
    assert '-m twine check dist/*' in script
    assert 'scripts/artifact_audit.py --quiet' in script
    assert 'scripts/wheel_smoke_test.sh' in script
    assert 'git diff --check' in script


def test_wheel_smoke_test_installs_built_wheel_and_checks_mcp():
    script = Path("scripts/wheel_smoke_test.sh").read_text(encoding="utf-8")

    assert '-m venv' in script
    assert 'pip install --no-deps' in script
    assert 'bin/omniglyph" --version' in script
    assert 'scripts/mcp_smoke_test.sh' in script


def test_release_shell_scripts_are_executable():
    assert os.access("scripts/release_check.sh", os.X_OK)
    assert os.access("scripts/mcp_smoke_test.sh", os.X_OK)
    assert os.access("scripts/wheel_smoke_test.sh", os.X_OK)
