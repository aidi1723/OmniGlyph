from omniglyph.repository import GlyphRepository


def validate_output_terms(repository: GlyphRepository, terms: list[str]) -> dict:
    known = {}
    details = []
    unknown = []
    for term in terms:
        record = repository.find_term(term)
        if record is None:
            unknown.append(term)
            details.append({"term": term, "status": "unknown", "canonical_id": None})
            continue
        known[term] = record["canonical_id"]
        details.append(
            {
                "term": term,
                "status": "known",
                "canonical_id": record["canonical_id"],
                "entry_type": record["entry_type"],
                "source_name": record["source_name"],
            }
        )
    return {"status": "pass" if not unknown else "warn", "known": known, "unknown": unknown, "details": details}
