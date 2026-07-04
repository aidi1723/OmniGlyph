import json
import unicodedata
from collections.abc import Iterable
from pathlib import Path

from omniglyph.oes import risk_level_for_findings
from omniglyph.security_pack import PYTHON_UNICODEDATA_SOURCE, find_confusable

BIDI_CONTROL_CODEPOINTS = {
    0x061C,
    0x200E,
    0x200F,
    0x202A,
    0x202B,
    0x202C,
    0x202D,
    0x202E,
    0x2066,
    0x2067,
    0x2068,
    0x2069,
}

SCRIPT_NAME_HINTS = {
    "CYRILLIC": "Cyrillic",
    "GREEK": "Greek",
}

TEXT_EXTENSIONS = {
    ".bash",
    ".c",
    ".cc",
    ".cfg",
    ".conf",
    ".cpp",
    ".css",
    ".csv",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

SKIPPED_DIRECTORY_NAMES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".uv-cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}


def scan_text(text: str, source_name: str = "<text>") -> dict:
    findings = []
    for line_number, line in enumerate(text.splitlines(), 1):
        for column_number, char in enumerate(line, 1):
            finding = _inspect_char(char, line_number, column_number)
            if finding is not None:
                findings.append(finding)
    return _report(source_name, len(text), findings)


def scan_file(path: Path | str) -> dict:
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return _file_error_report(file_path, "UnicodeDecodeError", "file is not valid UTF-8 text")
    except OSError as exc:
        return _file_error_report(file_path, type(exc).__name__, str(exc))
    return scan_text(text, source_name=str(file_path))


def scan_path(path: Path | str) -> dict:
    scan_root = Path(path)
    if not scan_root.exists():
        reports = [_file_error_report(scan_root, "FileNotFoundError", "path does not exist")]
    elif scan_root.is_file():
        reports = [scan_file(scan_root)]
    else:
        reports = [scan_file(file_path) for file_path in _iter_text_files(scan_root)]
    findings = []
    scanned_files = []
    failed_files = []
    for report in reports:
        if report["status"] == "error":
            failed_files.extend(report["failed_files"])
            continue
        scanned_files.append(report["source"])
        findings.extend(report["findings"])
    status = "error" if failed_files else "warn" if findings else "pass"
    return {
        "source": str(scan_root),
        "status": status,
        "summary": {"file_count": len(scanned_files), "finding_count": len(findings), "failed_count": len(failed_files)},
        "files": scanned_files,
        "failed_files": failed_files,
        "findings": findings,
    }


def format_text_report(report: dict) -> str:
    lines = [f"OmniGlyph Code Linter: {report['source']}"]
    failed_files = report.get("failed_files", [])
    if failed_files:
        lines.append(f"ERROR: failed to scan {len(failed_files)} file(s).")
        for failure in failed_files:
            lines.append(f"[error] {failure['source']} {failure['error_type']} - {failure['message']}")
    finding_count = report["summary"]["finding_count"]
    if finding_count == 0 and not failed_files:
        lines.append("PASS: no suspicious Unicode symbols found.")
        return "\n".join(lines)
    if finding_count == 0:
        return "\n".join(lines)
    lines.append(f"WARN: found {finding_count} suspicious Unicode symbol(s).")
    for index, finding in enumerate(report["findings"], 1):
        guidance = _format_guidance(finding)
        lines.append(
            f"[{index}] {finding['source']}:{finding['line']}:{finding['column']} "
            f"{finding['unicode_hex']} {finding['name']} - {finding['message']}{guidance}"
        )
    return "\n".join(lines)


def format_json_report(report: dict) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2)


def _inspect_char(char: str, line_number: int, column_number: int) -> dict | None:
    code_point = ord(char)
    name = _unicode_name(char)
    category = unicodedata.category(char)
    script_hint = _script_hint(name)
    normalized = unicodedata.normalize("NFKC", char)
    if code_point in BIDI_CONTROL_CODEPOINTS:
        return _finding(
            "unicode-bidi-control",
            "Bidi control character can visually reorder source code",
            char,
            name,
            category,
            script_hint,
            line_number,
            column_number,
            why_it_matters="Bidi controls can make code display in a different order than it is compiled or interpreted.",
        )
    if category == "Cf":
        return _finding(
            "unicode-invisible-format",
            "Invisible format character in source code",
            char,
            name,
            category,
            script_hint,
            line_number,
            column_number,
            why_it_matters="Invisible format characters can hide unexpected tokens inside copied code.",
        )
    if category == "Cc" and char not in {"\t", "\n", "\r"}:
        return _finding(
            "unicode-control-character",
            "Unexpected control character in source code",
            char,
            name,
            category,
            script_hint,
            line_number,
            column_number,
            why_it_matters="Unexpected control characters can alter parsing, terminals, or downstream tooling.",
        )
    confusable = find_confusable(char)
    if confusable is not None:
        return _finding(
            "unicode-confusable",
            f"Character may be mistaken for Latin {confusable.confusable_with}",
            char,
            name,
            category,
            script_hint,
            line_number,
            column_number,
            confusable_with=confusable.confusable_with,
            source_id=confusable.source_id,
            why_it_matters=confusable.why_it_matters,
        )
    if _is_fullwidth_or_halfwidth(code_point):
        return _finding(
            "unicode-fullwidth-halfwidth-form",
            "Fullwidth or halfwidth character may hide source-code intent",
            char,
            name,
            category,
            script_hint,
            line_number,
            column_number,
            normalized=normalized,
            why_it_matters="Fullwidth and halfwidth forms can look similar to ASCII while tokenizing differently.",
        )
    if script_hint in {"Cyrillic", "Greek"}:
        return _finding(
            "unicode-cross-script-homoglyph-risk",
            "Cross-script character may be confusable with Latin source code",
            char,
            name,
            category,
            script_hint,
            line_number,
            column_number,
            why_it_matters="Mixed-script identifiers deserve review because some glyphs are hard to distinguish visually.",
        )
    if normalized != char:
        return _finding(
            "unicode-nfkc-normalization-change",
            "Character changes under NFKC normalization",
            char,
            name,
            category,
            script_hint,
            line_number,
            column_number,
            normalized=normalized,
            why_it_matters="Normalization-sensitive characters can compare or render differently across systems.",
        )
    return None


def _finding(
    rule_id: str,
    message: str,
    char: str,
    name: str,
    category: str,
    script_hint: str | None,
    line_number: int,
    column_number: int,
    normalized: str | None = None,
    confusable_with: str | None = None,
    source_id: str | None = None,
    suggested_action: str = "review",
    auto_fixable: bool = False,
    why_it_matters: str | None = None,
) -> dict:
    finding = {
        "rule_id": rule_id,
        "severity": "warning",
        "message": message,
        "line": line_number,
        "column": column_number,
        "character": char if unicodedata.category(char) != "Cf" else "",
        "unicode_hex": f"U+{ord(char):04X}",
        "name": name,
        "category": category,
        "script_hint": script_hint,
        "source_id": source_id or PYTHON_UNICODEDATA_SOURCE["source_id"],
        "suggested_action": suggested_action,
        "auto_fixable": auto_fixable,
        "why_it_matters": why_it_matters or message,
    }
    if normalized is not None:
        finding["normalized"] = normalized
    if confusable_with is not None:
        finding["confusable_with"] = confusable_with
    return finding


def _report(source_name: str, scanned_chars: int, findings: list[dict]) -> dict:
    for finding in findings:
        finding["source"] = source_name
    rule_counts: dict[str, int] = {}
    for finding in findings:
        rule_counts[finding["rule_id"]] = rule_counts.get(finding["rule_id"], 0) + 1
    return {
        "source": source_name,
        "status": "pass" if not findings else "warn",
        "summary": {
            "scanned_chars": scanned_chars,
            "finding_count": len(findings),
            "risk_level": risk_level_for_findings(findings),
            "rule_counts": rule_counts,
        },
        "findings": findings,
    }


def _file_error_report(file_path: Path, error_type: str, message: str) -> dict:
    return {
        "source": str(file_path),
        "status": "error",
        "summary": {
            "scanned_chars": 0,
            "finding_count": 0,
            "risk_level": "unknown",
            "rule_counts": {},
        },
        "failed_files": [{"source": str(file_path), "error_type": error_type, "message": message}],
        "findings": [],
    }


def _format_guidance(finding: dict) -> str:
    parts = []
    if finding.get("confusable_with"):
        parts.append(f"confusable with {finding['confusable_with']}")
    if finding.get("suggested_action"):
        parts.append(f"action={finding['suggested_action']}")
    if not parts:
        return ""
    return f" ({'; '.join(parts)})"


def _unicode_name(char: str) -> str:
    try:
        return unicodedata.name(char)
    except ValueError:
        return "UNKNOWN"


def _script_hint(name: str) -> str | None:
    for marker, script in SCRIPT_NAME_HINTS.items():
        if marker in name:
            return script
    return None


def _is_fullwidth_or_halfwidth(code_point: int) -> bool:
    return 0xFF00 <= code_point <= 0xFFEF


def _iter_text_files(root: Path) -> Iterable[Path]:
    for file_path in sorted(root.rglob("*")):
        if any(part in SKIPPED_DIRECTORY_NAMES for part in file_path.relative_to(root).parts[:-1]):
            continue
        if file_path.is_file() and file_path.suffix.lower() in TEXT_EXTENSIONS:
            yield file_path
