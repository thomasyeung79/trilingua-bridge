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

def init_db():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            feature TEXT NOT NULL,
            source_lang TEXT,
            target_lang TEXT,
            user_input TEXT,
            ai_output TEXT,
            extra TEXT,
            tokens_input INTEGER,
            tokens_output INTEGER,
            model TEXT,
            latency_ms INTEGER
        );
    """)
    conn.commit()

def insert_history(
    feature: str,
    source_lang: str,
    target_lang: str,
    user_input: str,
    ai_output: str,
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
            timestamp, feature, source_lang, target_lang,
            user_input, ai_output, extra, tokens_input, tokens_output, model, latency_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ts, feature, source_lang, target_lang,
        user_input, ai_output, json.dumps(extra or {}, ensure_ascii=False),
        tokens_input, tokens_output, model, latency_ms
    ))
    conn.commit()

def fetch_history(
    limit: int = 50,
    feature: Optional[str] = None,
    source_lang: Optional[str] = None,
    target_lang: Optional[str] = None,
    search: Optional[str] = None,
    order: str = "DESC"
) -> List[Dict[str, Any]]:
    conn = _get_conn()
    clauses = []
    params: list = []
    if feature:
        clauses.append("feature = ?")
        params.append(feature)
    if source_lang:
        clauses.append("source_lang = ?")
        params.append(source_lang)
    if target_lang:
        clauses.append("target_lang = ?")
        params.append(target_lang)
    if search:
        clauses.append("(user_input LIKE ? OR ai_output LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like])

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"""
        SELECT id, timestamp, feature, source_lang, target_lang,
               user_input, ai_output, extra, tokens_input, tokens_output,
               model, latency_ms
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