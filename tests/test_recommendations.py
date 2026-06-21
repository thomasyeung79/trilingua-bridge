"""Tests for the AI Feature Recommendation Engine."""

from recommendation_engine import _activity_score, _language_goal_score, _preference_score, get_recommendations

# ── Language goal score tests ──────────────────────────────────


def test_kpop_high_for_korean():
    """Korean learners get a high language goal score for K-pop."""
    assert _language_goal_score("kpop", "ko") == 1.0


def test_kpop_low_for_non_korean():
    """Non-Korean learners get a lower K-pop score."""
    assert _language_goal_score("kpop", "zh") == 0.3
    assert _language_goal_score("kpop", "en") == 0.3


def test_conversation_memory_high():
    """Conversation Memory Coach scores high for any language."""
    assert _language_goal_score("conversation_memory", "ko") == 0.9
    assert _language_goal_score("conversation_memory", "en") == 0.9


def test_default_features_high():
    """Most features get a default 0.8 language goal score."""
    for fid in ("coach", "pronunciation", "grammar", "natural", "tone", "vocab"):
        assert _language_goal_score(fid, "ko") == 0.8, f"{fid} should be 0.8"
        assert _language_goal_score(fid, "en") == 0.8, f"{fid} should be 0.8"


# ── Preference score tests ─────────────────────────────────────


def test_coach_preference_high_with_translation():
    """Frequent translation users get a high coach preference."""
    mc = {"translate": 10}
    score = _preference_score("coach", mc, 0, False, "ko")
    assert score == 0.9


def test_vocab_preference_high_with_saved_items():
    """Users with many vocab items get a high vocab preference."""
    score = _preference_score("vocab", {}, 10, False, "ko")
    assert score == 0.9


def test_pronunciation_preference_high_with_show_pron():
    """Users who enable pronunciation get a high pronunciation preference."""
    score = _preference_score("pronunciation", {}, 0, True, "ko")
    assert score == 0.9


def test_pronunciation_preference_low_without_show_pron():
    """Users who disable pronunciation get a lower pronunciation score."""
    score = _preference_score("pronunciation", {}, 0, False, "ko")
    assert score == 0.3


def test_natural_preference_high_with_grammar():
    """Frequent grammar users get a high natural expression preference."""
    mc = {"grammar": 5}
    score = _preference_score("natural", mc, 0, False, "ko")
    assert score == 0.8


def test_conversation_memory_preference_high_with_coach():
    """Users who use Coach often get a high conversation memory preference."""
    mc = {"coach": 10}
    score = _preference_score("conversation_memory", mc, 0, False, "ko")
    assert score == 0.9


def test_kpop_preference_high_for_korean():
    """Korean learners get a high K-pop preference."""
    score = _preference_score("kpop", {}, 0, False, "ko")
    assert score == 1.0


# ── Activity score tests ───────────────────────────────────────


def test_activity_high_with_related_usage():
    """High related feature usage gives a high activity score."""
    mc = {"coach": 15}
    score = _activity_score("coach", mc, 50)
    assert score == 0.9
    score_mem = _activity_score("conversation_memory", mc, 50)
    assert score_mem == 0.9


def test_activity_neutral_with_no_history():
    """No usage history gives a neutral activity score."""
    score = _activity_score("coach", {}, 0)
    assert score == 0.3


def test_activity_moderate_with_some_usage():
    """Moderate usage gives a moderate activity score."""
    score = _activity_score("grammar", {"grammar": 3}, 10)
    assert score == 0.5


# ── Integration tests (get_recommendations) ────────────────────


def test_get_recommendations_returns_three():
    """get_recommendations returns exactly 3 recommendations."""
    recs = get_recommendations("test", "en", "ko")
    assert len(recs) == 3


def test_get_recommendations_sorted_by_score():
    """Recommendations are sorted by score descending."""
    recs = get_recommendations("test", "en", "ko")
    for i in range(len(recs) - 1):
        assert recs[i]["score"] >= recs[i + 1]["score"]


def test_get_recommendations_kpop_top_for_korean():
    """K-pop should be in the top 3 for Korean learners."""
    recs = get_recommendations("test", "en", "ko")
    ids = [r["id"] for r in recs]
    assert "kpop" in ids


def test_get_recommendations_has_required_keys():
    """Each recommendation has the required keys."""
    recs = get_recommendations("test", "en", "ko")
    for rec in recs:
        for key in ("id", "name", "description", "icon", "page", "score", "breakdown"):
            assert key in rec, f"Missing key: {key} in {rec['id']}"


def test_get_recommendations_custom_max():
    """max_results parameter limits the number of recommendations."""
    recs = get_recommendations("test", "en", "ko", max_results=2)
    assert len(recs) == 2


def test_get_recommendations_coach_top_for_translate_user():
    """A user who translates a lot (non-Korean learner) should get Coach as top recommendation."""
    recs = get_recommendations(
        "test",
        "en",
        "en",  # English learner → K-pop doesn't dominate
        mode_counts={"translate": 15, "grammar": 1},
    )
    assert recs[0]["id"] == "coach"


def test_get_recommendations_vocab_top_for_vocab_user():
    """A user with many saved vocab items (non-Korean learner) should get Vocab Builder."""
    recs = get_recommendations(
        "test",
        "en",
        "en",  # English learner → K-pop doesn't dominate
        mode_counts={"vocabulary": 5},
        vocab_item_count=15,
    )
    assert recs[0]["id"] == "vocab"


def test_score_breakdown_sums_to_total():
    """Breakdown sub-scores, when unweighted, correspond to the total score."""
    recs = get_recommendations("test", "en", "ko")
    for rec in recs:
        # The overall score is the sum of the weighted breakdown values
        total_parts = sum(rec["breakdown"].values())
        assert abs(total_parts - rec["score"]) < 0.01, (
            f"Breakdown {total_parts} != score {rec['score']} for {rec['id']}"
        )


def test_mode_counts_empty():
    """Empty mode_counts should not crash and return valid recommendations."""
    recs = get_recommendations("test", "en", "ko", mode_counts={})
    assert len(recs) == 3


def test_mode_counts_none():
    """None mode_counts should not crash."""
    recs = get_recommendations("test", "en", "ko", mode_counts=None)
    assert len(recs) == 3
