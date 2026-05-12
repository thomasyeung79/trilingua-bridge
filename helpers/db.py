import os
import sqlite3
import time
from typing import Any, Dict, List, Optional

DB_PATH = os.getenv("DB_PATH", "trilingua_v2.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    mode TEXT NOT NULL,
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

CREATE INDEX IF NOT EXISTS idx_history_user_ts ON history (username, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_history_mode ON history (mode);
CREATE INDEX IF NOT EXISTS idx_history_langs ON history (source_lang, target_lang);
CREATE INDEX IF NOT EXISTS idx_history_persona ON history (persona);
"""

def _connect() -> sqlite3.Connection:
    # Create directory if needed
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db() -> None:
    with _connect() as con:
        cur = con.cursor()
        for stmt in SCHEMA_SQL.strip().split(";"):
            s = stmt.strip()
            if s:
                cur.execute(s)
        con.commit()

def insert_history(
    username: str,
    mode: str,
    source_lang: Optional[str],
    target_lang: Optional[str],
    native_lang: Optional[str],
    persona: Optional[str],
    ui_lang: Optional[str],
    user_input: Optional[str],
    ai_output: Optional[str],
    tokens_input: Optional[int],
    tokens_output: Optional[int],
    model: Optional[str],
    latency_ms: Optional[int],
) -> None:
    ts = int(time.time() * 1000)
    with _connect() as con:
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO history (
                username, timestamp, mode, source_lang, target_lang, native_lang,
                persona, ui_lang, user_input, ai_output, tokens_input, tokens_output,
                model, latency_ms
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                username or "",
                ts,
                mode or "",
                source_lang or "",
                target_lang or "",
                native_lang or "",
                persona or "",
                ui_lang or "",
                user_input or "",
                ai_output or "",
                int(tokens_input) if tokens_input is not None else None,
                int(tokens_output) if tokens_output is not None else None,
                model or "",
                int(latency_ms) if latency_ms is not None else None,
            ),
        )
        con.commit()

def fetch_history(
    username: str,
    limit: int = 50,
    mode: Optional[str] = None,
    source_lang: Optional[str] = None,
    target_lang: Optional[str] = None,
    persona: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if not username:
        return []

    where = ["username = ?"]
    params: List[Any] = [username]

    if mode:
        where.append("mode = ?")
        params.append(mode)
    if source_lang:
        where.append("source_lang = ?")
        params.append(source_lang)
    if target_lang:
        where.append("target_lang = ?")
        params.append(target_lang)
    if persona:
        where.append("persona = ?")
        params.append(persona)
    if search:
        where.append("(user_input LIKE ? OR ai_output LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like])

    where_sql = " AND ".join(where) if where else "1=1"
    sql = f"""
        SELECT id, username, timestamp, mode, source_lang, target_lang, native_lang,
               persona, ui_lang, user_input, ai_output, tokens_input, tokens_output,
               model, latency_ms
        FROM history
        WHERE {where_sql}
        ORDER BY timestamp DESC
        LIMIT ?
    """
    params.append(int(limit))

    rows: List[Dict[str, Any]] = []
    with _connect() as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute(sql, params)
        for r in cur.fetchall():
            rows.append({k: r[k] for k in r.keys()})
    return rows
