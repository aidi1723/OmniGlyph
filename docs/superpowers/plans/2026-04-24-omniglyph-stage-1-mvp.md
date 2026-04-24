# OmniGlyph Stage 1 MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Stage 1 agent symbol fact base with deterministic Unicode ingestion, source snapshots, extensible glyph properties, SQLite-backed storage, and a read-only query API.

**Architecture:** Implement a minimal Python service with clear subsystem boundaries: ingestion preserves raw source artifacts, normalization converts Unicode rows into `glyph_node` plus `glyph_property` records, persistence stores source snapshots and source-backed properties, and the API exposes exact glyph lookup for agents. Use SQLite for the MVP so the system runs locally without infrastructure, while keeping schema names compatible with the future PostgreSQL + pgvector target.

**Tech Stack:** Python 3.11+, FastAPI, SQLite, pytest, standard-library `urllib`, `csv`, `sqlite3`, and `uuid`.

---

## File Structure

- Create: `pyproject.toml` — package metadata, dependencies, test config.
- Create: `src/omniglyph/__init__.py` — package marker.
- Create: `src/omniglyph/config.py` — filesystem paths and source URL config.
- Create: `src/omniglyph/sources.py` — raw source download and checksum logic.
- Create: `src/omniglyph/normalizer.py` — deterministic UnicodeData parser.
- Create: `src/omniglyph/repository.py` — SQLite schema for `source_snapshot`, `glyph_node`, `glyph_property`, and query layer.
- Create: `src/omniglyph/api.py` — FastAPI read-only endpoint.
- Create: `src/omniglyph/cli.py` — local ingestion command.
- Create: `tests/fixtures/UnicodeData.sample.txt` — deterministic fixture covering Latin, CJK, emoji, combining marks, variation selectors, and empty-ish Unicode fields.
- Create: `tests/test_normalizer.py` — parser and NULL behavior tests.
- Create: `tests/test_repository.py` — schema, upsert, and lookup tests.
- Create: `tests/test_api.py` — read-only endpoint contract tests.

## Task 1: Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `src/omniglyph/__init__.py`
- Create: `src/omniglyph/config.py`

- [ ] **Step 1: Create package metadata**

```toml
[project]
name = "omniglyph"
version = "0.1.0"
description = "Global civilization glyph base and semantic computation engine"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.110",
  "uvicorn[standard]>=0.27",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "httpx>=0.27",
]

[project.scripts]
omniglyph = "omniglyph.cli:main"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 2: Create package marker**

```python
__all__ = ["__version__"]

__version__ = "0.1.0"
```

- [ ] **Step 3: Create path config**

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path("data")
    raw_dir: Path = Path("data/raw")
    sqlite_path: Path = Path("data/omniglyph.sqlite3")
    unicode_data_url: str = "https://www.unicode.org/Public/UCD/latest/ucd/UnicodeData.txt"


settings = Settings()
```

- [ ] **Step 4: Run import check**

Run: `python -c "from omniglyph.config import settings; print(settings.sqlite_path)"`

Expected: prints `data/omniglyph.sqlite3`.

## Task 2: Unicode Normalizer

**Files:**
- Create: `src/omniglyph/normalizer.py`
- Create: `tests/fixtures/UnicodeData.sample.txt`
- Create: `tests/test_normalizer.py`

- [ ] **Step 1: Add fixture**

```text
0041;LATIN CAPITAL LETTER A;Lu;0;L;;;;;N;;;;0061;
0301;COMBINING ACUTE ACCENT;Mn;230;NSM;;;;;N;NON-SPACING ACUTE;;;;
FE0F;VARIATION SELECTOR-16;Mn;0;NSM;;;;;N;;;;;
94DD;CJK UNIFIED IDEOGRAPH-94DD;Lo;0;L;;;;;N;;;;;
1F600;GRINNING FACE;So;0;ON;;;;;N;;;;;
```

- [ ] **Step 2: Write failing parser tests**

```python
from pathlib import Path

from omniglyph.normalizer import parse_unicode_data


FIXTURE = Path(__file__).parent / "fixtures" / "UnicodeData.sample.txt"


def test_parse_unicode_data_maps_codepoint_and_glyph():
    records = list(parse_unicode_data(FIXTURE))

    assert records[0].glyph == "A"
    assert records[0].unicode_hex == "U+0041"
    assert records[0].basic_definition == "LATIN CAPITAL LETTER A"


def test_parse_unicode_data_supports_cjk_without_guessing_definition():
    records = list(parse_unicode_data(FIXTURE))

    assert records[3].glyph == "铝"
    assert records[3].unicode_hex == "U+94DD"
    assert records[3].basic_definition == "CJK UNIFIED IDEOGRAPH-94DD"
    assert records[3].etymology_tree is None
    assert records[3].semantic_vector is None
    assert records[3].computable_traits is None


def test_parse_unicode_data_skips_malformed_rows():
    malformed = FIXTURE.parent / "UnicodeData.malformed.txt"
    malformed.write_text("0041;LATIN CAPITAL LETTER A\nnot-hex;BROKEN\n", encoding="utf-8")

    records = list(parse_unicode_data(malformed))

    assert len(records) == 1
    assert records[0].glyph == "A"


def test_parse_unicode_data_covers_combining_marks_variation_selectors_and_emoji():
    records = list(parse_unicode_data(FIXTURE))

    assert records[1].glyph == "\u0301"
    assert records[2].unicode_hex == "U+FE0F"
    assert records[4].glyph == "😀"
```

- [ ] **Step 3: Run failing tests**

Run: `pytest tests/test_normalizer.py -v`

Expected: FAIL because `omniglyph.normalizer` does not exist.

- [ ] **Step 4: Implement normalizer**

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class GlyphRecord:
    glyph: str
    unicode_hex: str
    basic_definition: str | None
    etymology_tree: dict | None = None
    semantic_vector: list[float] | None = None
    computable_traits: dict | None = None
    source_name: str = "Unicode Character Database"
    source_file: str = "UnicodeData.txt"
    source_field: str = "Name"
    source_value: str | None = None


def parse_unicode_data(path: Path) -> Iterator[GlyphRecord]:
    with path.open("r", encoding="utf-8") as source:
        for line in source:
            fields = line.rstrip("\n").split(";")
            if len(fields) < 2:
                continue

            codepoint_hex, character_name = fields[0], fields[1]
            try:
                glyph = chr(int(codepoint_hex, 16))
            except ValueError:
                continue

            yield GlyphRecord(
                glyph=glyph,
                unicode_hex=f"U+{codepoint_hex.upper().zfill(4)}",
                basic_definition=character_name or None,
                source_value=character_name or None,
            )
```

- [ ] **Step 5: Run passing tests**

Run: `pytest tests/test_normalizer.py -v`

Expected: PASS.

## Task 3: SQLite Repository With Source Snapshots and Append-Only Properties

**Files:**
- Create: `src/omniglyph/repository.py`
- Create: `tests/test_repository.py`

- [ ] **Step 1: Write failing repository tests**

```python
from omniglyph.normalizer import GlyphRecord
from omniglyph.repository import GlyphRepository, SourceSnapshot


def test_repository_inserts_source_snapshot_and_finds_glyph(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    source = SourceSnapshot(
        source_name="Unicode Character Database",
        source_url="file://UnicodeData.sample.txt",
        source_version="fixture",
        sha256="fixture-sha256",
        license="Unicode Terms of Use",
        local_path="tests/fixtures/UnicodeData.sample.txt",
    )
    source_id = repository.add_source_snapshot(source)
    repository.insert_glyph_records([
        GlyphRecord(glyph="A", unicode_hex="U+0041", basic_definition="LATIN CAPITAL LETTER A", source_value="LATIN CAPITAL LETTER A")
    ], source_id=source_id)

    record = repository.find_by_glyph("A")

    assert record is not None
    assert record["glyph"] == "A"
    assert record["unicode"]["hex"] == "U+0041"
    assert record["unicode"]["name"] == "LATIN CAPITAL LETTER A"
    assert record["properties"][0]["confidence"] == 1.0
    assert record["sources"][0]["source_name"] == "Unicode Character Database"


def test_repository_preserves_multiple_source_values_without_overwrite(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    unicode_source = repository.add_source_snapshot(SourceSnapshot("Unicode Character Database", "file://u", "fixture", "sha-u", "Unicode Terms of Use", "u"))
    private_source = repository.add_source_snapshot(SourceSnapshot("Private Domain Pack", "file://p", "fixture", "sha-p", "private", "p"))

    repository.insert_glyph_records([
        GlyphRecord(glyph="铝", unicode_hex="U+94DD", basic_definition="CJK UNIFIED IDEOGRAPH-94DD", source_value="CJK UNIFIED IDEOGRAPH-94DD")
    ], source_id=unicode_source)
    repository.insert_property(
        glyph="铝",
        namespace="private_building_materials",
        name="trade_code",
        value="HS 7604.21",
        source_id=private_source,
        confidence=0.9,
    )

    record = repository.find_by_glyph("铝")

    property_names = {(item["namespace"], item["name"], item["value"]) for item in record["properties"]}
    assert ("unicode", "name", "CJK UNIFIED IDEOGRAPH-94DD") in property_names
    assert ("private_building_materials", "trade_code", "HS 7604.21") in property_names


def test_repository_returns_none_for_unknown_glyph(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()

    assert repository.find_by_glyph("水") is None
```

- [ ] **Step 2: Run failing tests**

Run: `pytest tests/test_repository.py -v`

Expected: FAIL because `omniglyph.repository` does not exist.

- [ ] **Step 3: Implement repository**

```python
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from omniglyph.normalizer import GlyphRecord


@dataclass(frozen=True)
class SourceSnapshot:
    source_name: str
    source_url: str
    source_version: str
    sha256: str
    license: str
    local_path: str


class GlyphRepository:
    def __init__(self, sqlite_path: Path):
        self.sqlite_path = sqlite_path

    def connect(self) -> sqlite3.Connection:
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.sqlite_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS source_snapshot (
                    id TEXT PRIMARY KEY,
                    source_name TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    source_version TEXT NOT NULL,
                    retrieved_at TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    license TEXT NOT NULL,
                    local_path TEXT NOT NULL,
                    UNIQUE(source_name, source_version, sha256)
                );

                CREATE TABLE IF NOT EXISTS glyph_node (
                    uid TEXT PRIMARY KEY,
                    glyph TEXT NOT NULL UNIQUE,
                    unicode_hex TEXT NOT NULL UNIQUE,
                    unicode_version TEXT,
                    name TEXT,
                    general_category TEXT,
                    script TEXT,
                    block TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS glyph_property (
                    id TEXT PRIMARY KEY,
                    glyph_uid TEXT NOT NULL,
                    property_namespace TEXT NOT NULL,
                    property_name TEXT NOT NULL,
                    property_value TEXT,
                    value_type TEXT NOT NULL,
                    language TEXT,
                    source_id TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (glyph_uid) REFERENCES glyph_node(uid),
                    FOREIGN KEY (source_id) REFERENCES source_snapshot(id),
                    UNIQUE(glyph_uid, property_namespace, property_name, property_value, language, source_id)
                );
                """
            )

    def add_source_snapshot(self, source: SourceSnapshot) -> str:
        source_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"omniglyph:source:{source.source_name}:{source.source_version}:{source.sha256}"))
        with self.connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO source_snapshot (
                    id, source_name, source_url, source_version, retrieved_at,
                    sha256, license, local_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    source.source_name,
                    source.source_url,
                    source.source_version,
                    datetime.now(timezone.utc).isoformat(),
                    source.sha256,
                    source.license,
                    source.local_path,
                ),
            )
        return source_id

    def insert_glyph_records(self, records: list[GlyphRecord], source_id: str) -> None:
        with self.connect() as connection:
            for record in records:
                glyph_uid = self._glyph_uid(record.unicode_hex)
                now = datetime.now(timezone.utc).isoformat()
                connection.execute(
                    """
                    INSERT INTO glyph_node (
                        uid, glyph, unicode_hex, unicode_version, name,
                        general_category, script, block, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(glyph) DO UPDATE SET
                        updated_at = excluded.updated_at
                    """,
                    (
                        glyph_uid,
                        record.glyph,
                        record.unicode_hex,
                        None,
                        record.basic_definition,
                        None,
                        None,
                        None,
                        now,
                        now,
                    ),
                )
                if record.basic_definition is not None:
                    self._insert_property_with_connection(
                        connection,
                        glyph_uid=glyph_uid,
                        namespace="unicode",
                        name="name",
                        value=record.basic_definition,
                        source_id=source_id,
                        confidence=1.0,
                    )

    def insert_property(
        self,
        glyph: str,
        namespace: str,
        name: str,
        value: str,
        source_id: str,
        confidence: float,
        language: str | None = None,
    ) -> None:
        with self.connect() as connection:
            row = connection.execute("SELECT uid FROM glyph_node WHERE glyph = ?", (glyph,)).fetchone()
            if row is None:
                raise ValueError(f"glyph not found: {glyph}")
            self._insert_property_with_connection(
                connection,
                glyph_uid=row["uid"],
                namespace=namespace,
                name=name,
                value=value,
                source_id=source_id,
                confidence=confidence,
                language=language,
            )

    def find_by_glyph(self, glyph: str) -> dict | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM glyph_node WHERE glyph = ?", (glyph,)).fetchone()
            if row is None:
                return None
            properties = connection.execute(
                """
                SELECT gp.property_namespace, gp.property_name, gp.property_value,
                       gp.value_type, gp.language, gp.confidence, gp.source_id,
                       ss.source_name, ss.source_version
                FROM glyph_property gp
                JOIN source_snapshot ss ON ss.id = gp.source_id
                WHERE gp.glyph_uid = ?
                ORDER BY gp.property_namespace, gp.property_name, gp.source_id
                """,
                (row["uid"],),
            ).fetchall()
            sources = connection.execute(
                """
                SELECT DISTINCT ss.id, ss.source_name, ss.source_url, ss.source_version,
                       ss.sha256, ss.license, ss.local_path
                FROM glyph_property gp
                JOIN source_snapshot ss ON ss.id = gp.source_id
                WHERE gp.glyph_uid = ?
                ORDER BY ss.source_name, ss.source_version
                """,
                (row["uid"],),
            ).fetchall()
            return {
                "uid": row["uid"],
                "glyph": row["glyph"],
                "unicode": {"hex": row["unicode_hex"], "name": row["name"], "block": row["block"]},
                "properties": [
                    {
                        "namespace": item["property_namespace"],
                        "name": item["property_name"],
                        "value": item["property_value"],
                        "value_type": item["value_type"],
                        "language": item["language"],
                        "confidence": item["confidence"],
                        "source_id": item["source_id"],
                        "source_name": item["source_name"],
                        "source_version": item["source_version"],
                    }
                    for item in properties
                ],
                "sources": [dict(source) for source in sources],
            }

    def _insert_property_with_connection(
        self,
        connection: sqlite3.Connection,
        glyph_uid: str,
        namespace: str,
        name: str,
        value: str,
        source_id: str,
        confidence: float,
        language: str | None = None,
    ) -> None:
        connection.execute(
            """
            INSERT OR IGNORE INTO glyph_property (
                id, glyph_uid, property_namespace, property_name, property_value,
                value_type, language, source_id, confidence, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                glyph_uid,
                namespace,
                name,
                value,
                "string",
                language,
                source_id,
                confidence,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

    def _glyph_uid(self, unicode_hex: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"omniglyph:glyph:{unicode_hex}"))
```

- [ ] **Step 4: Run passing tests**

Run: `pytest tests/test_repository.py -v`

Expected: PASS.

## Task 4: Raw Source Registration and Explicit Download

**Files:**
- Create: `src/omniglyph/sources.py`

- [ ] **Step 1: Implement checksum and explicit download helpers**

```python
import hashlib
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlretrieve


@dataclass(frozen=True)
class SourceArtifact:
    path: Path
    source_url: str
    source_version: str
    sha256: str
    license: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def register_local_source(path: Path, source_url: str, source_version: str, license: str) -> SourceArtifact:
    return SourceArtifact(
        path=path,
        source_url=source_url,
        source_version=source_version,
        sha256=sha256_file(path),
        license=license,
    )


def download_source(url: str, destination: Path, source_version: str, license: str) -> SourceArtifact:
    destination.parent.mkdir(parents=True, exist_ok=True)
    urlretrieve(url, destination)
    return register_local_source(destination, url, source_version, license)
```

- [ ] **Step 2: Run import check**

Run: `python -c "from omniglyph.sources import register_local_source, sha256_file; print(register_local_source, sha256_file)"`

Expected: prints function references.

## Task 5: Read-Only API

**Files:**
- Create: `src/omniglyph/api.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Write failing API tests**

```python
from fastapi.testclient import TestClient

from omniglyph.api import create_app
from omniglyph.normalizer import GlyphRecord
from omniglyph.repository import GlyphRepository, SourceSnapshot


def seeded_repository(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    source_id = repository.add_source_snapshot(SourceSnapshot("Unicode Character Database", "file://fixture", "fixture", "sha", "Unicode Terms of Use", "fixture"))
    repository.insert_glyph_records([
        GlyphRecord(glyph="铝", unicode_hex="U+94DD", basic_definition="CJK UNIFIED IDEOGRAPH-94DD", source_value="CJK UNIFIED IDEOGRAPH-94DD")
    ], source_id=source_id)
    return repository


def test_get_glyph_returns_record(tmp_path):
    client = TestClient(create_app(seeded_repository(tmp_path)))

    response = client.get("/api/v1/glyph", params={"char": "铝"})

    assert response.status_code == 200
    assert response.json()["unicode"]["hex"] == "U+94DD"
    assert response.json()["properties"][0]["confidence"] == 1.0


def test_get_glyph_rejects_empty_input(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    client = TestClient(create_app(repository))

    response = client.get("/api/v1/glyph", params={"char": ""})

    assert response.status_code == 400


def test_get_glyph_returns_404_for_missing_record(tmp_path):
    repository = GlyphRepository(tmp_path / "test.sqlite3")
    repository.initialize()
    client = TestClient(create_app(repository))

    response = client.get("/api/v1/glyph", params={"char": "水"})

    assert response.status_code == 404
```

- [ ] **Step 2: Run failing tests**

Run: `pytest tests/test_api.py -v`

Expected: FAIL because `omniglyph.api` does not exist.

- [ ] **Step 3: Implement API**

```python
from fastapi import FastAPI, HTTPException, Query

from omniglyph.config import settings
from omniglyph.repository import GlyphRepository


def create_app(repository: GlyphRepository | None = None) -> FastAPI:
    app = FastAPI(title="OmniGlyph API", version="0.1.0")
    glyph_repository = repository or GlyphRepository(settings.sqlite_path)

    @app.get("/api/v1/glyph")
    def get_glyph(char: str = Query(..., min_length=1)) -> dict:
        if len(char) != 1:
            raise HTTPException(status_code=400, detail="char must contain exactly one Unicode character")
        record = glyph_repository.find_by_glyph(char)
        if record is None:
            raise HTTPException(status_code=404, detail="glyph not found")
        return record

    return app


app = create_app()
```

- [ ] **Step 4: Run passing tests**

Run: `pytest tests/test_api.py -v`

Expected: PASS.

## Task 6: CLI Ingestion With Explicit Source Selection

**Files:**
- Create: `src/omniglyph/cli.py`

- [ ] **Step 1: Implement CLI**

```python
import argparse
from pathlib import Path

from omniglyph.config import settings
from omniglyph.normalizer import parse_unicode_data
from omniglyph.repository import GlyphRepository, SourceSnapshot
from omniglyph.sources import download_source, register_local_source

UNICODE_LICENSE = "Unicode Terms of Use"


def download_unicode() -> Path:
    artifact = download_source(
        settings.unicode_data_url,
        settings.raw_dir / "UnicodeData.txt",
        source_version="latest",
        license=UNICODE_LICENSE,
    )
    print(f"Downloaded {artifact.path} sha256={artifact.sha256}")
    return artifact.path


def ingest_unicode(source_path: Path, source_version: str = "local") -> int:
    artifact = register_local_source(
        source_path,
        source_url=source_path.as_uri() if source_path.is_absolute() else f"file://{source_path}",
        source_version=source_version,
        license=UNICODE_LICENSE,
    )
    records = list(parse_unicode_data(source_path))
    repository = GlyphRepository(settings.sqlite_path)
    repository.initialize()
    source_id = repository.add_source_snapshot(
        SourceSnapshot(
            source_name="Unicode Character Database",
            source_url=artifact.source_url,
            source_version=artifact.source_version,
            sha256=artifact.sha256,
            license=artifact.license,
            local_path=str(artifact.path),
        )
    )
    repository.insert_glyph_records(records, source_id=source_id)
    return len(records)


def main() -> None:
    parser = argparse.ArgumentParser(prog="omniglyph")
    subcommands = parser.add_subparsers(dest="command", required=True)

    subcommands.add_parser("download-unicode")

    ingest = subcommands.add_parser("ingest-unicode")
    ingest.add_argument("--source", type=Path, required=True)
    ingest.add_argument("--source-version", default="local")

    args = parser.parse_args()
    if args.command == "download-unicode":
        download_unicode()
    elif args.command == "ingest-unicode":
        count = ingest_unicode(args.source, args.source_version)
        print(f"Ingested {count} glyph records")
```

- [ ] **Step 2: Run fixture ingestion**

Run: `python -m omniglyph.cli ingest-unicode --source tests/fixtures/UnicodeData.sample.txt --source-version fixture --source-version fixture`

Expected: prints `Ingested 5 glyph records`.

- [ ] **Step 3: Verify download is explicit**

Run: `python -m omniglyph.cli download-unicode`

Expected: downloads `data/raw/UnicodeData.txt` and prints its SHA-256. Do not run this in CI unless network access is explicitly enabled.

## Task 7: End-to-End Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Run full test suite**

Run: `pytest -v`

Expected: all tests PASS.

- [ ] **Step 2: Run local API smoke test**

Run: `uvicorn omniglyph.api:app --reload`

Expected: server starts and exposes OpenAPI docs at `/docs`.

- [ ] **Step 3: Document MVP commands**

Append to `README.md`:

````markdown
## Local MVP Commands

Install development dependencies:

```bash
python -m pip install -e '.[dev]'
```

Ingest the Unicode source fixture explicitly:

```bash
python -m omniglyph.cli ingest-unicode --source tests/fixtures/UnicodeData.sample.txt --source-version fixture
```

Run the API:

```bash
uvicorn omniglyph.api:app --reload
```

Query one glyph:

```bash
curl 'http://127.0.0.1:8000/api/v1/glyph?char=铝'
```
````


## Task 8: Engineering Infrastructure

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.github/workflows/test.yml`
- Create: `LICENSE`
- Create: `NOTICE.md`
- Create: `CHANGELOG.md`
- Create: `migrations/0001_initial_sqlite.sql`

- [ ] **Step 1: Add Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -e .
EXPOSE 8000
CMD ["uvicorn", "omniglyph.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Add docker-compose file**

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
```

- [ ] **Step 3: Add GitHub Actions test workflow**

```yaml
name: tests

on:
  push:
  pull_request:

jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install -e '.[dev]'
      - run: pytest -v
```

- [ ] **Step 4: Add license and notices**

Create `LICENSE` with the chosen project code license before public release. Create `NOTICE.md` with this minimum content:

```markdown
# Notices

OmniGlyph source code license is defined in `LICENSE`.

Data source terms are tracked separately from source code licensing. Initial source classes include Unicode Character Database, Unihan, CLDR, approved open dictionaries, and private domain packs. Each imported source snapshot must store source URL, version, retrieval timestamp, checksum, and license note.
```

- [ ] **Step 5: Add changelog**

```markdown
# Changelog

## 0.1.0 - Unreleased

- Add Stage 1 Symbol Fact Base skeleton.
- Add Unicode source snapshot and glyph property ingestion.
- Add read-only `/api/v1/glyph` endpoint.
```

- [ ] **Step 6: Add initial migration mirror**

Copy the SQL schema from `GlyphRepository.initialize()` into `migrations/0001_initial_sqlite.sql` so SQLite schema changes become reviewable.

## Task 9: Benchmark Script

**Files:**
- Create: `scripts/benchmark_lookup.py`

- [ ] **Step 1: Implement lookup benchmark**

```python
import argparse
import statistics
import time

from omniglyph.repository import GlyphRepository


def benchmark(sqlite_path: str, glyph: str, iterations: int) -> dict:
    repository = GlyphRepository(sqlite_path)
    durations = []
    for _ in range(iterations):
        start = time.perf_counter()
        repository.find_by_glyph(glyph)
        durations.append((time.perf_counter() - start) * 1000)
    return {
        "iterations": iterations,
        "p50_ms": statistics.median(durations),
        "p95_ms": statistics.quantiles(durations, n=20)[18],
        "max_ms": max(durations),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/omniglyph.sqlite3")
    parser.add_argument("--glyph", default="铝")
    parser.add_argument("--iterations", type=int, default=1000)
    args = parser.parse_args()
    print(benchmark(args.db, args.glyph, args.iterations))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run benchmark after ingestion**

Run: `python scripts/benchmark_lookup.py --db data/omniglyph.sqlite3 --glyph 铝 --iterations 1000`

Expected: prints p50, p95, and max latency numbers. Do not claim P95 targets without this output.

## Self-Review

- Spec coverage: Stage 1 ingestion, normalization, source snapshots, read-only API, traceability, NULL discipline, append-only extensible properties, explicit downloads, CI/Docker/license placeholders, benchmark script, and no-generative-data rules are covered.
- Intentional exclusions: Stage 2 graph topology and Stage 3 semantic computation are documented but not implemented in the MVP.
- Placeholder scan: No implementation step depends on unspecified functions or TBD behavior.
- Type consistency: `GlyphRecord`, `GlyphRepository`, and API response fields use the same names across tasks.
