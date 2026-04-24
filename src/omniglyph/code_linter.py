import json
import unicodedata
from pathlib import Path
from typing import Iterable

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
    text = file_path.read_text(encoding="utf-8")
    return scan_text(text, source_name=str(file_path))


def scan_path(path: Path | str) -> dict:
    scan_root = Path(path)
    if scan_root.is_file():
        reports = [scan_file(scan_root)]
    else:
        reports = [scan_file(file_path) for file_path in _iter_text_files(scan_root)]
    findings = []
    scanned_files = []
    for report in reports:
        scanned_files.append(report["source"])
        findings.extend(report["findings"])
    return {
        "source": str(scan_root),
        "status": "pass" if not findings else "warn",
        "summary": {"file_count": len(scanned_files), "finding_count": len(findings)},
        "files": scanned_files,
        "findings": findings,
    }


def format_text_report(report: dict) -> str:
    lines = [f"OmniGlyph Code Linter: {report['source']}"]
    finding_count = report["summary"]["finding_count"]
    if finding_count == 0:
        lines.append("PASS: no suspicious Unicode symbols found.")
        return "\n".join(lines)
    lines.append(f"WARN: found {finding_count} suspicious Unicode symbol(s).")
    for index, finding in enumerate(report["findings"], 1):
        lines.append(
            f"[{index}] {finding['source']}:{finding['line']}:{finding['column']} "
            f"{finding['unicode_hex']} {finding['name']} - {finding['message']}"
        )
    return "\n".join(lines)


def format_json_report(report: dict) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2)


def _inspect_char(char: str, line_number: int, column_number: int) -> dict | None:
    code_point = ord(char)
    name = _unicode_name(char)
    category = unicodedata.category(char)
    script_hint = _script_hint(name)
    if code_point in BIDI_CONTROL_CODEPOINTS:
        return _finding("unicode-bidi-control", "Bidi control character can visually reorder source code", char, name, category, script_hint, line_number, column_number)
    if category == "Cf":
        return _finding("unicode-invisible-format", "Invisible format character in source code", char, name, category, script_hint, line_number, column_number)
    if category == "Cc" and char not in {"\t", "\n", "\r"}:
        return _finding("unicode-control-character", "Unexpected control character in source code", char, name, category, script_hint, line_number, column_number)
    if script_hint in {"Cyrillic", "Greek"}:
        return _finding("unicode-cross-script-homoglyph-risk", "Cross-script character may be confusable with Latin source code", char, name, category, script_hint, line_number, column_number)
    return None


def _finding(rule_id: str, message: str, char: str, name: str, category: str, script_hint: str | None, line_number: int, column_number: int) -> dict:
    return {
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
    }


def _report(source_name: str, scanned_chars: int, findings: list[dict]) -> dict:
    for finding in findings:
        finding["source"] = source_name
    return {
        "source": source_name,
        "status": "pass" if not findings else "warn",
        "summary": {"scanned_chars": scanned_chars, "finding_count": len(findings)},
        "findings": findings,
    }


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


def _iter_text_files(root: Path) -> Iterable[Path]:
    for file_path in sorted(root.rglob("*")):
        if file_path.is_file() and file_path.suffix.lower() in TEXT_EXTENSIONS:
            yield file_path
