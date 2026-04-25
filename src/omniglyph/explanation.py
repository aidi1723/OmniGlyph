from omniglyph.code_linter import scan_text
from omniglyph.oes import OES_SCHEMA, empty_safety, source_payload, unknown_payload
from omniglyph.repository import GlyphRepository
from omniglyph.security_pack import source_payloads_for_findings


def explain_glyph(repository: GlyphRepository, char: str) -> dict:
    record = repository.find_by_glyph(char)
    if record is None:
        return unknown_payload(char, "glyph", "No local source-backed glyph explanation found.")

    unicode_facts = record["unicode"]
    lexical = _glyph_lexical(record)
    return {
        "schema": OES_SCHEMA,
        "input": {"text": char, "kind": "glyph", "normalized": char},
        "status": "matched",
        "canonical_id": f"glyph:{unicode_facts['hex']}",
        "basic_facts": {
            "unicode_hex": unicode_facts["hex"],
            "name": unicode_facts["name"],
            "script": None,
            "block": unicode_facts["block"],
            "general_category": None,
        },
        "lexical": lexical,
        "concept_links": [],
        "safety": empty_safety(),
        "sources": [source_payload(source, confidence=1.0) for source in record["sources"]],
        "limits": [],
    }


def explain_term(repository: GlyphRepository, text: str) -> dict:
    record = repository.find_term(text)
    normalized = _normalize_text(text)
    if record is None:
        return unknown_payload(text, "term", "No local source-backed term explanation found.", normalized=normalized)

    return {
        "schema": OES_SCHEMA,
        "input": {"text": text, "kind": "term", "normalized": normalized},
        "status": "matched",
        "canonical_id": record["canonical_id"],
        "basic_facts": {},
        "lexical": [
            {
                "language": record["language"],
                "term": record["term"],
                "matched_text": record["matched_text"],
                "normalized_term": _normalize_text(record["term"]),
                "part_of_speech": None,
                "pronunciation": None,
                "definition": record["definition"],
                "aliases": [],
                "etymology": None,
                "entry_type": record["entry_type"],
                "traits": record["traits"],
                "confidence": record["confidence"],
                "source_id": record["source_id"],
            }
        ],
        "concept_links": [],
        "safety": empty_safety(),
        "sources": [
            {
                "source_id": record["source_id"],
                "source_name": record["source_name"],
                "source_version": record["source_version"],
                "license": None,
                "confidence": record["confidence"],
            }
        ],
        "limits": [],
    }


def explain_code_security(text: str, source_name: str = "<text>") -> dict:
    report = scan_text(text, source_name=source_name)
    findings = report["findings"]
    return {
        "schema": OES_SCHEMA,
        "input": {"text": source_name, "kind": "code", "normalized": source_name},
        "status": "unsafe" if findings else "matched",
        "canonical_id": None,
        "basic_facts": {
            "source_name": source_name,
            "scanned_chars": report["summary"]["scanned_chars"],
            "finding_count": report["summary"]["finding_count"],
        },
        "lexical": [],
        "concept_links": [],
        "safety": {"risk_level": report["summary"]["risk_level"], "findings": findings},
        "sources": source_payloads_for_findings(findings),
        "limits": ["Unicode security scan covers symbol-level risks only; it does not prove code behavior is safe."],
    }


def _glyph_lexical(record: dict) -> list[dict]:
    lexical = record["lexical"]
    if lexical.get("pinyin") is None and lexical.get("basic_meaning") is None:
        return []
    source_id = _source_id_by_name(record["sources"], lexical.get("sources", {}).get("pinyin"))
    return [
        {
            "language": "zh",
            "term": record["glyph"],
            "matched_text": record["glyph"],
            "normalized_term": record["glyph"],
            "part_of_speech": None,
            "pronunciation": lexical.get("pinyin"),
            "definition": lexical.get("basic_meaning"),
            "aliases": [],
            "etymology": None,
            "entry_type": "glyph_lexical_fact",
            "traits": {},
            "confidence": 1.0,
            "source_id": source_id,
        }
    ]


def _source_id_by_name(sources: list[dict], source_name: str | None) -> str | None:
    for source in sources:
        if source["source_name"] == source_name:
            return source["id"]
    return None


def _normalize_text(text: str) -> str:
    return " ".join(text.casefold().strip().split())
