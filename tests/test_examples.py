from pathlib import Path

from omniglyph.domain_pack import parse_domain_pack


def test_building_materials_example_pack_is_parseable():
    entries = list(parse_domain_pack(Path("examples/domain-packs/building_materials.csv"), "private_building_materials"))

    canonical_ids = {entry.canonical_id for entry in entries}
    assert "material:aluminum_profile" in canonical_ids
    assert "material:tempered_glass" in canonical_ids
    assert "trade:fob" in canonical_ids
    assert "trade:moq" in canonical_ids
    assert len(entries) >= 9


def test_cross_border_demo_normalizes_expected_terms():
    from examples.scripts.run_cross_border_demo import run_demo

    output = run_demo()

    assert output["normalization"]["known"]["aluminum profile"] == "material:aluminum_profile"
    assert output["normalization"]["known"]["tempered glass"] == "material:tempered_glass"
    assert output["normalization"]["known"]["FOB"] == "trade:fob"
    assert "Bangkok" in output["normalization"]["unknown"]
