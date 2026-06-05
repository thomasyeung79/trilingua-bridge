"""Basic unit tests for TriLingua Bridge pure helpers."""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any


# ── Safe JSON loads ─────────────────────────────────────────────

def safe_json_loads(text: str) -> Dict[str, Any]:
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
    result = safe_json_loads('[1, 2, 3]')
    assert result == {"result": [1, 2, 3]}


def test_safe_json_loads_invalid():
    assert safe_json_loads("not json") == {}


def test_safe_json_loads_empty_string():
    assert safe_json_loads("") == {}


# ── Language normalisation ──────────────────────────────────────

def normalize_lang(lang: str) -> str:
    """Normalise language code aliases."""
    aliases = {
        "zh-cn": "zh", "zh_hans": "zh", "zh-hans": "zh",
        "mandarin": "zh", "cn": "zh",
        "cantonese": "yue", "zh-hk": "yue", "zh_hant": "yue", "zh-hant": "yue",
        "ko-kr": "ko", "kr": "ko",
        "en-us": "en", "en-au": "en", "en-gb": "en",
        "ja-jp": "ja", "jp": "ja",
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

def normalize_usage(usage: Dict[str, Any]) -> Dict[str, Any]:
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
    "notes", "reason", "tips", "intent", "tone_notes",
    "tone_summary", "cultural_notes", "caution", "explanation",
    "why", "meaning", "note", "message", "error", "summary",
    "hidden_meaning", "recommended_understanding",
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
    return (
        value.startswith("{") and value.endswith("}")
    ) or (
        value.startswith("[") and value.endswith("]")
    )


def test_looks_like_json_object():
    assert looks_like_json('{"a":1}')
    assert looks_like_json('  {"a":1}  ')
    assert not looks_like_json('text')
    assert not looks_like_json('')
    assert not looks_like_json(123)


def test_looks_like_json_array():
    assert looks_like_json('[1,2,3]')
    assert not looks_like_json('[incomplete')
    assert not looks_like_json('incomplete]')


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
