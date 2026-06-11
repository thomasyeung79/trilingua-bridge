import os
import sqlite3
import time
import hashlib
import hmac
import secrets
from typing import Optional, List, Dict, Any

try:
    from error_monitor import capture_error
except Exception:
    def capture_error(*args, **kwargs): pass  # no-op fallback


# ── Dual-mode helpers ─────────────────────────────────────────

# ── Configuration helpers ────────────────────────────────────

_PG_CONFIG_KEYS = ["SUPABASE_DB_HOST", "SUPABASE_DB_NAME", "SUPABASE_DB_USER", "SUPABASE_DB_PASSWORD", "SUPABASE_DB_PORT"]


def _get_secret(key: str) -> str:
    """Read a config value from environment variables or Streamlit secrets."""
    value = os.environ.get(key)
    if not value:
        try:
            import streamlit as st
            value = st.secrets.get(key) or ""
        except Exception:
            pass
    return value or ""


def _get_pg_config() -> dict:
    """Read and validate PostgreSQL configuration from env / Streamlit secrets."""
    try:
        port = int(_get_secret("SUPABASE_DB_PORT") or "5432")
    except ValueError:
        raise RuntimeError(
            "Invalid PostgreSQL configuration: SUPABASE_DB_PORT must be an integer. "
            "Set USE_POSTGRES=false to use SQLite, or fix the port value."
        )
    config = {
        "host": _get_secret("SUPABASE_DB_HOST"),
        "dbname": _get_secret("SUPABASE_DB_NAME") or "postgres",
        "user": _get_secret("SUPABASE_DB_USER") or "postgres",
        "password": _get_secret("SUPABASE_DB_PASSWORD"),
        "port": port,
    }
    missing = [k for k in ("host", "password") if not config[k]]
    if missing:
        raise RuntimeError(
            f"Missing PostgreSQL configuration: SUPABASE_DB_HOST, SUPABASE_DB_PASSWORD. "
            "Set USE_POSTGRES=false to use SQLite, or configure these variables."
        )
    return config


def _use_postgres() -> bool:
    """Check whether to use PostgreSQL (Supabase) instead of SQLite."""
    return os.environ.get("USE_POSTGRES", "false").lower() == "true"


def _placeholder() -> str:
    """Return the SQL placeholder character for the active database."""
    return "%s" if _use_postgres() else "?"


def _now_value() -> float:
    """Return the current time as a Unix epoch float (compatible with both DBs)."""
    return time.time()


# ── Connection management ──────────────────────────────────────

def get_db_path() -> str:
    """
    SQLite-only: determine the local database file path.
    Ignored when USE_POSTGRES=true.
    """
    if _use_postgres():
        return ""

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


def get_connection():
    """
    Return a database connection for the active mode.

    PostgreSQL (USE_POSTGRES=true):
        Returns a psycopg2 connection with RealDictCursor.
        Configuration via SUPABASE_DB_HOST / _NAME / _USER / _PASSWORD / _PORT.

    SQLite (default):
        Returns a sqlite3 connection with Row factory.
    """
    if _use_postgres():
        import psycopg2
        from psycopg2.extras import RealDictCursor

        pg_config = _get_pg_config()

        return psycopg2.connect(
            host=pg_config["host"],
            dbname=pg_config["dbname"],
            user=pg_config["user"],
            password=pg_config["password"],
            port=pg_config["port"],
            sslmode="require",
            cursor_factory=RealDictCursor,
            connect_timeout=10,
        )

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


# ── Schema initialisation ──────────────────────────────────────

def init_db():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        if _use_postgres():
            _init_postgres(cursor)
        else:
            _init_sqlite(cursor)

        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()


def _init_sqlite(cursor):
    """Create tables with SQLite-compatible DDL."""
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
        CREATE TABLE IF NOT EXISTS daily_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            date TEXT NOT NULL,
            ai_requests INTEGER NOT NULL DEFAULT 0,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            UNIQUE(username, date)
        );
        """
    )

    _execute_indices(cursor)


def _init_postgres(cursor):
    """Create tables with PostgreSQL-compatible DDL."""
    # Acquire transaction-scoped advisory lock for concurrent-instance safety
    cursor.execute("SELECT pg_advisory_xact_lock(hashtext('trilingua_schema_init'))")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id BIGSERIAL PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            created_at DOUBLE PRECISION NOT NULL,
            last_login_at DOUBLE PRECISION
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id BIGSERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            timestamp DOUBLE PRECISION NOT NULL,
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
        CREATE TABLE IF NOT EXISTS saved_items (
            id BIGSERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            timestamp DOUBLE PRECISION NOT NULL,
            item_type TEXT NOT NULL,
            mode TEXT,
            source_lang TEXT,
            target_lang TEXT,
            prompt TEXT,
            content TEXT,
            note TEXT,
            reviewed_at DOUBLE PRECISION
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS vocab_items (
            id BIGSERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            timestamp DOUBLE PRECISION NOT NULL,
            term TEXT NOT NULL,
            meaning TEXT,
            source_lang TEXT,
            target_lang TEXT,
            example TEXT,
            strength INTEGER NOT NULL DEFAULT 1,
            reviewed_at DOUBLE PRECISION
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS learning_events (
            id BIGSERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            timestamp DOUBLE PRECISION NOT NULL,
            event_type TEXT NOT NULL,
            mode TEXT,
            target_lang TEXT,
            points INTEGER NOT NULL DEFAULT 1
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_usage (
            id BIGSERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            date TEXT NOT NULL,
            ai_requests INTEGER NOT NULL DEFAULT 0,
            created_at DOUBLE PRECISION NOT NULL,
            updated_at DOUBLE PRECISION NOT NULL,
            UNIQUE(username, date)
        );
        """
    )

    _execute_indices(cursor)


def _execute_indices(cursor):
    """Create indices — shared DDL between SQLite and PostgreSQL."""
    p = _placeholder()
    for sql in [
        "CREATE INDEX IF NOT EXISTS idx_history_user_time ON history(username, timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_history_mode ON history(mode)",
        "CREATE INDEX IF NOT EXISTS idx_history_langs ON history(source_lang, target_lang)",
        "CREATE INDEX IF NOT EXISTS idx_saved_user_time ON saved_items(username, timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_vocab_user_time ON vocab_items(username, timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_learning_user_time ON learning_events(username, timestamp DESC)",
    ]:
        cursor.execute(sql)


# ── Authentication (PBKDF2 — unchanged logic) ──────────────────

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


_RESERVED_USERNAMES = {"guest", "admin", "system", "anonymous", "support"}


def create_user(username: str, password: str) -> Dict[str, Any]:
    username_value = (username or "").strip().lower()
    password_value = password or ""

    if len(username_value) < 2:
        return {"ok": False, "error": "username_too_short"}

    if username_value in _RESERVED_USERNAMES:
        return {"ok": False, "error": "username_exists"}

    if len(password_value) < 6:
        return {"ok": False, "error": "password_too_short"}

    password_data = hash_password(password_value)
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO users (
                username,
                password_hash,
                password_salt,
                created_at,
                last_login_at
            )
            VALUES ({_placeholder()}, {_placeholder()}, {_placeholder()}, {_placeholder()}, {_placeholder()})
            """,
            (
                username_value,
                password_data["hash"],
                password_data["salt"],
                _now_value(),
                _now_value(),
            ),
        )
        conn.commit()
        return {"ok": True, "username": username_value}

    except sqlite3.IntegrityError:
        try:
            conn.rollback()
        except Exception:
            pass
        return {"ok": False, "error": "username_exists"}
    except Exception as ex:
        # Handle psycopg2.errors.UniqueViolation and fallback string check
        try:
            conn.rollback()
        except Exception:
            pass
        err_str = str(ex).lower()
        if "unique" in err_str or "integrity" in err_str:
            return {"ok": False, "error": "username_exists"}
        return {"ok": False, "error": "account_error"}

    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> Dict[str, Any]:
    username_value = (username or "").strip().lower()
    conn = get_connection()

    try:
        cursor = conn.cursor()
        p = _placeholder()
        cursor.execute(
            f"""
            SELECT username, password_hash, password_salt
            FROM users
            WHERE username = {p}
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
            f"UPDATE users SET last_login_at = {p} WHERE username = {p}",
            (_now_value(), username_value),
        )
        conn.commit()

        return {"ok": True, "username": row["username"]}

    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()


# ── Schema migration helper (SQLite only) ──────────────────────

def ensure_history_columns():
    """
    Adds missing columns for older local databases (SQLite only).
    PostgreSQL schema is always current after init_db().
    """
    if _use_postgres():
        return

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


# ── History ────────────────────────────────────────────────────

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
        now = _now_value()
        p = _placeholder()
        created_at_text = time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(now),
        )

        cursor.execute(
            f"""
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
            VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
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
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
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
    p = _placeholder()
    query = f"""
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
        WHERE username = {p}
    """

    params: List[Any] = [username or "guest"]

    if mode:
        query += f" AND mode = {p}"
        params.append(mode)

    if source_lang:
        query += f" AND source_lang = {p}"
        params.append(source_lang)

    if target_lang:
        query += f" AND target_lang = {p}"
        params.append(target_lang)

    if persona:
        query += f" AND persona = {p}"
        params.append(persona)

    if search:
        query += f" AND (user_input LIKE {p} OR ai_output LIKE {p})"
        like_value = f"%{search}%"
        params.extend([like_value, like_value])

    query += f" ORDER BY timestamp DESC LIMIT {p}"
    params.append(normalize_limit(limit))

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(query, params)

        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


# ── Learning events ────────────────────────────────────────────

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
        p = _placeholder()
        cursor.execute(
            f"""
            INSERT INTO learning_events (
                username,
                timestamp,
                event_type,
                mode,
                target_lang,
                points
            )
            VALUES ({p}, {p}, {p}, {p}, {p}, {p})
            """,
            (
                username or "guest",
                _now_value(),
                event_type or "activity",
                mode or "",
                target_lang or "",
                int(points or 1),
            ),
        )
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()


def fetch_learning_summary(username: str, days: int = 7) -> Dict[str, Any]:
    now = _now_value()
    since = now - max(1, int(days or 7)) * 86400
    today_start = time.mktime(time.localtime(now)[:3] + (0, 0, 0, 0, 0, -1))
    conn = get_connection()

    try:
        cursor = conn.cursor()
        p = _placeholder()

        # Week aggregate
        cursor.execute(
            f"""
            SELECT COUNT(*) AS count, COALESCE(SUM(points), 0) AS points
            FROM learning_events
            WHERE username = {p} AND timestamp >= {p}
            """,
            (username or "guest", since),
        )
        week = dict(cursor.fetchone())

        # Today aggregate
        cursor.execute(
            f"""
            SELECT COUNT(*) AS count, COALESCE(SUM(points), 0) AS points
            FROM learning_events
            WHERE username = {p} AND timestamp >= {p}
            """,
            (username or "guest", today_start),
        )
        today = dict(cursor.fetchone())

        # Top mode
        cursor.execute(
            f"""
            SELECT mode, COUNT(*) AS count
            FROM learning_events
            WHERE username = {p} AND timestamp >= {p} AND mode != ''
            GROUP BY mode
            ORDER BY count DESC
            LIMIT 1
            """,
            (username or "guest", since),
        )
        top_mode = cursor.fetchone()

        # Active days for streak calculation
        if _use_postgres():
            cursor.execute(
                f"""
                SELECT DISTINCT to_timestamp(timestamp)::date AS day
                FROM learning_events
                WHERE username = {p}
                ORDER BY day DESC
                LIMIT 30
                """,
                (username or "guest",),
            )
        else:
            cursor.execute(
                f"""
                SELECT DISTINCT date(timestamp, 'unixepoch', 'localtime') AS day
                FROM learning_events
                WHERE username = {p}
                ORDER BY day DESC
                LIMIT 30
                """,
                (username or "guest",),
            )
        active_days = [str(row["day"]) for row in cursor.fetchall()]

        # Streak calculation (pure Python — same for both DBs)
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


# ── Saved items (review book) ──────────────────────────────────

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
        p = _placeholder()
        sql = f"""
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
            VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
        """

        params = (
            username or "guest",
            _now_value(),
            item_type or "review",
            mode or "",
            source_lang or "",
            target_lang or "",
            prompt or "",
            content or "",
            note or "",
        )

        if _use_postgres():
            cursor.execute(sql + " RETURNING id", params)
            row = cursor.fetchone()
            row_id = int(row["id"])
        else:
            cursor.execute(sql, params)
            row_id = int(cursor.lastrowid)

        conn.commit()
        return row_id
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()


def fetch_saved_items(
    username: str,
    limit: int = 50,
    item_type: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    p = _placeholder()
    query = f"""
        SELECT id, username, timestamp, item_type, mode, source_lang,
               target_lang, prompt, content, note, reviewed_at
        FROM saved_items
        WHERE username = {p}
    """
    params: List[Any] = [username or "guest"]

    if item_type:
        query += f" AND item_type = {p}"
        params.append(item_type)

    if search:
        query += f" AND (prompt LIKE {p} OR content LIKE {p} OR note LIKE {p})"
        like_value = f"%{search}%"
        params.extend([like_value, like_value, like_value])

    query += f" ORDER BY timestamp DESC LIMIT {p}"
    params.append(normalize_limit(limit))

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


# ── Vocab items ────────────────────────────────────────────────

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
        p = _placeholder()
        sql = f"""
            INSERT INTO vocab_items (
                username,
                timestamp,
                term,
                meaning,
                source_lang,
                target_lang,
                example
            )
            VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p})
        """

        params = (
            username or "guest",
            _now_value(),
            (term or "").strip()[:200],
            meaning or "",
            source_lang or "",
            target_lang or "",
            example or "",
        )

        if _use_postgres():
            cursor.execute(sql + " RETURNING id", params)
            row = cursor.fetchone()
            row_id = int(row["id"])
        else:
            cursor.execute(sql, params)
            row_id = int(cursor.lastrowid)

        conn.commit()
        return row_id
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()


def fetch_vocab_items(
    username: str,
    limit: int = 80,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    p = _placeholder()
    query = f"""
        SELECT id, username, timestamp, term, meaning, source_lang,
               target_lang, example, strength, reviewed_at
        FROM vocab_items
        WHERE username = {p}
    """
    params: List[Any] = [username or "guest"]

    if search:
        query += f" AND (term LIKE {p} OR meaning LIKE {p} OR example LIKE {p})"
        like_value = f"%{search}%"
        params.extend([like_value, like_value, like_value])

    query += f" ORDER BY timestamp DESC LIMIT {p}"
    params.append(normalize_limit(limit))

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


# ── Daily usage quota ──────────────────────────────────────────

# Quota counts AI actions per day (one action = one Coach/Translate/etc run).
# Secondary analysis (naturalness, detection) runs within the same action.
# Quota is consumed at reservation time, not per provider API call.
# Guest quota uses a persistent per-session guest_id (unique per visitor).
# Guest quota is per Streamlit session. Closing browser or new incognito
# creates a new guest identity. Logged-in users have stable daily quota.
_DAILY_LIMIT_GUEST = 5
_DAILY_LIMIT_USER = 30


def _quota_limit(is_guest: bool) -> int:
    """Return the daily AI action limit for guest or logged-in users."""
    return _DAILY_LIMIT_GUEST if is_guest else _DAILY_LIMIT_USER


def reserve_daily_usage(username: str, is_guest: bool = False) -> tuple:
    """
    Atomically reserve one AI request for the user.

    Args:
        username: User identifier for quota tracking.
        is_guest: True for guest visitors (limit=5), False for logged-in (limit=30).

    PostgreSQL: uses INSERT ... ON CONFLICT DO UPDATE ... WHERE ... RETURNING
    which is a single atomic SQL statement — no race possible.

    SQLite: uses BEGIN IMMEDIATE + read-check-write within a transaction.
    SQLite serialises writes, so this is safe.

    Returns (allowed: bool, remaining_after: int).
    On database error, returns (False, 0) to fail closed.
    """
    today = time.strftime("%Y-%m-%d")
    now = _now_value()
    max_req = _quota_limit(is_guest)
    p = _placeholder()
    conn = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        if _use_postgres():
            # ── PostgreSQL: single atomic upsert with conditional WHERE ──
            cursor.execute(
                f"""
                INSERT INTO daily_usage (username, date, ai_requests, created_at, updated_at)
                VALUES ({p}, {p}, 1, {p}, {p})
                ON CONFLICT (username, date) DO UPDATE SET
                    ai_requests = daily_usage.ai_requests + 1,
                    updated_at = {p}
                WHERE daily_usage.ai_requests < {p}
                RETURNING ai_requests
                """,
                (username or "guest", today, now, now, now, max_req),
            )
            row = cursor.fetchone()
            conn.commit()

            if row:
                cur = row["ai_requests"]
                allowed = True
                remaining = max(0, max_req - cur)
            else:
                # No row returned = WHERE condition failed (quota reached)
                allowed = False
                remaining = 0

        else:
            # ── SQLite: transaction with read-check-write ──
            cursor.execute("BEGIN IMMEDIATE")
            cursor.execute(
                f"""SELECT ai_requests FROM daily_usage WHERE username = {p} AND date = {p}""",
                (username or "guest", today),
            )
            row = cursor.fetchone()
            current = row["ai_requests"] if row else 0
            allowed = current < max_req

            if allowed:
                if row:
                    cursor.execute(
                        f"""UPDATE daily_usage SET ai_requests = ai_requests + 1, updated_at = {p}
                            WHERE username = {p} AND date = {p}""",
                        (now, username or "guest", today),
                    )
                else:
                    cursor.execute(
                        f"""INSERT INTO daily_usage (username, date, ai_requests, created_at, updated_at)
                            VALUES ({p}, {p}, 1, {p}, {p})""",
                        (username or "guest", today, now, now),
                    )
            conn.commit()

            remaining = max(0, max_req - (current + 1 if allowed else current))

        return (allowed, remaining)

    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        # Fail closed: quota error should not allow unbounded AI calls
        capture_error("quota_reservation_failed")
        return (False, 0)

    finally:
        if conn is not None:
            conn.close()


def get_daily_usage_remaining(username: str, is_guest: bool = False) -> int:
    """Get the number of remaining AI requests for today for the given user.

    Args:
        username: User identifier for quota tracking.
        is_guest: True for guest visitors (limit=5), False for logged-in (limit=30).
    """
    today = time.strftime("%Y-%m-%d")
    max_requests = _quota_limit(is_guest)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        p = _placeholder()
        cursor.execute(
            f"""SELECT ai_requests FROM daily_usage WHERE username = {p} AND date = {p}""",
            (username or "guest", today),
        )
        row = cursor.fetchone()
        current = row["ai_requests"] if row else 0
        return max(0, max_requests - current)
    finally:
        conn.close()
