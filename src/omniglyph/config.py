from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path("data")
    raw_dir: Path = Path("data/raw")
    sqlite_path: Path = Path("data/omniglyph.sqlite3")
    unicode_data_url: str = "https://www.unicode.org/Public/UCD/latest/ucd/UnicodeData.txt"


settings = Settings()
