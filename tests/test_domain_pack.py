from pathlib import Path

from omniglyph.domain_pack import parse_domain_pack


FIXTURE = Path(__file__).parent / "fixtures" / "domain_pack.csv"


def test_parse_domain_pack_reads_terms_aliases_and_traits():
    entries = list(parse_domain_pack(FIXTURE, namespace="private_building_materials"))

    first = entries[0]
    assert first.term == "aluminum profile"
    assert first.canonical_id == "material:aluminum_profile"
    assert first.entry_type == "material"
    assert first.aliases == ["aluminium profile", "铝型材"]
    assert first.traits == {"material": "aluminum", "domain": "construction"}
    assert first.namespace == "private_building_materials"


def test_parse_domain_pack_skips_incomplete_rows(tmp_path):
    source = tmp_path / "bad.csv"
    source.write_text("term,canonical_id,entry_type,language,aliases,definition,traits\nFOB,trade:fob,trade_term,en,,Free On Board,{}\nmissing,,trade_term,en,,,{}\n", encoding="utf-8")

    entries = list(parse_domain_pack(source, namespace="private_trade"))

    assert len(entries) == 1
    assert entries[0].term == "FOB"
