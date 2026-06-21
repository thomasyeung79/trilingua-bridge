"""
Production error monitoring via Sentry.

Initialisation (called once from app.py):

    from error_monitor import init_monitoring
    init_monitoring()

Does nothing if SENTRY_DSN is not configured.

Privacy guarantees:
- request bodies / cookies / query strings are stripped
- user section is removed
- embedded secrets (Bearer, Basic, postgres://, sk-...) are redacted
- exception values are sanitised
- message/logentry strings are sanitised
- non-string keys do not crash
"""

import os
import re
from typing import Any

SENTRY_DSN_ENV = "SENTRY_DSN"
_sentry_initialized = False

# Keys considered sensitive regardless of case or nesting.
_SENSITIVE_KEY_PATTERNS = {
    "authorization",
    "auth",
    "cookie",
    "set-cookie",
    "cookies",
    "password",
    "passwd",
    "secret",
    "token",
    "api_token",
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
    "x-api-key",
    "openai",
    "open_ai",
    "anthropic",
    "deepseek",
    "supabase",
    "database_url",
    "db_url",
    "db_password",
    "db_pass",
    "dsn",
    "private_key",
    "secret_key",
    "email",
    "phone",
}

# Secret patterns to redact anywhere inside string values.
_SECRET_REGEX = re.compile(
    r"((?:Bearer|Basic)\s+)[^\s,;'\"]+|"
    r"(?:postgres|postgresql|mysql|mongodb|redis)://\S+|"
    r"(?:https?://)[^\s]*@[^\s]+|"  # credential URL: https://user:pass@host
    r"(?:sk-|sk-ant-)[a-zA-Z0-9_-]{20,}|"
    r"\beyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+|"  # JWT
    r"(?:password|api_key|token)=\S+",  # password=/api_key=/token= in text
    re.IGNORECASE,
)


def _redact_secrets(text: str) -> str:
    """Replace embedded secrets in any string with [filtered-secret]."""
    return _SECRET_REGEX.sub(r"\1[filtered-secret]", text)


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


def _is_sensitive_key(key: str) -> bool:
    """Check if a dictionary key name matches a sensitive pattern case-insensitively."""
    k = str(key).lower().replace("-", "_").replace(" ", "_")
    return any(pattern in k for pattern in _SENSITIVE_KEY_PATTERNS)


def _sanitize_value(value: Any, depth: int = 0) -> Any:
    """Recursively sanitize a value, filtering sensitive keys at any depth."""
    MAX_DEPTH = 8
    if depth > MAX_DEPTH:
        return "[max-depth]"

    if isinstance(value, dict):
        result = {}
        for k, v in value.items():
            if _is_sensitive_key(k):
                result[k] = "[filtered]"
            else:
                result[k] = _sanitize_value(v, depth + 1)
        return result

    if isinstance(value, list):
        return [_sanitize_value(item, depth + 1) for item in value]

    if isinstance(value, str):
        return _redact_secrets(value)

    if isinstance(value, bytes):
        return "[filtered-bytes]"

    return value


def _sanitize_event(event: dict) -> dict:
    """Walk the entire Sentry event dict and redact sensitive data recursively."""
    # --- Fix 1: Remove request bodies ---
    if "request" in event:
        req = event["request"]
        for field in ("data", "body", "cookies", "query_string"):
            if field in req:
                req[field] = "[filtered]"
        if "headers" in req:
            req["headers"] = {}
        # Strip URL query parameters
        if "url" in req and isinstance(req["url"], str) and "?" in req["url"]:
            req["url"] = req["url"].split("?")[0]
        event["request"] = req

    # --- Fix 2: Remove user section ---
    if "user" in event:
        event["user"] = {}

    # --- Fix 3: Filter exception values (keep type/stacktrace, remove message text) ---
    if "exception" in event:
        exc = event["exception"]
        if isinstance(exc, dict) and "values" in exc:
            vals = exc["values"]
            if isinstance(vals, list):
                sanitised_vals = []
                for val in vals:
                    if isinstance(val, dict):
                        val_copy = {}
                        for k, v in val.items():
                            if k == "value":
                                val_copy[k] = "[filtered-exception-message]"
                            else:
                                val_copy[k] = _sanitize_value(v)
                        sanitised_vals.append(val_copy)
                    else:
                        sanitised_vals.append(val)
                exc["values"] = sanitised_vals

    # --- Walk all other top-level dicts for key-based redaction ---
    for top_key in list(event.keys()):
        if top_key in ("request", "user", "exception", "breadcrumbs", "_meta"):
            continue  # handled above or explicitly removed
        if isinstance(event[top_key], dict):
            event[top_key] = _sanitize_value(event[top_key])
        elif isinstance(event[top_key], list):
            event[top_key] = [_sanitize_value(item) for item in event[top_key]]

    # --- Fix 4: Sanitize message / logentry ---
    for msg_key in ("message", "logentry"):
        if msg_key in event and isinstance(event[msg_key], str):
            event[msg_key] = _redact_secrets(event[msg_key])
        elif msg_key in event and isinstance(event[msg_key], dict):
            event[msg_key] = _sanitize_value(event[msg_key])

    # --- Silenced sections ---
    if "breadcrumbs" in event:
        event["breadcrumbs"] = {}
    if "_meta" in event:
        event.pop("_meta", None)

    return event


def _before_send(event: dict, hint: dict) -> dict:
    """Sanitise events before sending to Sentry — strip sensitive data recursively.

    Returns the sanitised event, or None if sanitisation fails (fail closed).
    """
    try:
        return _sanitize_event(event)
    except Exception:
        return None


def _before_send_transaction(event: dict, hint: dict) -> dict:
    """Do not send any transaction events."""
    return None


def _detect_environment() -> str:
    """Detect the deployment environment for Sentry tagging."""
    env = _get_secret("SENTRY_ENVIRONMENT")
    if env:
        return env
    hostname = os.environ.get("HOSTNAME", "")
    if "streamlit" in hostname or os.environ.get("IS_STREAMLIT_CLOUD"):
        return "streamlit-cloud"
    if os.environ.get("DEPLOY_MODE") == "demo":
        return "production"
    return "local"


def _detect_release() -> str:
    """Detect the app release version for Sentry tagging."""
    release = _get_secret("SENTRY_RELEASE")
    if release:
        return release
    return "unknown"


def init_monitoring() -> bool:
    """
    Initialise Sentry SDK if SENTRY_DSN is configured.

    Returns True if Sentry was initialised, False otherwise.
    Safe to call multiple times — only initialises once.
    """
    global _sentry_initialized

    if _sentry_initialized:
        return True

    dsn = _get_secret(SENTRY_DSN_ENV)
    if not dsn:
        return False

    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=dsn,
            environment=_detect_environment(),
            release=_detect_release(),
            traces_sample_rate=0.0,
            send_default_pii=False,
            include_local_variables=False,
            max_breadcrumbs=0,
            before_send=_before_send,
            before_send_transaction=_before_send_transaction,
        )
        _sentry_initialized = True
        return True
    except Exception:
        return False


def capture_error(
    message: str,
    exception: BaseException | None = None,
    extra: dict | None = None,
) -> None:
    """Capture an error in Sentry (safe text only — no raw provider data)."""
    if not _sentry_initialized:
        return
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            if extra:
                for key, value in extra.items():
                    scope.set_extra(key, value)
            scope.set_extra("context", message)
            if exception:
                sentry_sdk.capture_exception(exception)
            else:
                sentry_sdk.capture_message(message)
    except Exception:
        pass


def is_active() -> bool:
    """Returns True if Sentry monitoring is active."""
    return _sentry_initialized
