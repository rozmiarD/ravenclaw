from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Tuple

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "logs.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    tor TEXT NOT NULL,
    agent TEXT DEFAULT '',
    decision TEXT NOT NULL,
    status TEXT NOT NULL,
    result TEXT NOT NULL,
    row_type TEXT NOT NULL DEFAULT 'entry',
    highlight INTEGER NOT NULL DEFAULT 0
);
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    with conn:
        conn.executescript(SCHEMA)
        migrate_schema(conn)
    conn.close()


def migrate_schema(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(logs)")}
    if "tor" not in cols or "agent" not in cols:
        conn.execute("ALTER TABLE logs RENAME TO logs_old")
        conn.executescript(SCHEMA)
        conn.execute(
            """
            INSERT INTO logs (id, timestamp, tor, agent, decision, status, result, row_type, highlight)
            SELECT id, timestamp, agent, '' AS agent, decision, status, result, 'entry', 0 FROM logs_old
            """
        )
        conn.execute("DROP TABLE logs_old")
        cols = {row[1] for row in conn.execute("PRAGMA table_info(logs)")}

    if "row_type" not in cols:
        conn.execute("ALTER TABLE logs ADD COLUMN row_type TEXT NOT NULL DEFAULT 'entry'")
    if "highlight" not in cols:
        conn.execute("ALTER TABLE logs ADD COLUMN highlight INTEGER NOT NULL DEFAULT 0")


def insert_log(
    timestamp: str,
    tor: str,
    decision: str,
    status: str,
    result: str,
    agent: str = "",
    row_type: str = "entry",
    highlight: bool = False,
) -> None:
    conn = get_conn()
    with conn:
        conn.execute(
            """
            INSERT INTO logs (timestamp, tor, agent, decision, status, result, row_type, highlight)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (timestamp, tor, agent, decision, status, result, row_type, 1 if highlight else 0),
        )
    conn.close()


def fetch_logs(page: int = 1, per_page: int = 25) -> Tuple[Iterable[sqlite3.Row], int]:
    conn = get_conn()
    offset = (page - 1) * per_page
    rows = conn.execute(
        "SELECT * FROM logs ORDER BY id DESC LIMIT ? OFFSET ?",
        (per_page, offset),
    ).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
    conn.close()
    return rows, total


def clear_logs() -> int:
    conn = get_conn()
    with conn:
        deleted = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
        conn.execute("DELETE FROM logs")
        conn.execute("DELETE FROM sqlite_sequence WHERE name='logs'")
    conn.close()
    return int(deleted)
