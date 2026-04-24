
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
