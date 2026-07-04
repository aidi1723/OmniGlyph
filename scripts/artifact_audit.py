#!/usr/bin/env python3
from __future__ import annotations

import argparse
import configparser
import json
import sys
import tarfile
import zipfile
from email.parser import Parser
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
    import tomli as tomllib

WHEEL_REQUIRED_FILES = {
    "omniglyph/__init__.py",
    "omniglyph/cli.py",
    "omniglyph/mcp_server.py",
    "omniglyph/api.py",
    "omniglyph/domain_packs/software_development.csv",
}

SDIST_REQUIRED_SUFFIXES = {
    "tests/fixtures/Unihan.sample.txt",
    "examples/scripts/run_cross_border_demo.py",
    "scripts/mcp_smoke_test.sh",
    "scripts/wheel_smoke_test.sh",
}

FORBIDDEN_PARTS = {
    ".DS_Store",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".uv-cache",
    ".venv",
    "data",
    "dist",
    "__pycache__",
}


def audit_artifacts(wheel_path: Path, sdist_path: Path) -> dict:
    errors: list[str] = []
    wheel = _audit_wheel(wheel_path, errors)
    sdist = _audit_sdist(sdist_path, errors)
    return {
        "schema": "omniglyph.artifact_audit:0.1",
        "status": "pass" if not errors else "fail",
        "wheel": wheel,
        "sdist": sdist,
        "errors": errors,
    }


def default_artifact_paths(project_root: Path | str = Path(".")) -> tuple[Path, Path]:
    root = Path(project_root)
    version = _project_version(root / "pyproject.toml")
    return (
        root / "dist" / f"omniglyph-{version}-py3-none-any.whl",
        root / "dist" / f"omniglyph-{version}.tar.gz",
    )


def _audit_wheel(wheel_path: Path, errors: list[str]) -> dict:
    if not wheel_path.exists():
        errors.append(f"wheel not found: {wheel_path}")
        return {"path": str(wheel_path), "files": 0, "requires_dist": [], "entry_points": {}}
    with zipfile.ZipFile(wheel_path) as archive:
        names = set(archive.namelist())
        _record_missing("wheel", WHEEL_REQUIRED_FILES, names, errors)
        _record_forbidden("wheel", names, errors)
        metadata_name = _single_name(names, ".dist-info/METADATA", "wheel METADATA", errors)
        entry_points_name = _single_name(names, ".dist-info/entry_points.txt", "wheel entry_points.txt", errors)
        requires_dist = []
        entry_points = {}
        if metadata_name is not None:
            metadata = Parser().parsestr(archive.read(metadata_name).decode("utf-8"))
            requires_dist = metadata.get_all("Requires-Dist") or []
            for requirement in ("fastapi>=0.110", "uvicorn[standard]>=0.27"):
                if requirement not in requires_dist:
                    errors.append(f"wheel metadata missing Requires-Dist: {requirement}")
        if entry_points_name is not None:
            parser = configparser.ConfigParser()
            parser.read_string(archive.read(entry_points_name).decode("utf-8"))
            entry_points = dict(parser["console_scripts"]) if parser.has_section("console_scripts") else {}
            expected_entry_points = {
                "omniglyph": "omniglyph.cli:main",
                "omniglyph-mcp": "omniglyph.mcp_server:main",
            }
            for name, target in expected_entry_points.items():
                if entry_points.get(name) != target:
                    errors.append(f"wheel entry point {name} must target {target}")
    return {
        "path": str(wheel_path),
        "files": len(names),
        "requires_dist": requires_dist,
        "entry_points": entry_points,
    }


def _audit_sdist(sdist_path: Path, errors: list[str]) -> dict:
    if not sdist_path.exists():
        errors.append(f"sdist not found: {sdist_path}")
        return {"path": str(sdist_path), "files": 0}
    with tarfile.open(sdist_path) as archive:
        names = set(archive.getnames())
    for suffix in SDIST_REQUIRED_SUFFIXES:
        if not any(name.endswith(suffix) for name in names):
            errors.append(f"sdist missing required file ending with: {suffix}")
    _record_forbidden("sdist", names, errors)
    return {"path": str(sdist_path), "files": len(names)}


def _record_missing(label: str, required: set[str], names: set[str], errors: list[str]) -> None:
    for path in sorted(required):
        if path not in names:
            errors.append(f"{label} missing required file: {path}")


def _record_forbidden(label: str, names: set[str], errors: list[str]) -> None:
    for name in sorted(names):
        parts = set(Path(name).parts)
        forbidden = sorted(parts & FORBIDDEN_PARTS)
        if forbidden:
            errors.append(f"{label} contains forbidden path {name}: {', '.join(forbidden)}")


def _single_name(names: set[str], suffix: str, label: str, errors: list[str]) -> str | None:
    matches = sorted(name for name in names if name.endswith(suffix))
    if len(matches) != 1:
        errors.append(f"expected exactly one {label}, found {len(matches)}")
        return None
    return matches[0]


def _project_version(pyproject_path: Path) -> str:
    with pyproject_path.open("rb") as handle:
        metadata = tomllib.load(handle)
    version = metadata.get("project", {}).get("version")
    if not isinstance(version, str) or not version:
        raise ValueError(f"project.version missing from {pyproject_path}")
    return version


def main() -> None:
    default_wheel, default_sdist = default_artifact_paths()
    parser = argparse.ArgumentParser(prog="artifact_audit.py")
    parser.add_argument("--wheel", type=Path, default=default_wheel)
    parser.add_argument("--sdist", type=Path, default=default_sdist)
    parser.add_argument("--quiet", action="store_true", help="print a one-line summary instead of the full JSON report")
    args = parser.parse_args()
    report = audit_artifacts(args.wheel, args.sdist)
    if args.quiet:
        _print_quiet_report(report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "pass":
        raise SystemExit(1)


def _print_quiet_report(report: dict) -> None:
    if report["status"] == "pass":
        print("artifact audit ok")
        return
    errors = report.get("errors", [])
    print(f"artifact audit failed: {len(errors)} error(s)", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
