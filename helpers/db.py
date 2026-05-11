import os
import json
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any

DB_PATH = os.getenv("DB_PATH", "trilingua.db")

_conn = None

def _get_conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
    return _conn

def _column_exists(conn, table: str, col: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info({table});")
    return any(row[1] == col for row in cur.fetchall())

def _ensure_indexes(conn):
    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_history_username ON history(username);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_history_feature ON history(feature);")
    except Exception:
        pass

def init_db():
    conn = _get_conn()
    # Base table (add username, native_lang, ui_lang columns for isolation and context)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            username TEXT,
            feature TEXT NOT NULL,
            source_lang TEXT,
            target_lang TEXT,
            native_lang TEXT,
            ui_lang TEXT,
            user_input TEXT,
            ai_output TEXT,
            extra TEXT,
            tokens_input INTEGER,
            tokens_output INTEGER,
            model TEXT,
            latency_ms INTEGER
        );
    """)
    # Migrations for older DBs
    for col in ("username", "native_lang", "ui_lang"):
        if not _column_exists(conn, "history", col):
            try:
                conn.execute(f"ALTER TABLE history ADD COLUMN {col} TEXT;")
            except Exception:
                pass
    _ensure_indexes(conn)
    conn.commit()

def insert_history(
    username: str,
    feature: str,
    source_lang: str,
    target_lang: str,
    user_input: str,
    ai_output: str,
    native_lang: Optional[str] = None,
    ui_lang: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
    tokens_input: Optional[int] = None,
    tokens_output: Optional[int] = None,
    model: Optional[str] = None,
    latency_ms: Optional[int] = None
):
    conn = _get_conn()
    ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    conn.execute("""
        INSERT INTO history (
            timestamp, username, feature, source_lang, target_lang,
            native_lang, ui_lang, user_input, ai_output, extra,
            tokens_input, tokens_output, model, latency_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ts, username, feature, source_lang, target_lang,
        native_lang, ui_lang, user_input, ai_output, json.dumps(extra or {}, ensure_ascii=False),
        tokens_input, tokens_output, model, latency_ms
    ))
    conn.commit()

def fetch_history(
    username: str,
    limit: int = 50,
    feature: Optional[str] = None,
    source_lang: Optional[str] = None,
    target_lang: Optional[str] = None,
    search: Optional[str] = None,
    order: str = "DESC"
) -> List[Dict[str, Any]]:
    if not username:
        return []
    conn = _get_conn()
    clauses = ["username = ?"]
    params: list = [username]
    if feature:
        clauses.append("feature = ?"); params.append(feature)
    if source_lang:
        clauses.append("source_lang = ?"); params.append(source_lang)
    if target_lang:
        clauses.append("target_lang = ?"); params.append(target_lang)
    if search:
        clauses.append("(user_input LIKE ? OR ai_output LIKE ?)")
        like = f"%{search}%"; params.extend([like, like])

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"""
        SELECT id, timestamp, username, feature, source_lang, target_lang,
               native_lang, ui_lang, user_input, ai_output, extra,
               tokens_input, tokens_output, model, latency_ms
        FROM history
        {where}
        ORDER BY id {order}
        LIMIT ?
    """
    params.append(limit)
    rows = conn.execute(sql, tuple(params)).fetchall()
    result = []
    for r in rows:
        item = dict(r)
        try:
            item["extra"] = json.loads(item.get("extra") or "{}")
        except Exception:
            item["extra"] = {}
        result.append(item)
    return result
