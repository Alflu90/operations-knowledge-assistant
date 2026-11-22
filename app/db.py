"""Livello SQL (SQLite): catalogo documenti/chunk e registro delle domande."""
import re
import sqlite3
from pathlib import Path

from app import config
from app.chunking import Chunk

SCHEMA = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA.read_text())


def replace_catalog(documents: list[tuple[str, int]], chunks: list[Chunk]) -> None:
    """Sostituisce il catalogo con i documenti (nome, pagine) e i chunk dati."""
    with connect() as conn:
        conn.execute("DELETE FROM documents")  # elimina a cascata anche i chunk
        ids = {}
        for filename, pages in documents:
            cur = conn.execute("INSERT INTO documents (filename, pages) VALUES (?, ?)", (filename, pages))
            ids[filename] = cur.lastrowid
        conn.executemany(
            "INSERT INTO chunks (id, document_id, page, chunk_index, text, char_count) VALUES (?, ?, ?, ?, ?, ?)",
            [(f"{c.source}:{c.page}:{c.index}", ids[c.source], c.page, c.index, c.text, len(c.text)) for c in chunks],
        )


def log_query(question: str, answer: str, answered: bool, latency_ms: int, best_distance, hits: list[dict]) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO query_log (question, answer, answered, latency_ms, best_distance) VALUES (?, ?, ?, ?, ?)",
            (question, answer, int(answered), latency_ms, best_distance),
        )
        query_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO query_sources (query_id, rank, chunk_id, distance) VALUES (?, ?, ?, ?)",
            [(query_id, i, h["chunk_id"], h["distance"]) for i, h in enumerate(hits, start=1)],
        )
    return query_id


def catalog_counts() -> dict:
    with connect() as conn:
        return {
            "documents": conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
            "chunks": conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0],
        }


def run_analytics() -> dict[str, list[dict]]:
    """Esegue le query di sql/analytics.sql e restituisce {nome: righe}."""
    
    text = (SCHEMA.parent / "analytics.sql").read_text()
    parts = re.split(r"^-- name: (.+)$", text, flags=re.MULTILINE)  # ['', nome1, sql1, nome2, sql2, ...]
    with connect() as conn:
        return {
            name: [dict(row) for row in conn.execute(sql).fetchall()]
            for name, sql in zip(parts[1::2], parts[2::2])
        }
