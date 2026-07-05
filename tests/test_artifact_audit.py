import importlib.util
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
    import tomli as tomllib


def load_artifact_audit_module():
    script_path = Path("scripts/artifact_audit.py")
    spec = importlib.util.spec_from_file_location("artifact_audit", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_artifact_audit_passes_for_current_dist_when_present():
    artifact_audit = load_artifact_audit_module()
    wheel_path, sdist_path = artifact_audit.default_artifact_paths()
    if not wheel_path.exists() or not sdist_path.exists():
        return

    report = artifact_audit.audit_artifacts(wheel_path=wheel_path, sdist_path=sdist_path)

    assert report["status"] == "pass"
    assert report["wheel"]["entry_points"]["omniglyph"] == "omniglyph.cli:main"
    assert report["wheel"]["entry_points"]["omniglyph-mcp"] == "omniglyph.mcp_server:main"
    assert "fastapi>=0.110" in report["wheel"]["requires_dist"]
    assert "uvicorn[standard]>=0.27" in report["wheel"]["requires_dist"]


def test_release_check_runs_artifact_audit():
    script = Path("scripts/release_check.sh").read_text(encoding="utf-8")

    assert "scripts/artifact_audit.py" in script


def test_artifact_audit_quiet_mode_reports_concise_failure(tmp_path):
    missing_wheel = tmp_path / "missing.whl"
    missing_sdist = tmp_path / "missing.tar.gz"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/artifact_audit.py",
            "--quiet",
            "--wheel",
            str(missing_wheel),
            "--sdist",
            str(missing_sdist),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert "artifact audit failed: 2 error(s)" in result.stderr
    assert "{" not in result.stderr


def test_default_artifact_paths_are_derived_from_project_version(tmp_path):
    artifact_audit = load_artifact_audit_module()
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "sample"\nversion = "1.2.3b4"\n', encoding="utf-8")

    wheel_path, sdist_path = artifact_audit.default_artifact_paths(tmp_path)

    assert wheel_path == tmp_path / "dist" / "omniglyph-1.2.3b4-py3-none-any.whl"
    assert sdist_path == tmp_path / "dist" / "omniglyph-1.2.3b4.tar.gz"


def test_artifact_audit_toml_parser_supports_declared_python_versions():
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    script = Path("scripts/artifact_audit.py").read_text(encoding="utf-8")

    assert metadata["project"]["requires-python"] == ">=3.10"
    assert "import tomli as tomllib" in script
    assert 'tomli>=2.0; python_version < "3.11"' in metadata["project"]["optional-dependencies"]["dev"]
