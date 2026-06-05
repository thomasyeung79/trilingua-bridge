import os
import sqlite3
import time
import hashlib
import hmac
import secrets
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

    conn = sqlite3.connect(
        db_path,
        timeout=30,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row

    return conn


def init_db():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                timestamp REAL NOT NULL,
                created_at_text TEXT,
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
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                created_at REAL NOT NULL,
                last_login_at REAL
            );
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                timestamp REAL NOT NULL,
                item_type TEXT NOT NULL,
                mode TEXT,
                source_lang TEXT,
                target_lang TEXT,
                prompt TEXT,
                content TEXT,
                note TEXT,
                reviewed_at REAL
            );
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS vocab_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                timestamp REAL NOT NULL,
                term TEXT NOT NULL,
                meaning TEXT,
                source_lang TEXT,
                target_lang TEXT,
                example TEXT,
                strength INTEGER NOT NULL DEFAULT 1,
                reviewed_at REAL
            );
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS learning_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                timestamp REAL NOT NULL,
                event_type TEXT NOT NULL,
                mode TEXT,
                target_lang TEXT,
                points INTEGER NOT NULL DEFAULT 1
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

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_saved_user_time
            ON saved_items(username, timestamp DESC);
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_vocab_user_time
            ON vocab_items(username, timestamp DESC);
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_learning_user_time
            ON learning_events(username, timestamp DESC);
            """
        )

        conn.commit()

    finally:
        conn.close()


def hash_password(password: str, salt: Optional[str] = None) -> Dict[str, str]:
    salt_value = salt or secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        (password or "").encode("utf-8"),
        salt_value.encode("utf-8"),
        120_000,
    ).hex()

    return {
        "hash": password_hash,
        "salt": salt_value,
    }


def create_user(username: str, password: str) -> Dict[str, Any]:
    username_value = (username or "").strip()
    password_value = password or ""

    if len(username_value) < 2:
        return {"ok": False, "error": "username_too_short"}

    if len(password_value) < 6:
        return {"ok": False, "error": "password_too_short"}

    password_data = hash_password(password_value)
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (
                username,
                password_hash,
                password_salt,
                created_at,
                last_login_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                username_value,
                password_data["hash"],
                password_data["salt"],
                time.time(),
                time.time(),
            ),
        )
        conn.commit()
        return {"ok": True, "username": username_value}

    except sqlite3.IntegrityError:
        return {"ok": False, "error": "username_exists"}

    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> Dict[str, Any]:
    username_value = (username or "").strip()
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT username, password_hash, password_salt
            FROM users
            WHERE username = ?
            """,
            (username_value,),
        )
        row = cursor.fetchone()

        if not row:
            return {"ok": False, "error": "invalid_credentials"}

        candidate = hash_password(password or "", row["password_salt"])["hash"]

        if not hmac.compare_digest(candidate, row["password_hash"]):
            return {"ok": False, "error": "invalid_credentials"}

        cursor.execute(
            "UPDATE users SET last_login_at = ? WHERE username = ?",
            (time.time(), username_value),
        )
        conn.commit()

        return {"ok": True, "username": row["username"]}

    finally:
        conn.close()


def ensure_history_columns():
    """
    Adds missing columns for older local databases.
    SQLite has no simple ADD COLUMN IF NOT EXISTS, so inspect first.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(history);")
        existing_columns = {row["name"] for row in cursor.fetchall()}

        if "created_at_text" not in existing_columns:
            cursor.execute("ALTER TABLE history ADD COLUMN created_at_text TEXT;")

        conn.commit()

    finally:
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

    try:
        cursor = conn.cursor()
        now = time.time()
        created_at_text = time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(now),
        )

        cursor.execute(
            """
            INSERT INTO history (
                username,
                timestamp,
                created_at_text,
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username or "guest",
                now,
                created_at_text,
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

    finally:
        conn.close()


def normalize_limit(limit: int) -> int:
    try:
        limit_value = int(limit)
    except Exception:
        return 50

    return max(1, min(limit_value, 500))


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
            created_at_text,
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
    params.append(normalize_limit(limit))

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(query, params)

        return [dict(row) for row in cursor.fetchall()]

    finally:
        conn.close()


def insert_learning_event(
    username: str,
    event_type: str,
    mode: Optional[str] = None,
    target_lang: Optional[str] = None,
    points: int = 1,
):
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO learning_events (
                username,
                timestamp,
                event_type,
                mode,
                target_lang,
                points
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                username or "guest",
                time.time(),
                event_type or "activity",
                mode or "",
                target_lang or "",
                int(points or 1),
            ),
        )
        conn.commit()

    finally:
        conn.close()


def fetch_learning_summary(username: str, days: int = 7) -> Dict[str, Any]:
    now = time.time()
    since = now - max(1, int(days or 7)) * 86400
    today_start = time.mktime(time.localtime(now)[:3] + (0, 0, 0, 0, 0, -1))
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) AS count, COALESCE(SUM(points), 0) AS points
            FROM learning_events
            WHERE username = ? AND timestamp >= ?
            """,
            (username or "guest", since),
        )
        week = dict(cursor.fetchone())

        cursor.execute(
            """
            SELECT COUNT(*) AS count, COALESCE(SUM(points), 0) AS points
            FROM learning_events
            WHERE username = ? AND timestamp >= ?
            """,
            (username or "guest", today_start),
        )
        today = dict(cursor.fetchone())

        cursor.execute(
            """
            SELECT mode, COUNT(*) AS count
            FROM learning_events
            WHERE username = ? AND timestamp >= ? AND mode != ''
            GROUP BY mode
            ORDER BY count DESC
            LIMIT 1
            """,
            (username or "guest", since),
        )
        top_mode = cursor.fetchone()

        cursor.execute(
            """
            SELECT DISTINCT date(timestamp, 'unixepoch', 'localtime') AS day
            FROM learning_events
            WHERE username = ?
            ORDER BY day DESC
            LIMIT 30
            """,
            (username or "guest",),
        )
        active_days = [row["day"] for row in cursor.fetchall()]

        streak = 0
        cursor_day = time.strftime("%Y-%m-%d", time.localtime(now))
        active_set = set(active_days)
        while cursor_day in active_set:
            streak += 1
            previous = time.mktime(time.strptime(cursor_day, "%Y-%m-%d")) - 86400
            cursor_day = time.strftime("%Y-%m-%d", time.localtime(previous))

        return {
            "today_count": today["count"],
            "today_points": today["points"],
            "week_count": week["count"],
            "week_points": week["points"],
            "top_mode": top_mode["mode"] if top_mode else "-",
            "streak": streak,
        }

    finally:
        conn.close()


def add_saved_item(
    username: str,
    item_type: str,
    mode: str,
    source_lang: Optional[str],
    target_lang: Optional[str],
    prompt: str,
    content: str,
    note: Optional[str] = None,
) -> int:
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO saved_items (
                username,
                timestamp,
                item_type,
                mode,
                source_lang,
                target_lang,
                prompt,
                content,
                note
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username or "guest",
                time.time(),
                item_type or "review",
                mode or "",
                source_lang or "",
                target_lang or "",
                prompt or "",
                content or "",
                note or "",
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)

    finally:
        conn.close()


def fetch_saved_items(
    username: str,
    limit: int = 50,
    item_type: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    query = """
        SELECT id, username, timestamp, item_type, mode, source_lang,
               target_lang, prompt, content, note, reviewed_at
        FROM saved_items
        WHERE username = ?
    """
    params: List[Any] = [username or "guest"]

    if item_type:
        query += " AND item_type = ?"
        params.append(item_type)

    if search:
        query += " AND (prompt LIKE ? OR content LIKE ? OR note LIKE ?)"
        like_value = f"%{search}%"
        params.extend([like_value, like_value, like_value])

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(normalize_limit(limit))

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    finally:
        conn.close()


def add_vocab_item(
    username: str,
    term: str,
    meaning: str,
    source_lang: Optional[str],
    target_lang: Optional[str],
    example: Optional[str] = None,
) -> int:
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO vocab_items (
                username,
                timestamp,
                term,
                meaning,
                source_lang,
                target_lang,
                example
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username or "guest",
                time.time(),
                (term or "").strip()[:200],
                meaning or "",
                source_lang or "",
                target_lang or "",
                example or "",
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)

    finally:
        conn.close()


def fetch_vocab_items(
    username: str,
    limit: int = 80,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    query = """
        SELECT id, username, timestamp, term, meaning, source_lang,
               target_lang, example, strength, reviewed_at
        FROM vocab_items
        WHERE username = ?
    """
    params: List[Any] = [username or "guest"]

    if search:
        query += " AND (term LIKE ? OR meaning LIKE ? OR example LIKE ?)"
        like_value = f"%{search}%"
        params.extend([like_value, like_value, like_value])

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(normalize_limit(limit))

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    finally:
        conn.close()
