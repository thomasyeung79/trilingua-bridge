import os
import sqlite3
import time
from typing import Optional, List, Dict, Any


def get_db_path() -> str:
    """
    Priority:
    1. Streamlit secrets DB_PATH
    2. Environment variable DB_PATH
    3. Environment variable TRILINGUA_DB_PATH
    4. Default local database
    """

    try:
        import streamlit as st

        db_path = st.secrets.get("DB_PATH")
        if db_path:
            return db_path
    except Exception:
        pass

    return (
        os.environ.get("DB_PATH")
        or os.environ.get("TRILINGUA_DB_PATH")
        or "trilingua_bridge.db"
    )


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    folder = os.path.dirname(db_path)

    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            timestamp REAL NOT NULL,
            mode TEXT,
            source_lang TEXT,
            target_lang TEXT,
            native_lang TEXT,
            persona TEXT,
            ui_lang TEXT,
            user_input TEXT,
            ai_output TEXT,
            tokens_input INTEGER,
            tokens_output INTEGER,
            model TEXT,
            latency_ms INTEGER
        );
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_history_user_time
        ON history(username, timestamp DESC);
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_history_mode
        ON history(mode);
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_history_langs
        ON history(source_lang, target_lang);
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
    ui_lang: Optional[str],
    user_input: str,
    ai_output: str,
    tokens_input: Optional[int],
    tokens_output: Optional[int],
    model: Optional[str],
    latency_ms: Optional[int],
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO history (
            username,
            timestamp,
            mode,
            source_lang,
            target_lang,
            native_lang,
            persona,
            ui_lang,
            user_input,
            ai_output,
            tokens_input,
            tokens_output,
            model,
            latency_ms
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            username or "guest",
            time.time(),
            mode or "",
            source_lang or "",
            target_lang or "",
            native_lang or "",
            persona or "",
            ui_lang or "",
            user_input or "",
            ai_output or "",
            tokens_input,
            tokens_output,
            model or "",
            latency_ms,
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
    query = """
        SELECT
            id,
            username,
            timestamp,
            mode,
            source_lang,
            target_lang,
            native_lang,
            persona,
            ui_lang,
            user_input,
            ai_output,
            tokens_input,
            tokens_output,
            model,
            latency_ms
        FROM history
        WHERE username = ?
    """

    params: List[Any] = [username or "guest"]

    if mode:
        query += " AND mode = ?"
        params.append(mode)

    if source_lang:
        query += " AND source_lang = ?"
        params.append(source_lang)

    if target_lang:
        query += " AND target_lang = ?"
        params.append(target_lang)

    if persona:
        query += " AND persona = ?"
        params.append(persona)

    if search:
        query += " AND (user_input LIKE ? OR ai_output LIKE ?)"
        like_value = f"%{search}%"
        params.extend([like_value, like_value])

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)

    rows = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return rows
