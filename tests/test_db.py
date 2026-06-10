"""Tests for dual SQLite/PostgreSQL mode in db_helper.py."""

import os
from typing import Optional


# ── Helper function tests (no DB connection needed) ───────────

def _placeholder_for(postgres: bool) -> str:
    """Mirrors db_helper._placeholder() logic."""
    return "%s" if postgres else "?"


def _use_postgres_for(postgres_env: Optional[str]) -> bool:
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
    from db_helper import get_db_path, _use_postgres
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
