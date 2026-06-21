-- Engram schema v1

CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    description TEXT
);

-- Append-only event log
CREATE TABLE IF NOT EXISTS events (
    id          TEXT PRIMARY KEY,  -- ULID
    event_type  TEXT NOT NULL,
    source      TEXT NOT NULL,
    source_id   TEXT,
    timestamp   TEXT NOT NULL,     -- ISO 8601
    ingested_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    payload     TEXT NOT NULL,     -- JSON
    project     TEXT,
    actor       TEXT,
    checksum    TEXT NOT NULL,     -- SHA-256 for dedup
    processed   INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_events_type        ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_source       ON events(source, source_id);
CREATE INDEX IF NOT EXISTS idx_events_timestamp    ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_project      ON events(project);
CREATE INDEX IF NOT EXISTS idx_events_unprocessed  ON events(processed) WHERE processed = 0;
CREATE UNIQUE INDEX IF NOT EXISTS idx_events_checksum ON events(checksum);

-- Knowledge graph nodes
CREATE TABLE IF NOT EXISTS entities (
    id              TEXT PRIMARY KEY,  -- ULID
    entity_type     TEXT NOT NULL,
    title           TEXT NOT NULL,
    content         TEXT,
    properties      TEXT NOT NULL DEFAULT '{}',  -- JSON
    project         TEXT,
    status          TEXT NOT NULL DEFAULT 'active',
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    importance      REAL NOT NULL DEFAULT 0.5,
    access_count    INTEGER NOT NULL DEFAULT 0,
    last_accessed   TEXT,
    decay_factor    REAL NOT NULL DEFAULT 1.0,
    source_event_id TEXT REFERENCES events(id),
    created_by      TEXT,
    confidence      REAL NOT NULL DEFAULT 1.0
);

CREATE INDEX IF NOT EXISTS idx_entities_type       ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_project    ON entities(project);
CREATE INDEX IF NOT EXISTS idx_entities_status     ON entities(status);
CREATE INDEX IF NOT EXISTS idx_entities_importance ON entities(importance DESC);
CREATE INDEX IF NOT EXISTS idx_entities_type_proj  ON entities(entity_type, project);

-- Knowledge graph edges
CREATE TABLE IF NOT EXISTS relationships (
    id              TEXT PRIMARY KEY,
    source_id       TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    target_id       TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    relation_type   TEXT NOT NULL,
    properties      TEXT NOT NULL DEFAULT '{}',  -- JSON
    weight          REAL NOT NULL DEFAULT 1.0,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    source_event_id TEXT REFERENCES events(id),
    UNIQUE(source_id, target_id, relation_type)
);

CREATE INDEX IF NOT EXISTS idx_rel_source      ON relationships(source_id);
CREATE INDEX IF NOT EXISTS idx_rel_target      ON relationships(target_id);
CREATE INDEX IF NOT EXISTS idx_rel_type        ON relationships(relation_type);
CREATE INDEX IF NOT EXISTS idx_rel_source_type ON relationships(source_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_rel_target_type ON relationships(target_id, relation_type);

-- Audit trail
CREATE TABLE IF NOT EXISTS provenance (
    id                TEXT PRIMARY KEY,
    entity_id         TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    action            TEXT NOT NULL,
    actor             TEXT NOT NULL,
    timestamp         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    source_event_id   TEXT REFERENCES events(id),
    related_entity_id TEXT REFERENCES entities(id),
    details           TEXT NOT NULL DEFAULT '{}',  -- JSON
    confidence_delta  REAL NOT NULL DEFAULT 0.0
);

CREATE INDEX IF NOT EXISTS idx_prov_entity    ON provenance(entity_id);
CREATE INDEX IF NOT EXISTS idx_prov_action    ON provenance(action);
CREATE INDEX IF NOT EXISTS idx_prov_timestamp ON provenance(timestamp);
CREATE INDEX IF NOT EXISTS idx_prov_related   ON provenance(related_entity_id);

-- Point-in-time entity snapshots
CREATE TABLE IF NOT EXISTS entity_snapshots (
    id            TEXT PRIMARY KEY,
    entity_id     TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    snapshot_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    title         TEXT,
    content       TEXT,
    properties    TEXT,
    status        TEXT,
    importance    REAL,
    confidence    REAL,
    provenance_id TEXT REFERENCES provenance(id)
);

CREATE INDEX IF NOT EXISTS idx_snap_entity ON entity_snapshots(entity_id, snapshot_at);

-- Entity tags
CREATE TABLE IF NOT EXISTS tags (
    entity_id  TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    tag        TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (entity_id, tag)
);

CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);

-- Entity-to-file associations
CREATE TABLE IF NOT EXISTS entity_files (
    entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    action    TEXT NOT NULL DEFAULT 'related',
    PRIMARY KEY (entity_id, file_path)
);

CREATE INDEX IF NOT EXISTS idx_ef_path ON entity_files(file_path);

-- Key-value config store
CREATE TABLE IF NOT EXISTS config (
    key        TEXT PRIMARY KEY,
    value      TEXT,
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- Full-text search (content-sync mode)
CREATE VIRTUAL TABLE IF NOT EXISTS entities_fts USING fts5(
    title,
    content,
    entity_type,
    project,
    content='entities',
    content_rowid='rowid'
);

-- Keep FTS index in sync with entities table
CREATE TRIGGER IF NOT EXISTS entities_ai AFTER INSERT ON entities BEGIN
    INSERT INTO entities_fts(rowid, title, content, entity_type, project)
    VALUES (NEW.rowid, NEW.title, NEW.content, NEW.entity_type, NEW.project);
END;

CREATE TRIGGER IF NOT EXISTS entities_ad AFTER DELETE ON entities BEGIN
    INSERT INTO entities_fts(entities_fts, rowid, title, content, entity_type, project)
    VALUES ('delete', OLD.rowid, OLD.title, OLD.content, OLD.entity_type, OLD.project);
END;

CREATE TRIGGER IF NOT EXISTS entities_au AFTER UPDATE ON entities BEGIN
    INSERT INTO entities_fts(entities_fts, rowid, title, content, entity_type, project)
    VALUES ('delete', OLD.rowid, OLD.title, OLD.content, OLD.entity_type, OLD.project);
    INSERT INTO entities_fts(rowid, title, content, entity_type, project)
    VALUES (NEW.rowid, NEW.title, NEW.content, NEW.entity_type, NEW.project);
END;
