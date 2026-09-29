import unicodedata
from dataclasses import dataclass
from typing import Any, cast


@dataclass(frozen=True)
class ConfusableMapping:
    character: str
    confusable_with: str
    source_id: str
    why_it_matters: str


UNICODE_CONFUSABLES_SOURCE: dict[str, Any] = {
    "source_id": "source:unicode-confusables:minimal",
    "source_name": "OmniGlyph Unicode Confusables Minimal Pack",
    "source_version": "0.2.0",
    "license": "Unicode Terms of Use; OmniGlyph curated fixture",
    "confidence": 1.0,
}

PYTHON_UNICODEDATA_SOURCE: dict[str, Any] = {
    "source_id": f"source:python-unicodedata:{unicodedata.unidata_version}",
    "source_name": "Python unicodedata Unicode Character Database",
    "source_version": unicodedata.unidata_version,
    "license": "Python Software Foundation License; Unicode Terms of Use",
    "confidence": 1.0,
}

SECURITY_SOURCES: dict[str, dict[str, Any]] = {
    UNICODE_CONFUSABLES_SOURCE["source_id"]: UNICODE_CONFUSABLES_SOURCE,
    PYTHON_UNICODEDATA_SOURCE["source_id"]: PYTHON_UNICODEDATA_SOURCE,
}

# Single-character letters that commonly render like one Latin letter.
# Other Cyrillic and Greek letters stay on the generic cross-script rule.
_CONFUSABLE_LETTERS = (
    ("\u0430", "a", "Cyrillic small letter a"),
    ("\u0435", "e", "Cyrillic small letter ie"),
    ("\u043e", "o", "Cyrillic small letter o"),
    ("\u0440", "p", "Cyrillic small letter er"),
    ("\u0441", "c", "Cyrillic small letter es"),
    ("\u0443", "y", "Cyrillic small letter u"),
    ("\u0445", "x", "Cyrillic small letter ha"),
    ("\u0455", "s", "Cyrillic small letter dze"),
    ("\u0456", "i", "Cyrillic small letter byelorussian-ukrainian i"),
    ("\u0458", "j", "Cyrillic small letter je"),
    ("\u04cf", "l", "Cyrillic small letter palochka"),
    ("\u0410", "A", "Cyrillic capital letter a"),
    ("\u0412", "B", "Cyrillic capital letter ve"),
    ("\u0415", "E", "Cyrillic capital letter ie"),
    ("\u041a", "K", "Cyrillic capital letter ka"),
    ("\u041c", "M", "Cyrillic capital letter em"),
    ("\u041d", "H", "Cyrillic capital letter en"),
    ("\u041e", "O", "Cyrillic capital letter o"),
    ("\u0420", "P", "Cyrillic capital letter er"),
    ("\u0421", "C", "Cyrillic capital letter es"),
    ("\u0422", "T", "Cyrillic capital letter te"),
    ("\u0423", "Y", "Cyrillic capital letter u"),
    ("\u0425", "X", "Cyrillic capital letter ha"),
    ("\u0406", "I", "Cyrillic capital letter byelorussian-ukrainian i"),
    ("\u0391", "A", "Greek capital letter alpha"),
    ("\u0392", "B", "Greek capital letter beta"),
    ("\u0395", "E", "Greek capital letter epsilon"),
    ("\u0396", "Z", "Greek capital letter zeta"),
    ("\u0397", "H", "Greek capital letter eta"),
    ("\u0399", "I", "Greek capital letter iota"),
    ("\u039a", "K", "Greek capital letter kappa"),
    ("\u039c", "M", "Greek capital letter mu"),
    ("\u039d", "N", "Greek capital letter nu"),
    ("\u039f", "O", "Greek capital letter omicron"),
    ("\u03a1", "P", "Greek capital letter rho"),
    ("\u03a4", "T", "Greek capital letter tau"),
    ("\u03a5", "Y", "Greek capital letter upsilon"),
    ("\u03a7", "X", "Greek capital letter chi"),
    ("\u03bf", "o", "Greek small letter omicron"),
)


def _confusable(character: str, latin: str, name: str) -> ConfusableMapping:
    return ConfusableMapping(
        character=character,
        confusable_with=latin,
        source_id=UNICODE_CONFUSABLES_SOURCE["source_id"],
        why_it_matters=f"{name} can look like Latin {latin} in identifiers.",
    )


CONFUSABLES = {
    character: _confusable(character, latin, name) for character, latin, name in _CONFUSABLE_LETTERS
}


def find_confusable(char: str) -> ConfusableMapping | None:
    return CONFUSABLES.get(char)


def source_payloads_for_findings(findings: list[dict]) -> list[dict]:
    source_ids = sorted(cast(str, finding["source_id"]) for finding in findings if finding.get("source_id"))
    return [
        {
            "source_id": source["source_id"],
            "source_name": source["source_name"],
            "source_version": source["source_version"],
            "license": source["license"],
            "confidence": source["confidence"],
        }
        for source_id in source_ids
        if (source := SECURITY_SOURCES.get(source_id)) is not None
    ]
