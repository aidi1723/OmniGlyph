from pathlib import Path

from omniglyph.domain_pack import bundled_domain_pack, parse_domain_pack


FIXTURE = Path(__file__).parent / "fixtures" / "domain_pack.csv"
SOFTWARE_PACK = Path("examples/domain-packs/software_development.csv")


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


def test_parse_software_development_domain_pack():
    entries = list(parse_domain_pack(SOFTWARE_PACK, namespace="public_software_development"))

    terms = {entry.term: entry for entry in entries}
    assert {"API", "SDK", "MCP", "SQL injection", "Unicode confusable", "Trojan Source"}.issubset(terms)
    api = terms["API"]
    assert api.canonical_id == "software:api"
    assert api.entry_type == "software_term"
    assert "Application Programming Interface" in api.aliases
    assert api.definition == "A contract that lets software components request capabilities or data from each other."
    assert api.traits == {"domain": "software_development", "category": "interface", "maturity": "stable"}


def test_software_development_pack_is_available_as_package_resource():
    entries = list(parse_domain_pack(bundled_domain_pack("software_development"), namespace="public_software_development"))

    assert {entry.term for entry in entries} >= {"API", "MCP", "Trojan Source"}
