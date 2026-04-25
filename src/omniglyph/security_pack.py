import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class ConfusableMapping:
    character: str
    confusable_with: str
    source_id: str
    why_it_matters: str


UNICODE_CONFUSABLES_SOURCE = {
    "source_id": "source:unicode-confusables:minimal",
    "source_name": "OmniGlyph Unicode Confusables Minimal Pack",
    "source_version": "0.1.0",
    "license": "Unicode Terms of Use; OmniGlyph curated fixture",
    "confidence": 1.0,
}

PYTHON_UNICODEDATA_SOURCE = {
    "source_id": f"source:python-unicodedata:{unicodedata.unidata_version}",
    "source_name": "Python unicodedata Unicode Character Database",
    "source_version": unicodedata.unidata_version,
    "license": "Python Software Foundation License; Unicode Terms of Use",
    "confidence": 1.0,
}

SECURITY_SOURCES = {
    UNICODE_CONFUSABLES_SOURCE["source_id"]: UNICODE_CONFUSABLES_SOURCE,
    PYTHON_UNICODEDATA_SOURCE["source_id"]: PYTHON_UNICODEDATA_SOURCE,
}

CONFUSABLES = {
    "\u0430": ConfusableMapping(
        character="\u0430",
        confusable_with="a",
        source_id=UNICODE_CONFUSABLES_SOURCE["source_id"],
        why_it_matters="Cyrillic small letter a can look like Latin small letter a in identifiers.",
    ),
    "\u0435": ConfusableMapping(
        character="\u0435",
        confusable_with="e",
        source_id=UNICODE_CONFUSABLES_SOURCE["source_id"],
        why_it_matters="Cyrillic small letter ie can look like Latin small letter e in identifiers.",
    ),
    "\u043e": ConfusableMapping(
        character="\u043e",
        confusable_with="o",
        source_id=UNICODE_CONFUSABLES_SOURCE["source_id"],
        why_it_matters="Cyrillic small letter o can look like Latin small letter o in identifiers.",
    ),
    "\u0391": ConfusableMapping(
        character="\u0391",
        confusable_with="A",
        source_id=UNICODE_CONFUSABLES_SOURCE["source_id"],
        why_it_matters="Greek capital alpha can look like Latin capital A in identifiers.",
    ),
    "\u03bf": ConfusableMapping(
        character="\u03bf",
        confusable_with="o",
        source_id=UNICODE_CONFUSABLES_SOURCE["source_id"],
        why_it_matters="Greek small omicron can look like Latin small letter o in identifiers.",
    ),
}


def find_confusable(char: str) -> ConfusableMapping | None:
    return CONFUSABLES.get(char)


def source_payloads_for_findings(findings: list[dict]) -> list[dict]:
    source_ids = sorted({finding.get("source_id") for finding in findings if finding.get("source_id")})
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
