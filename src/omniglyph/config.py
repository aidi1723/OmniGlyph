import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path("data")
    raw_dir: Path = Path("data/raw")
    sqlite_path: Path = Path("data/omniglyph.sqlite3")
    lexicon_pack_root: Path | None = None
    unicode_data_url: str = "https://www.unicode.org/Public/UCD/latest/ucd/UnicodeData.txt"


def load_settings() -> Settings:
    data_dir = Path(os.environ.get("OMNIGLYPH_DATA_DIR", "data"))
    raw_dir = Path(os.environ.get("OMNIGLYPH_RAW_DIR", str(data_dir / "raw")))
    sqlite_path = Path(os.environ.get("OMNIGLYPH_SQLITE_PATH", str(data_dir / "omniglyph.sqlite3")))
    lexicon_pack_root_raw = os.environ.get("OMNIGLYPH_LEXICON_PACK_ROOT")
    lexicon_pack_root = Path(lexicon_pack_root_raw) if lexicon_pack_root_raw else None
    unicode_data_url = os.environ.get("OMNIGLYPH_UNICODE_DATA_URL", Settings.unicode_data_url)
    return Settings(
        data_dir=data_dir,
        raw_dir=raw_dir,
        sqlite_path=sqlite_path,
        lexicon_pack_root=lexicon_pack_root,
        unicode_data_url=unicode_data_url,
    )


settings = load_settings()
