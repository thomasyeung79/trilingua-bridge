"""Tests for i18n consistency across all UI languages."""

from ui_helper import TEXTS, UI_LANGS


LOCALES = UI_LANGS  # ["en", "zh", "ko", "yue", "ja"]


def test_all_locales_have_provider_auto_option():
    """provider_auto_option must mention all three providers in order."""
    for lang in LOCALES:
        text = TEXTS[lang].get("provider_auto_option", "")
        assert "OpenAI" in text, f"{lang}: missing OpenAI"
        assert "Anthropic" in text or "Anthropic" in text, f"{lang}: missing Anthropic"
        assert "DeepSeek" in text, f"{lang}: missing DeepSeek"


def test_japanese_provider_auto_option_has_correct_order():
    """Japanese fallback text must show correct order."""
    text = TEXTS["ja"]["provider_auto_option"]
    assert "OpenAI" in text
    assert "Anthropic" in text
    assert "DeepSeek" in text
    # Verify order: OpenAI before Anthropic before DeepSeek
    assert text.index("OpenAI") < text.index("Anthropic") < text.index("DeepSeek")


def test_all_locales_have_region_jp():
    """region_jp must exist in every UI language."""
    for lang in LOCALES:
        assert "region_jp" in TEXTS[lang], f"{lang}: missing region_jp"
        assert TEXTS[lang]["region_jp"], f"{lang}: region_jp is empty"


def test_japanese_provider_auto_option_meaningful():
    """Japanese fallback text must be non-empty and not just English."""
    text = TEXTS["ja"]["provider_auto_option"]
    assert len(text) > 10
    # Should contain Japanese characters
    assert any(ord(c) > 0x3000 for c in text), "Expected Japanese characters"


def test_all_locales_have_new_conversation():
    """new_conversation must exist in every UI language."""
    for lang in LOCALES:
        assert "new_conversation" in TEXTS[lang], f"{lang}: missing new_conversation"
        assert len(TEXTS[lang]["new_conversation"]) > 0, f"{lang}: new_conversation is empty"


def test_all_locales_have_conversation_reset():
    """conversation_reset must exist in every UI language."""
    for lang in LOCALES:
        assert "conversation_reset" in TEXTS[lang], f"{lang}: missing conversation_reset"
        assert len(TEXTS[lang]["conversation_reset"]) > 0, f"{lang}: conversation_reset is empty"


def test_auto_not_in_study_lang_codes():
    """Auto-detect must NOT be in the study language codes list."""
    from ui_helper import STUDY_LANG_CODES
    assert "auto" not in STUDY_LANG_CODES


def test_all_locales_have_swap_unavailable_auto():
    """swap_unavailable_auto must exist in every UI language."""
    for lang in LOCALES:
        assert "swap_unavailable_auto" in TEXTS[lang], f"{lang}: missing swap_unavailable_auto"
        assert len(TEXTS[lang]["swap_unavailable_auto"]) > 0, f"{lang}: swap_unavailable_auto is empty"
