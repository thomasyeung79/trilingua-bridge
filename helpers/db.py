import os
import sqlite3
import time
from typing import Any, Dict, List, Optional

DB_PATH = os.getenv("DB_PATH", "trilingua.db")

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
    # Ensure directory exists
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    return con

def _set_pragmas(con: sqlite3.Connection) -> None:
    cur = con.cursor()
    # Improve concurrency and durability balance
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")
    cur.execute("PRAGMA foreign_keys=ON;")

def _columns(con: sqlite3.Connection, table: str) -> List[str]:
    cur = con.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    return [row[1] for row in cur.fetchall()]

def _ensure_migrations(con: sqlite3.Connection) -> None:
    """
    Best-effort migrations for older schemas:
    - If only 'feature' exists but not 'mode', add 'mode' and backfill from 'feature'
    - Ensure 'persona' and 'ui_lang' exist
    """
    cur = con.cursor()
    cols = _columns(con, "history")

    # If table didn't exist, SCHEMA_SQL just created it and cols are up-to-date
    # Handle legacy 'feature' -> 'mode'
    if "mode" not in cols and "feature" in cols:
        cur.execute("ALTER TABLE history ADD COLUMN mode TEXT;")
        cur.execute("UPDATE history SET mode = feature WHERE mode IS NULL OR mode = '';")

    # Add missing newer columns if absent
    cols = _columns(con, "history")
    if "persona" not in cols:
        cur.execute("ALTER TABLE history ADD COLUMN persona TEXT;")
    if "ui_lang" not in cols:
        cur.execute("ALTER TABLE history ADD COLUMN ui_lang TEXT;")
    if "tokens_input" not in cols:
        cur.execute("ALTER TABLE history ADD COLUMN tokens_input INTEGER;")
    if "tokens_output" not in cols:
        cur.execute("ALTER TABLE history ADD COLUMN tokens_output INTEGER;")
    if "model" not in cols:
        cur.execute("ALTER TABLE history ADD COLUMN model TEXT;")
    if "latency_ms" not in cols:
        cur.execute("ALTER TABLE history ADD COLUMN latency_ms INTEGER;")

    # Recreate indexes if needed
    cur.execute("CREATE INDEX IF NOT EXISTS idx_history_user_ts ON history (username, timestamp DESC);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_history_mode ON history (mode);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_history_langs ON history (source_lang, target_lang);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_history_persona ON history (persona);")

def init_db() -> None:
    with _connect() as con:
        _set_pragmas(con)
        cur = con.cursor()
        for stmt in SCHEMA_SQL.strip().split(";"):
            s = stmt.strip()
            if s:
                cur.execute(s)
        _ensure_migrations(con)
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
    """
    Insert a history row. All text fields default to "" if None.
    Token/model/latency fields accept None.
    """
    ts = int(time.time() * 1000)
    with _connect() as con:
        _set_pragmas(con)
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
    """
    Fetch recent history for a user with optional filters.
    - search does a LIKE on user_input and ai_output.
    """
    if not username:
        return []

    limit = max(1, int(limit or 50))

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
    params.append(limit)

    rows: List[Dict[str, Any]] = []
    with _connect() as con:
        con.row_factory = sqlite3.Row
        _set_pragmas(con)
        cur = con.cursor()
        cur.execute(sql, params)
        for r in cur.fetchall():
            rows.append({k: r[k] for k in r.keys()})
    return rows
