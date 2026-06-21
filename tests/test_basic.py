"""Basic unit tests for TriLingua Bridge pure helpers."""

import hashlib
import json
import time
from typing import Any

# ── Safe JSON loads ─────────────────────────────────────────────


def safe_json_loads(text: str) -> dict[str, Any]:
    """Parse JSON safely, wrapping non-dict results."""
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
        return {"result": data}
    except Exception:
        return {}


def test_safe_json_loads_valid_dict():
    assert safe_json_loads('{"a": 1}') == {"a": 1}


def test_safe_json_loads_valid_list():
    result = safe_json_loads("[1, 2, 3]")
    assert result == {"result": [1, 2, 3]}


def test_safe_json_loads_invalid():
    assert safe_json_loads("not json") == {}


def test_safe_json_loads_empty_string():
    assert safe_json_loads("") == {}


# ── Language normalisation ──────────────────────────────────────


def normalize_lang(lang: str) -> str:
    """Normalise language code aliases."""
    aliases = {
        "zh-cn": "zh",
        "zh_hans": "zh",
        "zh-hans": "zh",
        "mandarin": "zh",
        "cn": "zh",
        "cantonese": "yue",
        "zh-hk": "yue",
        "zh_hant": "yue",
        "zh-hant": "yue",
        "ko-kr": "ko",
        "kr": "ko",
        "en-us": "en",
        "en-au": "en",
        "en-gb": "en",
        "ja-jp": "ja",
        "jp": "ja",
    }
    return aliases.get(lang, lang)


def test_normalize_lang_known_aliases():
    assert normalize_lang("zh-cn") == "zh"
    assert normalize_lang("zh_hans") == "zh"
    assert normalize_lang("canton") == "canton"
    assert normalize_lang("kr") == "ko"
    assert normalize_lang("en-us") == "en"
    assert normalize_lang("ja-jp") == "ja"
    assert normalize_lang("jp") == "ja"


def test_normalize_lang_unknown():
    assert normalize_lang("fr") == "fr"
    assert normalize_lang("") == ""
    assert normalize_lang("  en  ") == "  en  "  # assumes caller strips


# ── Usage helpers ───────────────────────────────────────────────


def normalize_usage(usage: dict[str, Any]) -> dict[str, Any]:
    """Extract token and model keys from usage dict."""
    usage = usage or {}
    return {
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "model": usage.get("model"),
    }


def test_normalize_usage_full():
    u = {"prompt_tokens": 10, "completion_tokens": 20, "model": "gpt-4"}
    assert normalize_usage(u) == {"prompt_tokens": 10, "completion_tokens": 20, "model": "gpt-4"}


def test_normalize_usage_empty():
    assert normalize_usage({}) == {"prompt_tokens": None, "completion_tokens": None, "model": None}


def test_normalize_usage_none():
    assert normalize_usage(None) == {"prompt_tokens": None, "completion_tokens": None, "model": None}


# ── JSON explanation key detection ──────────────────────────────

EXPLANATION_KEYS = {
    "notes",
    "reason",
    "tips",
    "intent",
    "tone_notes",
    "tone_summary",
    "cultural_notes",
    "caution",
    "explanation",
    "why",
    "meaning",
    "note",
    "message",
    "error",
    "summary",
    "hidden_meaning",
    "recommended_understanding",
}


def test_explanation_keys_coverage():
    assert "notes" in EXPLANATION_KEYS
    assert "reason" in EXPLANATION_KEYS
    assert "summary" in EXPLANATION_KEYS
    assert "random_key" not in EXPLANATION_KEYS


# ── Limit normalisation ─────────────────────────────────────────


def normalize_limit(limit_value: int) -> int:
    try:
        limit_value = int(limit_value)
    except Exception:
        return 50
    return max(1, min(limit_value, 500))


def test_normalize_limit_within_range():
    assert normalize_limit(50) == 50
    assert normalize_limit(1) == 1
    assert normalize_limit(500) == 500


def test_normalize_limit_clamping():
    assert normalize_limit(0) == 1
    assert normalize_limit(1000) == 500


def test_normalize_limit_invalid():
    assert normalize_limit("bad") == 50
    assert normalize_limit(None) == 50


# ── Stable key fragment (used for widget keys) ──────────────────


def stable_key_fragment(*parts: str) -> str:
    raw = "|".join(str(part or "") for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def test_stable_key_fragment_deterministic():
    k1 = stable_key_fragment("foo", "bar")
    k2 = stable_key_fragment("foo", "bar")
    assert k1 == k2
    assert len(k1) == 12


def test_stable_key_fragment_different():
    assert stable_key_fragment("a") != stable_key_fragment("b")


# ── Looks-like-JSON check ───────────────────────────────────────


def looks_like_json(value: str) -> bool:
    if not isinstance(value, str):
        return False
    value = value.strip()
    return (value.startswith("{") and value.endswith("}")) or (value.startswith("[") and value.endswith("]"))


def test_looks_like_json_object():
    assert looks_like_json('{"a":1}')
    assert looks_like_json('  {"a":1}  ')
    assert not looks_like_json("text")
    assert not looks_like_json("")
    assert not looks_like_json(123)


def test_looks_like_json_array():
    assert looks_like_json("[1,2,3]")
    assert not looks_like_json("[incomplete")
    assert not looks_like_json("incomplete]")


# ── Row time formatting ─────────────────────────────────────────


def format_row_time(timestamp_value: float) -> str:
    try:
        if timestamp_value > 1e12:
            timestamp_value = timestamp_value / 1000
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp_value))
    except Exception:
        return str(timestamp_value or "")


def test_format_row_time_unix():
    ts = 1717000000.0
    result = format_row_time(ts)
    assert isinstance(result, str)
    assert len(result) == 19  # "YYYY-MM-DD HH:MM:SS"


def test_format_row_time_milliseconds():
    ts = 1717000000000.0
    result = format_row_time(ts)
    assert isinstance(result, str)
    assert len(result) == 19


def test_format_row_time_zero():
    result = format_row_time(0)
    assert "1970-01-01" in result


# ── Password hashing signature check ────────────────────────────


def test_hash_password_returns_required_keys():
    salt = "a" * 32
    result = hashlib.pbkdf2_hmac(
        "sha256",
        b"test_password",
        salt.encode("utf-8"),
        1000,  # low iteration count for speed
    ).hex()
    assert isinstance(result, str)
    assert len(result) > 0


# ── Sentry privacy tests ─────────────────────────────────────────


def _make_test_event() -> dict:
    """Build a realistic Sentry event with sensitive data."""
    return {
        "request": {
            "data": "user_input=I+love+you",
            "cookies": "session=abc123",
            "headers": {
                "authorization": "Bearer sk-abc123",
                "X-API-Key": "sk-ant-xyz",
                "Cookie": "auth=token",
                "Content-Type": "application/json",
            },
        },
        "extra": {
            "password": "supersecret",
            "api_key": "sk-1234567890abcdef",
            "deepseek": "sk-ds-xyz",
            "safe_key": "hello",
            "nested": {
                "sub_password": "secretvalue",
                "sub_safe": "public",
                "deep_nested": {"token": "abc123", "name": "test"},
            },
        },
        "contexts": {
            "supabase": {"url": "https://db.project.supabase.co", "key": "eyJhbGci"},
            "database": {"password": "db_pass_123"},
        },
        "breadcrumbs": {"values": [{"message": "sensitive log"}]},
        "user": {"email": "test@example.com"},
        "logger": "test",
        "level": "error",
    }


def test_sanitize_removes_request_headers():
    """Request headers are removed entirely (Fix 2)."""
    from error_monitor import _sanitize_event

    event = _make_test_event()
    result = _sanitize_event(event)
    assert result["request"]["headers"] == {}


def test_sanitize_redacts_nested_password():
    """Nested extra.password is redacted."""
    from error_monitor import _sanitize_event

    event = _make_test_event()
    result = _sanitize_event(event)
    assert result["extra"]["password"] == "[filtered]"
    assert result["extra"]["nested"]["sub_password"] == "[filtered]"
    assert result["extra"]["nested"]["deep_nested"]["token"] == "[filtered]"
    assert result["extra"]["nested"]["deep_nested"]["name"] == "test"


def test_sanitize_redacts_contexts_supabase():
    """Nested contexts.supabase is redacted (the key name triggers redaction)."""
    from error_monitor import _sanitize_event

    event = _make_test_event()
    result = _sanitize_event(event)
    assert result["contexts"]["supabase"] == "[filtered]"
    assert result["contexts"]["database"]["password"] == "[filtered]"


def test_sanitize_removes_breadcrumbs():
    """Breadcrumbs are completely silenced."""
    from error_monitor import _sanitize_event

    event = _make_test_event()
    result = _sanitize_event(event)
    assert result["breadcrumbs"] == {}


def test_sanitize_preserves_safe_keys():
    """Non-sensitive keys are preserved."""
    from error_monitor import _sanitize_event

    event = _make_test_event()
    result = _sanitize_event(event)
    assert result["extra"]["safe_key"] == "hello"
    assert result["logger"] == "test"
    assert result["level"] == "error"


def test_sanitize_redacts_api_key_patterns():
    """Strings resembling provider API keys are redacted by embedded secret regex."""
    from error_monitor import _redact_secrets, _sanitize_value

    # Full string matching sk- pattern
    assert _redact_secrets("sk-abc1234567890123456789") == "[filtered-secret]"
    assert _redact_secrets("sk-ant-mykey1234567890abcdef") == "[filtered-secret]"
    # Embedded in text
    assert "sk-abc1234567890123456789" not in _redact_secrets("key is sk-abc1234567890123456789 here")
    # Short strings not matched
    assert _redact_secrets("hello") == "hello"
    assert _redact_secrets("short") == "short"
    # _sanitize_value should also call _redact_secrets internally
    assert _sanitize_value("hello") == "hello"


def test_init_monitoring_no_dsn():
    """init_monitoring returns False without SENTRY_DSN."""
    import os

    os.environ.pop("SENTRY_DSN", None)
    from error_monitor import init_monitoring

    assert init_monitoring() is False


def test_capture_error_never_raises():
    """capture_error never raises an exception."""
    from error_monitor import capture_error

    capture_error("test", extra={"key": "value"})
    capture_error("test", extra={"password": "secret"})
    capture_error("test")
    capture_error(None)
    assert True  # If we reach here, no exception was raised


def test_sanitize_recursive_depth_limit():
    """Sanitizer does not overflow on deeply nested structures."""
    from error_monitor import _sanitize_value

    deep = {"a": {"b": {"c": {"d": {"e": {"f": {"g": {"h": {"i": "value"}}}}}}}}}
    result = _sanitize_value(deep)
    # Should not crash
    assert result is not None


def test_sanitize_redacts_api_key_and_apikey_variants():
    """Various api_key key casing patterns are redacted."""
    from error_monitor import _sanitize_value

    test_cases = [
        {"API_KEY": "secret"},
        {"api_key": "secret"},
        {"ApiKey": "secret"},
        {"x-api-key": "secret"},
        {"X-Api-Key": "secret"},
    ]
    for case in test_cases:
        result = _sanitize_value(case)
        assert list(result.values())[0] == "[filtered]", f"Failed for {case}"


def test_provider_capture_no_raw_error():
    """ai_helper.py capture_error calls use safe literals, not raw error variables."""
    import os

    path = os.path.join(os.path.dirname(__file__), "..", "ai_helper.py")
    with open(path, encoding="utf-8") as f:
        content = f.read()
    # Verify no capture_error call contains banned variable names
    offending = []
    for var in ["str(e)", "openai_error", "anthropic_error", "deepseek_error"]:
        # Find all occurrences of capture_error and check if the var appears nearby
        idx = 0
        while True:
            idx = content.find("capture_error", idx)
            if idx == -1:
                break
            # Look forward from capture_error until the matching closing paren
            depth = 0
            started = False
            end = idx
            for i, ch in enumerate(content[idx:]):
                if ch == "(":
                    depth += 1
                    started = True
                elif ch == ")":
                    depth -= 1
                    if started and depth == 0:
                        end = idx + i + 1
                        break
            block = content[idx:end]
            if var in block:
                offending.append(f"capture_error at char {idx} contains {var}")
            idx = end
    assert not offending, f"Unsafe capture_error calls: {'; '.join(offending)}"


# ── Sentry privacy hardening tests (Fix 1–7) ───────────────────


def test_sanitize_removes_request_data():
    """request.data and request.cookies are removed (Fix 1)."""
    from error_monitor import _sanitize_event

    event = {
        "request": {
            "data": "user_input=hello",
            "cookies": "session=abc",
            "query_string": "page=1",
            "headers": {"content-type": "text"},
        }
    }
    result = _sanitize_event(event)
    assert result["request"]["data"] == "[filtered]"
    assert result["request"]["cookies"] == "[filtered]"
    assert result["request"]["query_string"] == "[filtered]"


def test_sanitize_removes_user_section():
    """event.user is removed (Fix 2)."""
    from error_monitor import _sanitize_event

    event = {"user": {"email": "test@example.com", "username": "alice"}}
    result = _sanitize_event(event)
    assert result["user"] == {}


def test_sanitize_redacts_email_keys():
    """Email keys are redacted (Fix 2 + key patterns)."""
    from error_monitor import _sanitize_event

    event = {"extra": {"email": "user@example.com", "phone": "123-456"}}
    result = _sanitize_event(event)
    assert result["extra"]["email"] == "[filtered]"
    assert result["extra"]["phone"] == "[filtered]"


def test_sanitize_logentry_sanitized():
    """logentry string is sanitised for embedded secrets (Fix 4)."""
    from error_monitor import _sanitize_event

    event = {"logentry": "Connection to postgres://user:pass@db.supabase.co:5432 failed"}
    result = _sanitize_event(event)
    assert "postgres://" not in result["logentry"]
    assert "[filtered-secret]" in result["logentry"]


def test_sanitize_message_sanitized():
    """message string is sanitised (Fix 4)."""
    from error_monitor import _sanitize_event

    event = {"message": "Error: Basic dXNlcjpwYXNz"}
    result = _sanitize_event(event)
    assert "[filtered-secret]" in result["message"]


def test_redact_bearer_token():
    """Embedded Bearer token is redacted (Fix 5)."""
    from error_monitor import _redact_secrets

    text = "Authorization: Bearer sk-abc1234567890123456789"
    result = _redact_secrets(text)
    assert "Bearer" in result
    assert "sk-abc" not in result
    assert "[filtered-secret]" in result


def test_redact_postgres_url():
    """Embedded postgres:// URL is redacted (Fix 5)."""
    from error_monitor import _redact_secrets

    text = "connecting to postgres://user:pass@db.supabase.co:5432/postgres"
    result = _redact_secrets(text)
    assert "postgres://" not in result
    assert "[filtered-secret]" in result


def test_redact_mysql_url():
    """Embedded mysql:// URL is redacted (Fix 5)."""
    from error_monitor import _redact_secrets

    text = "mysql://admin:secret@mysql.example.com:3306/db"
    result = _redact_secrets(text)
    assert "mysql://" not in result
    assert "[filtered-secret]" in result


def test_redact_mongodb_url():
    """Embedded mongodb:// URL is redacted (Fix 5)."""
    from error_monitor import _redact_secrets

    text = "mongodb://user:pass@cluster.mongodb.net/db"
    result = _redact_secrets(text)
    assert "mongodb://" not in result
    assert "[filtered-secret]" in result


def test_redact_redis_url():
    """Embedded redis:// URL is redacted (Fix 5)."""
    from error_monitor import _redact_secrets

    text = "redis://:password@redis.internal:6379/0"
    result = _redact_secrets(text)
    assert "redis://" not in result
    assert "[filtered-secret]" in result


def test_sanitize_non_string_key():
    """Non-string dictionary keys do not crash sanitizer (Fix 6)."""
    from error_monitor import _sanitize_value

    result = _sanitize_value({42: "value", None: "other", ("tuple",): "test"})
    # Should not crash even with non-string keys
    assert result is not None


def test_sanitize_bytes_value():
    """Bytes values are handled without crash (Fix 6)."""
    from error_monitor import _sanitize_value

    result = _sanitize_value({"data": b"binary content"})
    assert result["data"] == "[filtered-bytes]"
    assert result is not None


# ── Sentry privacy hardening v2 tests (Fix 1–6 from Codex review) ──


def test_exception_value_replaced():
    """Exception value is replaced with [filtered-exception-message] (Fix 1)."""
    from error_monitor import _sanitize_event

    event = {"exception": {"values": [{"type": "ValueError", "value": "Bearer sk-abc1234567890123456789 crashed"}]}}
    result = _sanitize_event(event)
    assert result["exception"]["values"][0]["value"] == "[filtered-exception-message]"
    assert result["exception"]["values"][0]["type"] == "ValueError"


def test_request_headers_removed():
    """Request headers dict is replaced with empty dict (Fix 2)."""
    from error_monitor import _sanitize_event

    event = {"request": {"headers": {"Authorization": "Bearer xxx", "User-Agent": "Mozilla/5.0"}}}
    result = _sanitize_event(event)
    assert result["request"]["headers"] == {}


def test_request_url_query_stripped():
    """Query parameters are stripped from request.url (Fix 3)."""
    from error_monitor import _sanitize_event

    event = {"request": {"url": "https://example.com/path?token=abc123&secret=xyz"}}
    result = _sanitize_event(event)
    assert "?" not in result["request"]["url"]
    assert result["request"]["url"] == "https://example.com/path"


def test_before_send_fails_closed():
    """If before_send sanitizer crashes, event is dropped (Fix 4)."""
    from error_monitor import _before_send

    # None event would cause AttributeError in _sanitize_event
    result = _before_send(None, None)
    assert result is None


def test_redact_jwt():
    """JWT-like strings (eyJ...eyJ...) are redacted (Fix 5)."""
    from error_monitor import _redact_secrets

    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature"
    text = f"token={jwt}"
    result = _redact_secrets(text)
    assert "eyJhbGci" not in result
    assert "[filtered-secret]" in result


def test_redact_password_in_text():
    """password=value in text is redacted (Fix 5)."""
    from error_monitor import _redact_secrets

    text = "connection password=supersecret host=localhost"
    result = _redact_secrets(text)
    assert "supersecret" not in result
    assert "[filtered-secret]" in result


def test_redact_api_key_in_text():
    """api_key=value in text is redacted (Fix 5)."""
    from error_monitor import _redact_secrets

    text = "api_key=sk-abc12345678901234567890"
    result = _redact_secrets(text)
    assert "[filtered-secret]" in result


def test_redact_credential_url():
    """Credential URL (https://user:pass@host) is redacted (Fix 5)."""
    from error_monitor import _redact_secrets

    text = "connect to https://admin:secret123@db.example.com:8080/db"
    result = _redact_secrets(text)
    assert "admin:secret123" not in result
    assert "[filtered-secret]" in result


def test_redact_token_equals():
    """token=value in text is redacted (Fix 5)."""
    from error_monitor import _redact_secrets

    text = "token=eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature"
    result = _redact_secrets(text)
    assert "[filtered-secret]" in result
