import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def get_conn(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: Path):
    conn = get_conn(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS captures (
            id          TEXT PRIMARY KEY,
            created_at  TEXT NOT NULL,
            image_path  TEXT NOT NULL,
            context_image_path TEXT,
            selection_geometry TEXT,
            status      TEXT NOT NULL DEFAULT 'pending',
            ocr_text    TEXT,
            ocr_engine  TEXT,
            processed_at TEXT,
            error       TEXT,
            retry_count INTEGER NOT NULL DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_captures_status ON captures(status);
        CREATE INDEX IF NOT EXISTS idx_captures_created ON captures(created_at);
    """)
    conn.commit()
    conn.close()


def insert_capture(conn, image_path: str, context_image_path: str = None, geometry: str = None) -> str:
    capture_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    conn.execute(
        """INSERT INTO captures (id, created_at, image_path, context_image_path, selection_geometry, status)
           VALUES (?, ?, ?, ?, ?, 'pending')""",
        (capture_id, now, image_path, context_image_path, geometry),
    )
    conn.commit()
    return capture_id


def mark_processed(conn, capture_id: str, ocr_text: str, ocr_engine: str):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    conn.execute(
        """UPDATE captures SET status='processed', ocr_text=?, ocr_engine=?, processed_at=? WHERE id=?""",
        (ocr_text, ocr_engine, now, capture_id),
    )
    conn.commit()


def mark_failed(conn, capture_id: str, error: str):
    conn.execute(
        """UPDATE captures SET status='failed', error=?, retry_count=retry_count+1 WHERE id=?""",
        (error, capture_id),
    )
    conn.commit()


def mark_pending(conn, capture_id: str):
    conn.execute(
        """UPDATE captures SET status='pending', ocr_text=NULL, processed_at=NULL, error=NULL WHERE id=?""",
        (capture_id,),
    )
    conn.commit()


def get_capture(conn, capture_id: str):
    row = conn.execute("SELECT * FROM captures WHERE id=?", (capture_id,)).fetchone()
    return dict(row) if row else None


def get_pending_captures(conn):
    rows = conn.execute(
        "SELECT * FROM captures WHERE status='pending' ORDER BY created_at ASC"
    ).fetchall()
    return [dict(r) for r in rows]


def get_failed_captures(conn):
    rows = conn.execute("SELECT id, created_at, error FROM captures WHERE status='failed' ORDER BY created_at ASC").fetchall()
    return [dict(r) for r in rows]


def list_captures(conn, limit: int = 50, offset: int = 0):
    rows = conn.execute(
        "SELECT id, created_at, status, ocr_text, error FROM captures ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    return [dict(r) for r in rows]


def get_stats(conn):
    row = conn.execute("""
        SELECT
            COUNT(*) AS total,
            COALESCE(SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END), 0) AS pending,
            COALESCE(SUM(CASE WHEN status='processed' THEN 1 ELSE 0 END), 0) AS processed,
            COALESCE(SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END), 0) AS failed
        FROM captures
    """).fetchone()
    return dict(row)
