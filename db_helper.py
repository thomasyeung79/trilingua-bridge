import os
import sqlite3
import time
from typing import Optional, List, Dict, Any


DB_PATH = os.environ.get("DB_PATH") or "trilingua.db"


def _db_path() -> str:
    """
    Get database path.
    Priority:
    1. Streamlit secrets
    2. Environment variable
    3. Default local database
    """
    try:
        import streamlit as st

        db_path = st.secrets.get("DB_PATH")
        if db_path:
            return db_path

    except Exception:
        pass

    return DB_PATH


def _get_conn() -> sqlite3.Connection:
    db_path = _db_path()
    folder = os.path.dirname(db_path)

    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

    return sqlite3.connect(db_path, check_same_thread=False)


def init_db():
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            mode TEXT NOT NULL,
            source_lang TEXT,
            target_lang TEXT,
            native_lang TEXT,
            persona TEXT,
            ui_lang TEXT,
            user_input TEXT,
            ai_output TEXT,
            model TEXT,
            tokens_input INTEGER,
            tokens_output INTEGER,
            latency_ms INTEGER,
            timestamp INTEGER NOT NULL
        );
        """
    )

    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_history_username_timestamp
        ON history (username, timestamp DESC);
        """
    )

    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_history_mode
        ON history (mode);
        """
    )

    conn.commit()
    conn.close()


def insert_history(
    username: str,
    mode: str,
    source_lang: Optional[str],
    target_lang: Optional[str],
    native_lang: Optional[str],
    persona: Optional[str],
    ui_lang: str,
    user_input: str,
    ai_output: str,
    tokens_input: Optional[int],
    tokens_output: Optional[int],
    model: Optional[str],
    latency_ms: int,
):
    timestamp = int(time.time() * 1000)

    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO history (
            username,
            mode,
            source_lang,
            target_lang,
            native_lang,
            persona,
            ui_lang,
            user_input,
            ai_output,
            model,
            tokens_input,
            tokens_output,
            latency_ms,
            timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            username,
            mode,
            source_lang,
            target_lang,
            native_lang,
            persona,
            ui_lang,
            user_input,
            ai_output,
            model,
            tokens_input,
            tokens_output,
            latency_ms,
            timestamp,
        ),
    )

    conn.commit()
    conn.close()


def fetch_history(
    username: str,
    limit: int = 50,
    mode: Optional[str] = None,
    source_lang: Optional[str] = None,
    target_lang: Optional[str] = None,
    persona: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    conn = _get_conn()
    cur = conn.cursor()

    query = """
        SELECT
            id,
            username,
            mode,
            source_lang,
            target_lang,
            native_lang,
            persona,
            ui_lang,
            user_input,
            ai_output,
            model,
            tokens_input,
            tokens_output,
            latency_ms,
            timestamp
        FROM history
        WHERE username = ?
    """

    args: List[Any] = [username]

    if mode:
        query += " AND mode = ?"
        args.append(mode)

    if source_lang:
        query += " AND source_lang = ?"
        args.append(source_lang)

    if target_lang:
        query += " AND target_lang = ?"
        args.append(target_lang)

    if persona:
        query += " AND persona = ?"
        args.append(persona)

    if search:
        query += " AND (user_input LIKE ? OR ai_output LIKE ?)"
        like_value = f"%{search}%"
        args.extend([like_value, like_value])

    query += " ORDER BY timestamp DESC LIMIT ?"
    args.append(limit)

    cur.execute(query, args)
    rows = cur.fetchall()
    conn.close()

    history = []

    for row in rows:
        history.append(
            {
                "id": row[0],
                "username": row[1],
                "mode": row[2],
                "source_lang": row[3],
                "target_lang": row[4],
                "native_lang": row[5],
                "persona": row[6],
                "ui_lang": row[7],
                "user_input": row[8],
                "ai_output": row[9],
                "model": row[10],
                "tokens_input": row[11],
                "tokens_output": row[12],
                "latency_ms": row[13],
                "timestamp": row[14],
            }
        )

    return history
