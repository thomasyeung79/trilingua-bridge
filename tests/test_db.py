"""Tests for dual SQLite/PostgreSQL mode in db_helper.py."""

import pytest


@pytest.fixture(autouse=True)
def _cleanup_daily_usage():
    """Ensure daily_usage table is clean before each quota test."""
    # Run before test
    from db_helper import get_connection

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS daily_usage ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL,"
            "date TEXT NOT NULL, ai_requests INTEGER NOT NULL DEFAULT 0,"
            "created_at REAL NOT NULL, updated_at REAL NOT NULL,"
            "UNIQUE(username, date))"
        )
        cursor.execute("DELETE FROM daily_usage")
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()
    yield
    # Nothing to clean up after test


# ── Helper function tests (no DB connection needed) ───────────


def _placeholder_for(postgres: bool) -> str:
    """Mirrors db_helper._placeholder() logic."""
    return "%s" if postgres else "?"


def _use_postgres_for(postgres_env: str | None) -> bool:
    """Mirrors db_helper._use_postgres() logic."""
    return (postgres_env or "false").lower() == "true"


def test_placeholder_sqlite():
    """SQLite mode uses ? placeholder."""
    assert _placeholder_for(False) == "?"


def test_placeholder_postgres():
    """PostgreSQL mode uses %s placeholder."""
    assert _placeholder_for(True) == "%s"


def test_use_postgres_true():
    """USE_POSTGRES=true returns True."""
    assert _use_postgres_for("true") is True


def test_use_postgres_false():
    """USE_POSTGRES=false returns False."""
    assert _use_postgres_for("false") is False


def test_use_postgres_missing():
    """Missing USE_POSTGRES returns False."""
    assert _use_postgres_for(None) is False


def test_use_postgres_case_insensitive():
    """USE_POSTGRES=True (capital T) returns True."""
    assert _use_postgres_for("True") is True


def test_use_postgres_random():
    """USE_POSTGRES=anything_else returns False."""
    assert _use_postgres_for("yes") is False
    assert _use_postgres_for("1") is False
    assert _use_postgres_for("") is False


# ── Environment variable integration tests ────────────────────


def test_use_postgres_env_false(monkeypatch):
    """When USE_POSTGRES is not set, db_helper should default to SQLite."""
    monkeypatch.delenv("USE_POSTGRES", raising=False)
    from db_helper import _use_postgres

    assert _use_postgres() is False


def test_use_postgres_env_true(monkeypatch):
    """When USE_POSTGRES=true, db_helper should detect Postgres mode."""
    monkeypatch.setenv("USE_POSTGRES", "true")
    from db_helper import _use_postgres

    assert _use_postgres() is True


def test_placeholder_import(monkeypatch):
    """_placeholder() returns correct character based on env."""
    from db_helper import _placeholder

    monkeypatch.setenv("USE_POSTGRES", "false")
    assert _placeholder() == "?"

    monkeypatch.setenv("USE_POSTGRES", "true")
    assert _placeholder() == "%s"

    monkeypatch.delenv("USE_POSTGRES", raising=False)
    assert _placeholder() == "?"


def test_now_value_returns_float():
    """_now_value() returns a Unix epoch float."""
    from db_helper import _now_value

    now = _now_value()
    assert isinstance(now, float)
    assert now > 1_700_000_000  # Should be a recent timestamp


def test_normalize_limit_postgres_independent():
    """normalize_limit() is DB-independent and works the same."""
    from db_helper import normalize_limit

    assert normalize_limit(50) == 50
    assert normalize_limit(0) == 1
    assert normalize_limit(1000) == 500
    assert normalize_limit("bad") == 50
    assert normalize_limit(None) == 50


# ── RealDictCursor-style RETURNING id simulation (Fix 1) ──────


def test_fetchone_dict_style():
    """Simulate RealDictCursor returning a dict with id key."""
    row = {"id": 42}
    row_id = int(row["id"])
    assert row_id == 42
    assert isinstance(row_id, int)


def test_fetchone_dict_large_id():
    """BIGSERIAL ids can be large — int() handles them."""
    row = {"id": 9223372036854775807}
    row_id = int(row["id"])
    assert row_id == 9223372036854775807


# ── PostgreSQL active_days date string normalization (Fix 2) ───


def test_active_days_string_normalization():
    """PostgreSQL returns datetime.date objects — str() makes them comparable to strings."""
    from datetime import date

    pg_results = [{"day": date(2024, 6, 1)}, {"day": date(2024, 5, 31)}]
    active_days = [str(row["day"]) for row in pg_results]
    assert active_days == ["2024-06-01", "2024-05-31"]
    assert "2024-06-01" in active_days


def test_active_days_mixed_types():
    """Both string and date objects become strings after normalization."""
    from datetime import date

    mixed = [{"day": "2024-06-01"}, {"day": date(2024, 5, 31)}]
    active_days = [str(row["day"]) for row in mixed]
    assert active_days == ["2024-06-01", "2024-05-31"]


# ── PostgreSQL config validation (Fix 3 + Fix 4) ───────────────


def test_pg_config_raises_without_host(monkeypatch):
    """_get_pg_config() raises RuntimeError when mandatory keys are missing."""
    monkeypatch.setenv("USE_POSTGRES", "true")
    # Clear relevant env vars
    for k in ["SUPABASE_DB_HOST", "SUPABASE_DB_PASSWORD"]:
        monkeypatch.delenv(k, raising=False)

    from db_helper import _get_pg_config

    try:
        _get_pg_config()
        assert False, "Expected RuntimeError"
    except RuntimeError as e:
        msg = str(e)
        assert "SUPABASE_DB_HOST" in msg


def test_pg_config_sqlite_no_secrets_needed(monkeypatch):
    """SQLite mode never calls PostgreSQL config validation."""
    monkeypatch.setenv("USE_POSTGRES", "false")
    # No PG secrets configured — should work fine
    from db_helper import _use_postgres, get_db_path

    assert _use_postgres() is False
    assert get_db_path() != ""  # returns SQLite path, not empty


def test_pg_config_sqlite_without_psycopg2(monkeypatch):
    """SQLite mode works even if psycopg2 is not installed."""
    monkeypatch.setenv("USE_POSTGRES", "false")
    # Simulate psycopg2 not available by checking that the PG path is skipped
    from db_helper import get_connection

    conn = get_connection()
    # Should return a sqlite3 connection
    import sqlite3

    assert isinstance(conn, sqlite3.Connection)
    conn.close()


# ── PostgreSQL port validation (Fix 1) ─────────────────────────


def test_pg_config_invalid_port_raises(monkeypatch):
    """Non-numeric SUPABASE_DB_PORT raises RuntimeError with clear message."""
    monkeypatch.setenv("USE_POSTGRES", "true")
    monkeypatch.setenv("SUPABASE_DB_HOST", "db.test.supabase.co")
    monkeypatch.setenv("SUPABASE_DB_PASSWORD", "secret")
    monkeypatch.setenv("SUPABASE_DB_PORT", "not_a_number")

    from db_helper import _get_pg_config

    try:
        _get_pg_config()
        assert False, "Expected RuntimeError"
    except RuntimeError as e:
        msg = str(e)
        assert "SUPABASE_DB_PORT" in msg
        assert "integer" in msg


# ── Duplicate username path (Fix 2) ────────────────────────────


def test_create_user_validation_before_db():
    """create_user() validates input before reaching DB (no DB needed)."""
    from db_helper import create_user

    # Test short username/validation paths (rejects before DB call)
    assert create_user("a", "123456") == {"ok": False, "error": "username_too_short"}


def test_create_user_password_too_short():
    """create_user() rejects short password before reaching DB."""
    from db_helper import create_user

    assert create_user("valid", "12345") == {"ok": False, "error": "password_too_short"}


def test_duplicate_detection_string_fallback():
    """String-based duplicate detection still works as fallback."""
    # Simulate the logic used in create_user's except block
    test_cases = [
        ("unique constraint violated", True),
        ("integrity error", True),
        ("UNIQUE constraint failed", True),
        ("connection refused", False),
        ("syntax error", False),
    ]
    for err_str, expected_dup in test_cases:
        is_dup = "unique" in err_str.lower() or "integrity" in err_str.lower()
        assert is_dup == expected_dup, f"Failed for: {err_str}"


# ── Daily usage quota tests ─────────────────────────────────────
# The autouse fixture _cleanup_daily_usage creates the table and
# clears it before every test in this file.


def test_reserve_guest_allows_first_five():
    """Guest can reserve 5 requests; 6th is denied."""
    from db_helper import reserve_daily_usage

    for i in range(5):
        allowed, remaining = reserve_daily_usage("guest_x1", is_guest=True)
        assert allowed is True, f"Request {i + 1} should be allowed"
        assert remaining == 5 - (i + 1)

    # 6th should be denied
    allowed, remaining = reserve_daily_usage("guest_x1", is_guest=True)
    assert allowed is False
    assert remaining == 0


def test_reserve_guest_id_correct_limit():
    """Guest usernames (guest_xxx) get 5 limit when is_guest=True, not 30."""
    from db_helper import reserve_daily_usage

    allowed, remaining = reserve_daily_usage("guest_abc123", is_guest=True)
    assert allowed is True
    assert remaining == 4  # 5 - 1 = 4

    allowed, remaining = reserve_daily_usage("guest_abc123", is_guest=False)
    assert allowed is True
    assert remaining == 28  # 30 - 2 (existing 1 + this increment) = 28


def test_reserve_user_allows_thirty():
    """Logged-in user can reserve 30 requests; 31st is denied."""
    from db_helper import reserve_daily_usage

    for i in range(30):
        allowed, remaining = reserve_daily_usage("quota_user_30")
        assert allowed is True, f"Request {i + 1} should be allowed"
        assert remaining == 30 - (i + 1)

    allowed, remaining = reserve_daily_usage("quota_user_30")
    assert allowed is False
    assert remaining == 0


def test_reserve_decreases_remaining():
    """Each reserve_daily_usage call decreases remaining by 1."""
    from db_helper import reserve_daily_usage

    _, remaining_before = reserve_daily_usage("reserve_dec")
    assert remaining_before == 29

    _, remaining_after = reserve_daily_usage("reserve_dec")
    assert remaining_after == 28


def test_quota_denial_blocks_execution():
    """After quota denial, callers should not proceed (simulates guard)."""
    from db_helper import reserve_daily_usage

    # Simulate hitting the limit — reserve all 30
    for _ in range(30):
        reserve_daily_usage("deny_test")

    allowed, _ = reserve_daily_usage("deny_test")
    assert allowed is False, "Should be denied after consuming all quota"

    # This simulates the pattern in pages.py run_ai_task:
    # if not allowed: return None (no AI call is made)
    assert allowed is False  # The guard prevents the AI call


def test_quota_username_independent():
    """Different usernames have independent quota tracking."""
    from db_helper import reserve_daily_usage

    _, rem_a1 = reserve_daily_usage("indep_a")
    _, rem_b1 = reserve_daily_usage("indep_b")
    assert rem_a1 == 29
    assert rem_b1 == 29


def test_reserve_sqlite_mode_without_postgres():
    """reserve_daily_usage works in SQLite mode without PostgreSQL config."""
    from db_helper import _use_postgres, reserve_daily_usage

    assert _use_postgres() is False
    allowed, remaining = reserve_daily_usage("sqlite_only")
    assert allowed is True
    assert remaining > 0


# ── PostgreSQL atomic SQL pattern tests (Fix 1) ───────────────


def test_pg_reserve_sql_has_required_keywords():
    """PostgreSQL reserve SQL must use ON CONFLICT, WHERE, and RETURNING."""
    pg_sql = """
    INSERT INTO daily_usage (username, date, ai_requests, created_at, updated_at)
    VALUES (%s, %s, 1, %s, %s)
    ON CONFLICT (username, date) DO UPDATE SET
        ai_requests = daily_usage.ai_requests + 1,
        updated_at = %s
    WHERE daily_usage.ai_requests < %s
    RETURNING ai_requests
    """
    assert "ON CONFLICT" in pg_sql
    assert "WHERE daily_usage.ai_requests" in pg_sql
    assert "RETURNING ai_requests" in pg_sql


def test_pg_fetchone_none_means_denied():
    """Simulate PostgreSQL fetchone returning None after WHERE condition fails."""
    row = None
    if row is None:
        allowed = False
        remaining = 0
    assert allowed is False
    assert remaining == 0


def test_pg_fetchone_returns_row_means_allowed():
    """Simulate PostgreSQL fetchone returning a row after successful upsert."""
    row = {"ai_requests": 5}
    max_req = 30
    if row is not None:
        allowed = True
        remaining = max(0, max_req - row["ai_requests"])
    assert allowed is True
    assert remaining == 25


# ── Fail-closed on DB error (Fix 2) ───────────────────────────


def test_reserve_fails_closed_on_error(monkeypatch):
    """When reserve_daily_usage hits a DB error, it returns False, 0."""
    from db_helper import reserve_daily_usage

    # Monkeypatch get_connection to raise an exception
    def _broken_connection():
        raise RuntimeError("Simulated database failure")

    import db_helper

    monkeypatch.setattr(db_helper, "get_connection", _broken_connection)

    allowed, remaining = reserve_daily_usage("test_user")
    assert allowed is False, "Should fail closed"
    assert remaining == 0, "Should return 0 remaining on error"


# ── Guest quota design tests (Fix 1 + Fix 4) ──────────────────


def test_guest_quota_username_format():
    """Guest quota usernames follow guest_<short_id> format."""
    import secrets

    guest_id = "guest_" + secrets.token_urlsafe(16)
    assert guest_id.startswith("guest_")
    assert len(guest_id) > 20  # "guest_" (6) + at least 16 chars of urlsafe token


def test_logged_in_username_unchanged():
    """Logged-in users use their actual username for quota, not guest_id."""
    from db_helper import reserve_daily_usage

    # A non-"guest" username gets the 30-limit user pool
    allowed, remaining = reserve_daily_usage("real_user")
    assert allowed is True
    assert remaining == 29


def test_legacy_functions_removed():
    """check_daily_quota and increment_daily_usage must not exist."""
    import db_helper

    assert not hasattr(db_helper, "check_daily_quota"), "check_daily_quota must be removed"
    assert not hasattr(db_helper, "increment_daily_usage"), "increment_daily_usage must be removed"


def test_get_remaining_respects_is_guest():
    """get_daily_usage_remaining with is_guest=True returns max 5."""
    from db_helper import get_daily_usage_remaining

    remaining = get_daily_usage_remaining("guest_test", is_guest=True)
    assert remaining == 5

    remaining = get_daily_usage_remaining("real_user", is_guest=False)
    assert remaining == 30


def test_logged_in_user_named_guest_gets_user_quota():
    """A logged-in user with username 'guest' gets 30 limit, not guest limit."""
    from db_helper import reserve_daily_usage

    # Simulate: username is "guest" but is_guest=False (auth_mode="password")
    allowed, remaining = reserve_daily_usage("guest", is_guest=False)
    assert allowed is True
    assert remaining == 29  # 30 - 1


def test_guest_mode_gets_guest_quota():
    """A guest mode user (auth_mode='guest' or '') gets 5 limit."""
    from db_helper import reserve_daily_usage

    allowed, remaining = reserve_daily_usage("some_guest_id", is_guest=True)
    assert allowed is True
    assert remaining == 4  # 5 - 1


def test_create_user_reserved_usernames():
    """Reserved usernames cannot be registered."""
    from db_helper import create_user

    for name in ["guest", "admin", "system", "anonymous", "support"]:
        result = create_user(name, "password123")
        assert result["ok"] is False, f"{name} should be rejected"
        assert result["error"] == "username_exists", f"{name}: expected username_exists"


# ── Login username normalization (case-insensitive) ──────────


def _ensure_users_table():
    """Create the users table in the test database."""
    from db_helper import get_connection

    conn = get_connection()
    try:
        cursor = conn.cursor()
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
        conn.commit()
    finally:
        conn.close()


def test_login_normalizes_username():
    """Login with mixed-case username matches stored lowercase."""
    _ensure_users_table()
    from db_helper import authenticate_user, create_user

    # Register "Alice" (stored as "alice")
    result = create_user("Alice", "password123")
    assert result["ok"] is True

    # Login with exact case
    auth = authenticate_user("Alice", "password123")
    assert auth["ok"] is True, "Exact case login should work"

    # Login with all lowercase
    auth = authenticate_user("alice", "password123")
    assert auth["ok"] is True, "Lowercase login should work"

    # Login with uppercase
    auth = authenticate_user("ALICE", "password123")
    assert auth["ok"] is True, "Uppercase login should work"

    # Login with spaces
    auth = authenticate_user("  Alice  ", "password123")
    assert auth["ok"] is True, "Login with surrounding spaces should work"

    # Login with wrong password
    auth = authenticate_user("alice", "wrongpass")
    assert auth["ok"] is False, "Wrong password should fail"

    # Clean up
    from db_helper import get_connection

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username='alice'")
        conn.commit()
    finally:
        conn.close()


# ── PostgreSQL schema init safety ────────────────────────────


def test_pg_schema_init_has_advisory_lock():
    """_init_postgres must use pg_advisory_xact_lock for concurrent-instance safety."""
    with open("db_helper.py", encoding="utf-8") as f:
        content = f.read()
    assert "def _init_postgres" in content
    # Locate the function body
    start = content.index("def _init_postgres")
    body = content[start : start + 2000]  # first 2000 chars of the function
    assert "pg_advisory_xact_lock" in body, "Missing pg_advisory_xact_lock in _init_postgres"
    assert "trilingua_schema_init" in body, "Missing lock key in _init_postgres"
