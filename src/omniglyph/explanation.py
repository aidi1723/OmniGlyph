from omniglyph.repository import GlyphRepository

OES_SCHEMA = "oes:0.1"


def explain_glyph(repository: GlyphRepository, char: str) -> dict:
    record = repository.find_by_glyph(char)
    if record is None:
        return _unknown_payload(char, "glyph", "No local source-backed glyph explanation found.")

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
        "safety": {"risk_level": "none", "findings": []},
        "sources": [_source_payload(source, confidence=1.0) for source in record["sources"]],
        "limits": [],
    }


def explain_term(repository: GlyphRepository, text: str) -> dict:
    record = repository.find_term(text)
    normalized = _normalize_text(text)
    if record is None:
        return _unknown_payload(text, "term", "No local source-backed term explanation found.", normalized=normalized)

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
        "safety": {"risk_level": "none", "findings": []},
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


def _source_payload(source: dict, confidence: float) -> dict:
    return {
        "source_id": source["id"],
        "source_name": source["source_name"],
        "source_version": source["source_version"],
        "license": source["license"],
        "confidence": confidence,
    }


def _unknown_payload(text: str, kind: str, message: str, normalized: str | None = None) -> dict:
    return {
        "schema": OES_SCHEMA,
        "input": {"text": text, "kind": kind, "normalized": text if normalized is None else normalized},
        "status": "unknown",
        "canonical_id": None,
        "basic_facts": {},
        "lexical": [],
        "concept_links": [],
        "safety": {"risk_level": "none", "findings": []},
        "sources": [],
        "limits": [message],
    }


def _normalize_text(text: str) -> str:
    return " ".join(text.casefold().strip().split())
