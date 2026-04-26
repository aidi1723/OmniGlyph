import json
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
    def __init__(self, sqlite_path: Path | str):
        self.sqlite_path = Path(sqlite_path)

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
            connection.executescript(SCHEMA_SQL)
            self._ensure_lexical_metadata_columns(connection)
            connection.executescript(INDEX_SQL)

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


    def insert_unihan_properties(self, properties, source_id: str) -> int:
        inserted = 0
        with self.connect() as connection:
            for item in properties:
                row = connection.execute("SELECT uid FROM glyph_node WHERE glyph = ?", (item.glyph,)).fetchone()
                if row is None:
                    glyph_uid = self._glyph_uid(item.unicode_hex)
                    now = datetime.now(timezone.utc).isoformat()
                    connection.execute(
                        """
                        INSERT INTO glyph_node (
                            uid, glyph, unicode_hex, unicode_version, name,
                            general_category, script, block, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(glyph) DO UPDATE SET updated_at = excluded.updated_at
                        """,
                        (glyph_uid, item.glyph, item.unicode_hex, None, None, None, None, None, now, now),
                    )
                else:
                    glyph_uid = row["uid"]
                self._insert_property_with_connection(
                    connection,
                    glyph_uid=glyph_uid,
                    namespace=item.property_namespace,
                    name=item.property_name,
                    value=item.property_value,
                    source_id=source_id,
                    confidence=1.0,
                )
                inserted += 1
        return inserted


    def insert_lexical_entries(self, entries, source_id: str, confidence: float = 1.0) -> int:
        inserted = 0
        with self.connect() as connection:
            for entry in entries:
                entry_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"omniglyph:lexical:{entry.namespace}:{entry.canonical_id}:{entry.term}:{source_id}"))
                now = datetime.now(timezone.utc).isoformat()
                connection.execute(
                    """
                    INSERT OR IGNORE INTO lexical_entry (
                        id, namespace, term, normalized_term, canonical_id, entry_type,
                        language, definition, traits, source_id, confidence, created_at
                        , sensitivity, review_status, pack_id, pack_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry_id,
                        entry.namespace,
                        entry.term,
                        self._normalize_text(entry.term),
                        entry.canonical_id,
                        entry.entry_type,
                        entry.language,
                        entry.definition,
                        json.dumps(entry.traits, ensure_ascii=False, sort_keys=True),
                        source_id,
                        confidence,
                        now,
                        entry.sensitivity,
                        entry.review_status,
                        entry.pack_id,
                        entry.pack_version,
                    ),
                )
                for alias in entry.aliases:
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO lexical_alias (
                            id, lexical_entry_id, alias, normalized_alias, source_id, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(uuid.uuid5(uuid.NAMESPACE_URL, f"omniglyph:alias:{entry_id}:{alias}:{source_id}")),
                            entry_id,
                            alias,
                            self._normalize_text(alias),
                            source_id,
                            now,
                        ),
                    )
                inserted += 1
        return inserted

    def delete_lexical_namespace(self, namespace: str) -> int:
        with self.connect() as connection:
            rows = connection.execute("SELECT id FROM lexical_entry WHERE namespace = ?", (namespace,)).fetchall()
            entry_ids = [row["id"] for row in rows]
            if not entry_ids:
                return 0
            connection.executemany("DELETE FROM lexical_alias WHERE lexical_entry_id = ?", [(entry_id,) for entry_id in entry_ids])
            connection.execute("DELETE FROM lexical_entry WHERE namespace = ?", (namespace,))
            return len(entry_ids)

    def find_term(self, text: str) -> dict | None:
        normalized = self._normalize_text(text)
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT le.*, le.term AS matched_text, ss.source_name, ss.source_version
                FROM lexical_entry le
                JOIN source_snapshot ss ON ss.id = le.source_id
                WHERE le.normalized_term = ?
                ORDER BY le.confidence DESC, le.namespace
                LIMIT 1
                """,
                (normalized,),
            ).fetchone()
            if row is None:
                row = connection.execute(
                    """
                    SELECT le.*, la.alias AS matched_text, ss.source_name, ss.source_version
                    FROM lexical_alias la
                    JOIN lexical_entry le ON le.id = la.lexical_entry_id
                    JOIN source_snapshot ss ON ss.id = le.source_id
                    WHERE la.normalized_alias = ?
                    ORDER BY le.confidence DESC, le.namespace
                    LIMIT 1
                    """,
                    (normalized,),
                ).fetchone()
            if row is None:
                return None
            return self._lexical_row_to_dict(row)

    def list_secret_terms(self) -> list[str]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT term AS value FROM lexical_entry
                WHERE sensitivity = 'secret' AND review_status = 'approved'
                UNION
                SELECT la.alias AS value
                FROM lexical_alias la
                JOIN lexical_entry le ON le.id = la.lexical_entry_id
                WHERE le.sensitivity = 'secret' AND le.review_status = 'approved'
                ORDER BY value
                """
            ).fetchall()
            return [row["value"] for row in rows]

    def _lexical_row_to_dict(self, row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "namespace": row["namespace"],
            "term": row["term"],
            "matched_text": row["matched_text"],
            "canonical_id": row["canonical_id"],
            "entry_type": row["entry_type"],
            "language": row["language"],
            "definition": row["definition"],
            "traits": json.loads(row["traits"]),
            "confidence": row["confidence"],
            "source_id": row["source_id"],
            "source_name": row["source_name"],
            "source_version": row["source_version"],
            "sensitivity": row["sensitivity"],
            "review_status": row["review_status"],
            "pack_id": row["pack_id"],
            "pack_version": row["pack_version"],
        }

    def _normalize_text(self, text: str) -> str:
        return " ".join(text.casefold().strip().split())

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
            property_items = [
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
            ]
            return {
                "uid": row["uid"],
                "glyph": row["glyph"],
                "unicode": {"hex": row["unicode_hex"], "name": row["name"], "block": row["block"]},
                "lexical": self._shape_lexical(property_items),
                "domain_traits": self._shape_domain_traits(property_items),
                "properties": property_items,
                "sources": [dict(source) for source in sources],
            }


    def _shape_lexical(self, properties: list[dict]) -> dict:
        lexical = {"pinyin": None, "basic_meaning": None, "sources": {}}
        for item in properties:
            if item["namespace"] != "unihan":
                continue
            if item["name"] == "kMandarin" and lexical["pinyin"] is None:
                lexical["pinyin"] = item["value"]
                lexical["sources"]["pinyin"] = item["source_name"]
            elif item["name"] == "kDefinition" and lexical["basic_meaning"] is None:
                lexical["basic_meaning"] = item["value"]
                lexical["sources"]["basic_meaning"] = item["source_name"]
        return lexical

    def _shape_domain_traits(self, properties: list[dict]) -> dict:
        traits: dict[str, str] = {}
        for item in properties:
            namespace = item["namespace"]
            if not namespace.startswith("private_"):
                continue
            traits[item["name"]] = item["value"]
        return traits

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

    def _ensure_lexical_metadata_columns(self, connection: sqlite3.Connection) -> None:
        existing = {row["name"] for row in connection.execute("PRAGMA table_info(lexical_entry)").fetchall()}
        columns = {
            "sensitivity": "TEXT NOT NULL DEFAULT 'normal'",
            "review_status": "TEXT NOT NULL DEFAULT 'approved'",
            "pack_id": "TEXT",
            "pack_version": "TEXT",
        }
        for name, definition in columns.items():
            if name not in existing:
                connection.execute(f"ALTER TABLE lexical_entry ADD COLUMN {name} {definition}")


SCHEMA_SQL = """
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

CREATE TABLE IF NOT EXISTS lexical_entry (
    id TEXT PRIMARY KEY,
    namespace TEXT NOT NULL,
    term TEXT NOT NULL,
    normalized_term TEXT NOT NULL,
    canonical_id TEXT NOT NULL,
    entry_type TEXT NOT NULL,
    language TEXT NOT NULL,
    definition TEXT,
    traits TEXT NOT NULL,
    sensitivity TEXT NOT NULL DEFAULT 'normal',
    review_status TEXT NOT NULL DEFAULT 'approved',
    pack_id TEXT,
    pack_version TEXT,
    source_id TEXT NOT NULL,
    confidence REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES source_snapshot(id),
    UNIQUE(namespace, normalized_term, canonical_id, source_id)
);

CREATE TABLE IF NOT EXISTS lexical_alias (
    id TEXT PRIMARY KEY,
    lexical_entry_id TEXT NOT NULL,
    alias TEXT NOT NULL,
    normalized_alias TEXT NOT NULL,
    source_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (lexical_entry_id) REFERENCES lexical_entry(id),
    FOREIGN KEY (source_id) REFERENCES source_snapshot(id),
    UNIQUE(lexical_entry_id, normalized_alias, source_id)
);
"""


INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_glyph_property_glyph_uid
ON glyph_property(glyph_uid);

CREATE INDEX IF NOT EXISTS idx_lexical_entry_normalized_term
ON lexical_entry(normalized_term);

CREATE INDEX IF NOT EXISTS idx_lexical_alias_normalized_alias
ON lexical_alias(normalized_alias);
"""
