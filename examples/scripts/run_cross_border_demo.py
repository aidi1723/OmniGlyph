import json
from pathlib import Path
from tempfile import TemporaryDirectory

from omniglyph.domain_pack import parse_domain_pack
from omniglyph.normalization import compact_normalize, normalize_tokens
from omniglyph.repository import GlyphRepository, SourceSnapshot

ROOT = Path(__file__).resolve().parents[2]
DOMAIN_PACK = ROOT / "examples" / "domain-packs" / "building_materials.csv"
REQUEST = ROOT / "examples" / "requests" / "cross_border_inquiry.json"


def run_demo() -> dict:
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    with TemporaryDirectory() as directory:
        repository = GlyphRepository(Path(directory) / "omniglyph-demo.sqlite3")
        repository.initialize()
        source_id = repository.add_source_snapshot(
            SourceSnapshot(
                source_name="Example Building Materials Domain Pack",
                source_url=f"file://{DOMAIN_PACK}",
                source_version="example",
                sha256="example",
                license="example-private",
                local_path=str(DOMAIN_PACK),
            )
        )
        repository.insert_lexical_entries(list(parse_domain_pack(DOMAIN_PACK, "private_building_materials")), source_id)
        results = normalize_tokens(repository, request["tokens"])
        return {"input": request["text"], "normalization": compact_normalize(results), "details": results}


def main() -> None:
    print(json.dumps(run_demo(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
