from dataclasses import dataclass

from omniglyph.repository import GlyphRepository


@dataclass(frozen=True)
class NormalizeResult:
    input: str
    status: str
    type: str | None
    canonical_id: str | None
    summary: dict


def normalize_tokens(repository: GlyphRepository, tokens: list[str]) -> list[dict]:
    results = []
    for token in tokens:
        if len(token) == 1:
            glyph = repository.find_by_glyph(token)
            if glyph is not None:
                results.append(
                    NormalizeResult(
                        input=token,
                        status="matched",
                        type="glyph",
                        canonical_id=f"glyph:{glyph['unicode']['hex']}",
                        summary={
                            "unicode": glyph["unicode"]["hex"],
                            "pinyin": glyph["lexical"].get("pinyin"),
                        },
                    ).__dict__
                )
                continue
        term = repository.find_term(token)
        if term is not None:
            results.append(
                NormalizeResult(
                    input=token,
                    status="matched",
                    type=term["entry_type"],
                    canonical_id=term["canonical_id"],
                    summary={
                        "term": term["term"],
                        "definition": term["definition"],
                        "traits": term["traits"],
                    },
                ).__dict__
            )
            continue
        results.append(NormalizeResult(input=token, status="unknown", type=None, canonical_id=None, summary={}).__dict__)
    return results


def compact_normalize(results: list[dict]) -> dict:
    known = {item["input"]: item["canonical_id"] for item in results if item["status"] == "matched"}
    unknown = [item["input"] for item in results if item["status"] != "matched"]
    return {"known": known, "unknown": unknown}
