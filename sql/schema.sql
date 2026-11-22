CREATE TABLE IF NOT EXISTS documents (
    id          INTEGER PRIMARY KEY,
    filename    TEXT NOT NULL UNIQUE,
    pages       INTEGER NOT NULL,
    indexed_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chunks (
    id           TEXT PRIMARY KEY,   -- stesso id usato in ChromaDB
    document_id  INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page         INTEGER NOT NULL,
    chunk_index  INTEGER NOT NULL,
    text         TEXT NOT NULL,
    char_count   INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS query_log (
    id             INTEGER PRIMARY KEY,
    asked_at       TEXT NOT NULL DEFAULT (datetime('now')),
    question       TEXT NOT NULL,
    answer         TEXT NOT NULL,
    answered       INTEGER NOT NULL,   -- 1 = ha risposto, 0 = "non trovo questa informazione"
    latency_ms     INTEGER NOT NULL,
    best_distance  REAL
);

-- chunk_id senza chiave esterna: ri-indicizzare i documenti non deve cancellare lo storico
CREATE TABLE IF NOT EXISTS query_sources (
    query_id  INTEGER NOT NULL REFERENCES query_log(id) ON DELETE CASCADE,
    rank      INTEGER NOT NULL,
    chunk_id  TEXT NOT NULL,
    distance  REAL NOT NULL,
    PRIMARY KEY (query_id, rank)
);
