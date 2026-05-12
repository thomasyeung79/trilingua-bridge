import os
from typing import Dict, Any, Tuple, Optional

from langdetect import detect, DetectorFactory
from openai import OpenAI


DetectorFactory.seed = 0


# =========================
# OpenAI Client
# =========================

def get_openai_client() -> Optional[OpenAI]:
    """
    Get OpenAI client from environment or Streamlit secrets.
    """

    api_key = os.environ.get("OPENAI_API_KEY")

    try:
        import streamlit as st

        api_key = st.secrets.get("OPENAI_API_KEY") or api_key

    except Exception:
        pass

    if not api_key:
        return None

    return OpenAI(api_key=api_key)


# =========================
# OpenAI Wrapper
# =========================

def call_openai(
    messages,
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
) -> Tuple[str, Dict[str, Any]]:

    client = get_openai_client()

    if not client:
        mock_response = (
            "AI response (mock): "
            + (
                messages[-1].get("content", "")[:200]
                if messages
                else ""
            )
        )

        return mock_response, {
            "model": model,
            "prompt_tokens": None,
            "completion_tokens": None,
        }

    try:
        response = client.chat.completions.create(
            model=model or "gpt-4o-mini",
            temperature=temperature,
            messages=messages,
        )

        text = response.choices[0].message.content

        usage = {
            "model": getattr(response, "model", model),
            "prompt_tokens": (
                getattr(response.usage, "prompt_tokens", None)
                if hasattr(response, "usage")
                else None
            ),
            "completion_tokens": (
                getattr(response.usage, "completion_tokens", None)
                if hasattr(response, "usage")
                else None
            ),
        }

        return text, usage

    except Exception as e:
        return (
            f"AI error or network issue: {e}",
            {
                "model": model,
                "prompt_tokens": None,
                "completion_tokens": None,
            },
        )


# =========================
# Language Detection
# =========================

def detect_language(text: str) -> Optional[str]:

    try:
        code = detect(text)

        if code.startswith("zh"):
            return "zh"

        if code.startswith("ko"):
            return "ko"

        if code.startswith("en"):
            return "en"

        return None

    except Exception:
        return None


# =========================
# Persona Prompt
# =========================

def build_system_prompt(
    persona_profile: Dict[str, Any],
    native_lang: str,
    target_lang: str,
) -> str:

    style = persona_profile.get("style_hint", "")

    return (
        "You are an AI language and cross-cultural communication assistant. "
        f"Follow this style: {style} "
        f"Keep explanations/meta in the user's native language ({native_lang}); "
        f"produce examples and final rewrites in the target language ({target_lang}). "
        "Be concise, practical, and culturally aware."
    )


# =========================
# Translation
# =========================

def translate_text(
    text: str,
    source_lang: str,
    target_lang: str,
    native_lang: str,
    temperature: float,
    model: str,
    persona_profile: Dict[str, Any],
) -> Tuple[str, Dict[str, Any], Optional[str]]:

    detected = None

    if source_lang == "auto":
        detected = detect_language(text)

    actual_source = detected or source_lang

    system_prompt = build_system_prompt(
        persona_profile,
        native_lang,
        target_lang,
    )

    user_prompt = (
        f"Source language: {actual_source}. "
        f"Target language: {target_lang}. "
        f"Translate the message into {target_lang}. "
        f"Then give short helpful notes in {native_lang}.\n\n"
        f"Message:\n{text}"
    )

    output, usage = call_openai(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model=model,
        temperature=temperature,
    )

    if detected:
        usage["detected_lang"] = detected

    return output, usage, detected


# =========================
# Grammar Correction
# =========================

def correct_grammar(
    text: str,
    target_lang: str,
    native_lang: str,
    level: str,
    temperature: float,
    model: str,
    persona_profile: Dict[str, Any],
) -> Tuple[str, Dict[str, Any]]:

    system_prompt = build_system_prompt(
        persona_profile,
        native_lang,
        target_lang,
    )

    user_prompt = (
        f"Target language: {target_lang}. "
        f"Learner level: {level}. "
        f"Correct the grammar of the following text in {target_lang}. "
        f"Then explain the main issues in {native_lang}. "
        f"Provide 1-2 corrected examples in {target_lang}.\n\n"
        f"Text:\n{text}"
    )

    return call_openai(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model=model,
        temperature=temperature,
    )


# =========================
# Natural Expression
# =========================

def suggest_natural_expression(
    text: str,
    target_lang: str,
    native_lang: str,
    tone_preference: str,
    temperature: float,
    model: str,
    persona_profile: Dict[str, Any],
) -> Tuple[str, Dict[str, Any]]:

    system_prompt = build_system_prompt(
        persona_profile,
        native_lang,
        target_lang,
    )

    user_prompt = (
        f"Rewrite the text in natural {target_lang} "
        f"with a {tone_preference} tone. "
        f"Provide 2-3 options. "
        f"Add short notes in {native_lang} "
        f"explaining why they sound natural.\n\n"
        f"Text:\n{text}"
    )

    return call_openai(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model=model,
        temperature=temperature,
    )


# =========================
# Vocabulary Explanation
# =========================

def explain_vocabulary(
    text: str,
    target_lang: str,
    native_lang: str,
    max_items: int,
    temperature: float,
    model: str,
    persona_profile: Dict[str, Any],
) -> Tuple[str, Dict[str, Any]]:

    system_prompt = build_system_prompt(
        persona_profile,
        native_lang,
        target_lang,
    )

    user_prompt = (
        f"Extract up to {max_items} important vocabulary items "
        f"from the text. "
        f"For each item provide:\n"
        f"- Original term\n"
        f"- Meaning in {native_lang}\n"
        f"- One example sentence in {target_lang}\n\n"
        f"Text:\n{text}"
    )

    return call_openai(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model=model,
        temperature=temperature,
    )


# =========================
# Tone Analysis
# =========================

def analyze_tone(
    text: str,
    lang: str,
    native_lang: str,
    temperature: float,
    model: str,
    persona_profile: Dict[str, Any],
) -> Tuple[str, Dict[str, Any]]:

    system_prompt = build_system_prompt(
        persona_profile,
        native_lang,
        lang,
    )

    user_prompt = (
        f"Analyze the tone of the following {lang} text. "
        f"Describe tone, formality, and cultural cues in {native_lang}. "
        f"If useful, suggest a small rewrite.\n\n"
        f"Text:\n{text}"
    )

    return call_openai(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model=model,
        temperature=temperature,
    )


# =========================
# Chat Reply Assistant
# =========================

def chat_reply_assistant(
    text: str,
    source_lang: str,
    target_lang: str,
    native_lang: str,
    temperature: float,
    model: str,
    persona_profile: Dict[str, Any],
) -> Tuple[str, Dict[str, Any], Optional[str]]:

    detected = None

    if source_lang == "auto":
        detected = detect_language(text)

    actual_source = detected or source_lang

    system_prompt = build_system_prompt(
        persona_profile,
        native_lang,
        target_lang,
    )

    user_prompt = (
        f"The user received a message in {actual_source}. "
        f"Suggest 2-3 natural replies in {target_lang}. "
        f"Add short notes in {native_lang} "
        f"about tone and intent.\n\n"
        f"Received message:\n{text}"
    )

    output, usage = call_openai(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model=model,
        temperature=temperature,
    )

    if detected:
        usage["detected_lang"] = detected

    return output, usage, detected