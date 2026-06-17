"""AI Feature Recommendation Engine for TriLingua Bridge.

Recommends existing in-app features based on the user's language profile
and usage patterns. No external providers, no location data, no new DB tables.

Usage:
    from recommendation_engine import get_recommendations
    recs = get_recommendations(username, native_lang, target_lang, ...)
"""

from typing import Dict, Any, List, Optional


# ── Feature catalogue ──────────────────────────────────────────

_FEATURES = [
    {
        "id": "coach",
        "name": "AI Chat Coach",
        "description": "Get culturally-aware reply suggestions with tone analysis, cultural notes, and pronunciation guides.",
        "icon": "🎯",
        "page": "Coach",
    },
    {
        "id": "pronunciation",
        "name": "Pronunciation Guide",
        "description": "Hear native pronunciation with romanisation and text-to-speech for any language.",
        "icon": "🔊",
        "page": "Translate",
    },
    {
        "id": "grammar",
        "name": "Grammar Correction",
        "description": "Fix mistakes with level-appropriate explanations and reusable example patterns.",
        "icon": "✍️",
        "page": "Grammar",
    },
    {
        "id": "natural",
        "name": "Natural Expression",
        "description": "Turn translated-sounding sentences into something a native speaker would actually send.",
        "icon": "✨",
        "page": "Natural",
    },
    {
        "id": "tone",
        "name": "Tone Analysis",
        "description": "Check if your message sounds polite, rude, formal, friendly, or natural before you send it.",
        "icon": "🧭",
        "page": "Tone",
    },
    {
        "id": "vocab",
        "name": "Vocab Builder",
        "description": "Save phrases from real conversations and grow your personal phrase bank over time.",
        "icon": "📚",
        "page": "Vocab Bank",
    },
    {
        "id": "kpop",
        "name": "K-pop / Drama Context",
        "description": "Understand lyrics, drama lines, slang, and cultural references in media content.",
        "icon": "🎧",
        "page": "Kpop",
    },
    {
        "id": "conversation_memory",
        "name": "Conversation Memory Coach",
        "description": "Continue natural multi-turn conversations where the AI remembers what you talked about.",
        "icon": "💬",
        "page": "Coach",
    },
]


# ── Scoring helpers ────────────────────────────────────────────

def _language_goal_score(feature_id: str, target_lang: str) -> float:
    """How well the feature matches the user's target language (0.0–1.0)."""
    if feature_id == "kpop":
        return 1.0 if target_lang == "ko" else 0.3
    if feature_id == "conversation_memory":
        return 0.9  # useful for anyone practicing conversation
    return 0.8  # most features work well for any language


def _preference_score(
    feature_id: str,
    mode_counts: Dict[str, int],
    vocab_item_count: int,
    show_pron: bool,
    target_lang: str,
) -> float:
    """How well the feature matches the user's observed behaviour (0.0–1.0)."""
    tc = mode_counts.get("translate", 0)
    cc = mode_counts.get("coach", 0)
    gc = mode_counts.get("grammar", 0)
    vc = mode_counts.get("vocabulary", 0)

    if feature_id == "coach" and tc > 3:
        return 0.9
    if feature_id == "vocab" and (vocab_item_count > 5 or vc > 3):
        return 0.9
    if feature_id == "pronunciation" and show_pron:
        return 0.9
    if feature_id == "natural" and gc > 3:
        return 0.8
    if feature_id == "conversation_memory" and cc > 5:
        return 0.9
    if feature_id == "kpop" and target_lang == "ko":
        return 1.0
    if feature_id == "tone":
        return 0.6
    if feature_id == "grammar":
        return 0.5 if gc > 0 else 0.3
    return 0.3


def _activity_score(feature_id: str, mode_counts: Dict[str, int], total: int) -> float:
    """How actively the user engages with related features (0.0–1.0)."""
    if total == 0:
        return 0.3

    feature_mode_map = {
        "coach": "coach",
        "pronunciation": "translate",
        "grammar": "grammar",
        "natural": "grammar",
        "tone": "tone",
        "vocab": "vocabulary",
        "kpop": "kpop",
        "conversation_memory": "coach",
    }
    related = mode_counts.get(feature_mode_map.get(feature_id, ""), 0)

    if related > 10:
        return 0.9
    if related > 5:
        return 0.7
    if related > 2:
        return 0.5
    if total > 10:
        return 0.4
    return 0.3


# ── Public API ─────────────────────────────────────────────────

def get_recommendations(
    username: str,
    native_lang: str,
    target_lang: str,
    mode_counts: Optional[Dict[str, int]] = None,
    vocab_item_count: int = 0,
    show_pron: bool = False,
    max_results: int = 3,
) -> List[Dict[str, Any]]:
    """Return the top-N recommended features for a user.

    Args:
        username: Current user identifier.
        native_lang: User's native language code (e.g. 'zh', 'en').
        target_lang: User's learning target language code.
        mode_counts: Dict of {mode_name: usage_count} from history.
        vocab_item_count: Number of saved vocabulary items.
        show_pron: Whether the user has pronunciation/TTS enabled.
        max_results: Number of recommendations to return.

    Returns:
        List of dicts with keys: id, name, description, icon, page, score, breakdown.
    """
    total = sum((mode_counts or {}).values())

    scored: List[Dict[str, Any]] = []
    for feature in _FEATURES:
        fid = feature["id"]
        mc = mode_counts or {}
        ls = _language_goal_score(fid, target_lang)
        ps = _preference_score(fid, mc, vocab_item_count, show_pron, target_lang)
        act = _activity_score(fid, mc, total)

        overall = ls * 0.50 + ps * 0.30 + act * 0.20

        scored.append({
            **feature,
            "score": round(overall, 2),
            "breakdown": {
                "goal": round(ls * 0.50, 2),
                "preference": round(ps * 0.30, 2),
                "activity_momentum": round(act * 0.20, 2),
            },
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:max_results]
