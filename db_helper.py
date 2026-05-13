import os
import sqlite3
import time
from typing import Optional, List, Dict, Any


DB_PATH = os.environ.get("DB_PATH") or "trilingua_bridge.db"


def get_db_path() -> str:
    try:
        import streamlit as st

        db_path = st.secrets.get("DB_PATH")
        if db_path:
            return db_path
    except Exception:
        pass

    return DB_PATH


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    folder = os.path.dirname(db_path)

    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

    return sqlite3.connect(db_path, check_same_thread=False)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
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
            latency_ms INTEGER,
            timestamp INTEGER NOT NULL
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
    ui_lang: str,
    user_input: str,
    ai_output: str,
    tokens_input: Optional[int],
    tokens_output: Optional[int],
    model: Optional[str],
    latency_ms: Optional[int],
):
    timestamp = int(time.time() * 1000)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
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
            tokens_input,
            tokens_output,
            model,
            latency_ms,
            timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            username or "guest",
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
            tokens_input,
            tokens_output,
            model,
            latency_ms,
            timestamp
        FROM history
        WHERE username = ?
    """

    params: List[Any] = [username]

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
    rows = cursor.execute(query, params).fetchall()
    conn.close()

    columns = [
        "id",
        "username",
        "mode",
        "source_lang",
        "target_lang",
        "native_lang",
        "persona",
        "ui_lang",
        "user_input",
        "ai_output",
        "tokens_input",
        "tokens_output",
        "model",
        "latency_ms",
        "timestamp",
    ]

    history: List[Dict[str, Any]] = []

    for row in rows:
        history.append(dict(zip(columns, row)))

    return history
