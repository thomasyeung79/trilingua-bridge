import os
import json
import base64
from typing import Dict, Any, List, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

Lang = str


# =========================
# Secrets / Clients
# =========================

def get_secret_value(key: str) -> Optional[str]:
    value = os.environ.get(key)

    try:
        import streamlit as st

        value = st.secrets.get(key) or value
    except Exception:
        pass

    return value


def get_openai_client() -> Optional[OpenAI]:
    api_key = get_secret_value("OPENAI_API_KEY")

    if not api_key:
        return None

    return OpenAI(api_key=api_key)


def get_deepseek_client() -> Optional[OpenAI]:
    api_key = get_secret_value("DEEPSEEK_API_KEY")

    if not api_key:
        return None

    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )


def get_openai_model(model: Optional[str] = None) -> str:
    return (
        model
        or get_secret_value("OPENAI_MODEL")
        or "gpt-4o-mini"
    )


def get_deepseek_model() -> str:
    return (
        get_secret_value("DEEPSEEK_MODEL")
        or "deepseek-chat"
    )


# =========================
# Common Helpers
# =========================

def safe_json_loads(text: str) -> Dict[str, Any]:
    try:
        data = json.loads(text)

        if isinstance(data, dict):
            return data

        return {"result": data}

    except Exception:
        return {}


def usage_from_response(response, provider: str) -> Dict[str, Any]:
    usage = getattr(response, "usage", None)
    model = getattr(response, "model", None)

    if model:
        model = f"{provider}/{model}"

    return {
        "model": model or provider,
        "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
        "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
        "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
        "provider": provider,
    }


def mock_usage(model: Optional[str] = None) -> Dict[str, Any]:
    return {
        "model": model or "mock",
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
        "provider": "mock",
    }


def language_rules() -> str:
    return """
Language code rules:
- zh = Simplified Chinese / Mandarin Chinese
- yue = Traditional Chinese / Cantonese
- ko = Korean
- en = English

Output rules:
- If target_lang is zh, output Simplified Chinese.
- If target_lang is yue, output Traditional Chinese with Cantonese wording when appropriate.
- If target_lang is ko, output Korean.
- If target_lang is en, output English.
- Do not output English unless target_lang or output_lang is en.
"""


def get_output_rule(lang: str) -> str:
    rules = {
        "zh": "Use Simplified Chinese only. Do not output English.",
        "yue": "Use Traditional Chinese / Cantonese-style wording. Do not output English.",
        "ko": "Use Korean only. Do not output English.",
        "en": "Use English only.",
    }

    return rules.get(lang, "Use the requested output language.")


def persona_instructions(persona_profile: Dict[str, Any]) -> str:
    if not persona_profile:
        return ""

    role = persona_profile.get("role", "")
    style = persona_profile.get("style_hint", "")
    region = persona_profile.get("region_guidelines", "")

    return f"""
Persona:
{role}

Style:
{style}

Regional / cultural guidelines:
{region}
""".strip()


# =========================
# Provider Calls
# =========================

def call_json_chat(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.4,
) -> Tuple[Dict[str, Any], Dict[str, Any], str]:

    system_prompt = (
        system_prompt
        + "\nReturn valid JSON only. Do not include markdown."
    )

    openai_error = ""

    openai_client = get_openai_client()

    if openai_client:
        try:
            response = openai_client.chat.completions.create(
                model=get_openai_model(model),
                temperature=temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            content = response.choices[0].message.content or ""
            data = safe_json_loads(content)

            return data, usage_from_response(response, "openai"), content

        except Exception as e:
            openai_error = str(e)

    else:
        openai_error = "OpenAI API key is missing."

    deepseek_client = get_deepseek_client()

    if deepseek_client:
        try:
            response = deepseek_client.chat.completions.create(
                model=get_deepseek_model(),
                temperature=temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            content = response.choices[0].message.content or ""
            data = safe_json_loads(content)

            return data, usage_from_response(response, "deepseek"), content

        except Exception as e:
            deepseek_error = str(e)

            return (
                {
                    "mock": True,
                    "message": (
                        "Both OpenAI and DeepSeek failed.\n\n"
                        f"OpenAI Error: {openai_error}\n"
                        f"DeepSeek Error: {deepseek_error}"
                    ),
                },
                mock_usage(model),
                "",
            )

    return (
        {
            "mock": True,
            "message": (
                "No available AI provider. "
                "Please set OPENAI_API_KEY or DEEPSEEK_API_KEY."
            ),
        },
        mock_usage(model),
        "",
    )


def call_plain_chat(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.4,
) -> Tuple[str, Dict[str, Any]]:

    openai_error = ""

    openai_client = get_openai_client()

    if openai_client:
        try:
            response = openai_client.chat.completions.create(
                model=get_openai_model(model),
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            content = response.choices[0].message.content or ""
            return content, usage_from_response(response, "openai")

        except Exception as e:
            openai_error = str(e)

    else:
        openai_error = "OpenAI API key is missing."

    deepseek_client = get_deepseek_client()

    if deepseek_client:
        try:
            response = deepseek_client.chat.completions.create(
                model=get_deepseek_model(),
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            content = response.choices[0].message.content or ""
            return content, usage_from_response(response, "deepseek")

        except Exception as e:
            return (
                f"Both OpenAI and DeepSeek failed.\nOpenAI: {openai_error}\nDeepSeek: {e}",
                mock_usage(model),
            )

    return (
        "No available AI provider. Please set OPENAI_API_KEY or DEEPSEEK_API_KEY.",
        mock_usage(model),
    )


# =========================
# Language Detection
# =========================

def detect_language_simple(
    text: str,
    model: str,
    temperature: float,
    persona_profile: Dict[str, Any],
) -> Optional[str]:

    system_prompt = (
        "You are a strict language detector. "
        "Return JSON only: {\"lang\":\"zh|yue|ko|en\"}."
    )

    prompt = {
        "task": "detect_language",
        "allowed_codes": ["zh", "yue", "ko", "en"],
        "text": text,
        "hint": "If the text is clearly Cantonese or Traditional Chinese Cantonese wording, return yue.",
    }

    data, _, _ = call_json_chat(
        model=model,
        system_prompt=system_prompt,
        user_prompt=json.dumps(prompt, ensure_ascii=False),
        temperature=min(temperature, 0.2),
    )

    lang = data.get("lang")

    if lang in ("zh", "yue", "ko", "en"):
        return lang

    return None


# =========================
# Translation
# =========================

def translate_text(
    text: str,
    source_lang: Lang,
    target_lang: Lang,
    native_lang: Lang,
    temperature: float,
    model: str,
    persona_profile: Dict[str, Any],
) -> Tuple[str, Dict[str, Any], Optional[str]]:

    detected = None

    if source_lang == "auto":
        detected = detect_language_simple(
            text=text,
            model=model,
            temperature=temperature,
            persona_profile=persona_profile,
        )

    system_prompt = (
        "You are a helpful cross-cultural translator. "
        "Translate naturally and preserve tone, intent, and cultural meaning.\n"
        f"{language_rules()}\n"
        f"{persona_instructions(persona_profile)}"
    )

    prompt = {
        "task": "translate",
        "source_lang": detected or source_lang,
        "target_lang": target_lang,
        "native_lang": native_lang,
        "text": text,
        "important_output_rule": get_output_rule(target_lang),
        "return_schema": {
            "detected_lang": "string or null",
            "translation": "string",
        },
    }

    data, usage, raw = call_json_chat(
        model=model,
        system_prompt=system_prompt,
        user_prompt=json.dumps(prompt, ensure_ascii=False),
        temperature=temperature,
    )

    if data.get("mock"):
        return data["message"], usage, detected

    return data.get("translation", raw).strip(), usage, data.get("detected_lang") or detected


# =========================
# Grammar
# =========================

def correct_grammar(
    text: str,
    target_lang: Lang,
    native_lang: Lang,
    level: str,
    temperature: float,
    model: str,
    persona_profile: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:

    system_prompt = (
        "You are a grammar coach for multilingual learners.\n"
        f"{language_rules()}\n"
        f"Explain in {native_lang}. {get_output_rule(native_lang)}\n"
        f"{persona_instructions(persona_profile)}"
    )

    prompt = {
        "task": "grammar_correction",
        "target_lang": target_lang,
        "native_lang": native_lang,
        "level": level,
        "text": text,
        "return_schema": {
            "clean": "corrected version",
            "notes": "brief explanation",
            "examples": ["example 1", "example 2"],
        },
    }

    data, usage, raw = call_json_chat(
        model=model,
        system_prompt=system_prompt,
        user_prompt=json.dumps(prompt, ensure_ascii=False),
        temperature=temperature,
    )

    if not data:
        data = {"clean": raw}

    return data, usage


# =========================
# Natural Expression
# =========================

def suggest_natural_expression(
    text: str,
    target_lang: Lang,
    native_lang: Lang,
    tone_preference: str,
    temperature: float,
    model: str,
    persona_profile: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:

    system_prompt = (
        "You are a natural expression coach. "
        "Improve the user's sentence so it sounds natural.\n"
        f"{language_rules()}\n"
        f"Explain in {native_lang}. {get_output_rule(native_lang)}\n"
        f"{persona_instructions(persona_profile)}"
    )

    prompt = {
        "task": "natural_expression",
        "target_lang": target_lang,
        "native_lang": native_lang,
        "tone_preference": tone_preference,
        "text": text,
        "return_schema": {
            "better_version": "string",
            "suggestions": ["string"],
            "tone_notes": "string",
            "naturalness_score": "1-10",
            "reason": "string",
        },
    }

    data, usage, raw = call_json_chat(
        model=model,
        system_prompt=system_prompt,
        user_prompt=json.dumps(prompt, ensure_ascii=False),
        temperature=temperature,
    )

    if not data:
        data = {"better_version": raw}

    return data, usage


# =========================
# Vocabulary
# =========================

def explain_vocabulary(
    text: str,
    target_lang: Lang,
    native_lang: Lang,
    max_items: int,
    temperature: float,
    model: str,
    persona_profile: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:

    system_prompt = (
        "You are a vocabulary and phrase explainer.\n"
        f"{language_rules()}\n"
        f"Explain in {native_lang}. {get_output_rule(native_lang)}\n"
        f"{persona_instructions(persona_profile)}"
    )

    prompt = {
        "task": "vocabulary_explanation",
        "target_lang": target_lang,
        "native_lang": native_lang,
        "max_items": max_items,
        "text": text,
        "return_schema": {
            "items": [
                {
                    "term": "word or phrase",
                    "meaning": "meaning",
                    "example": "example sentence",
                }
            ]
        },
    }

    data, usage, raw = call_json_chat(
        model=model,
        system_prompt=system_prompt,
        user_prompt=json.dumps(prompt, ensure_ascii=False),
        temperature=temperature,
    )

    if not data:
        data = {"items": [], "raw": raw}

    return data, usage


# =========================
# Tone Analysis
# =========================

def analyze_tone(
    text: str,
    lang: Lang,
    native_lang: Lang,
    temperature: float,
    model: str,
    persona_profile: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:

    system_prompt = (
        "You are a tone and intent analyzer.\n"
        f"{language_rules()}\n"
        f"Explain in {native_lang}. {get_output_rule(native_lang)}\n"
        f"{persona_instructions(persona_profile)}"
    )

    prompt = {
        "task": "tone_analysis",
        "lang": lang,
        "native_lang": native_lang,
        "text": text,
        "return_schema": {
            "tone_summary": "string",
            "intent": "string",
            "tips": "string",
        },
    }

    data, usage, raw = call_json_chat(
        model=model,
        system_prompt=system_prompt,
        user_prompt=json.dumps(prompt, ensure_ascii=False),
        temperature=temperature,
    )

    if not data:
        data = {"tone_summary": raw}

    return data, usage


# =========================
# Chat Reply Assistant
# =========================

def chat_reply_assistant(
    text: str,
    source_lang: Lang,
    target_lang: Lang,
    native_lang: Lang,
    temperature: float,
    model: str,
    persona_profile: Dict[str, Any],
) -> Tuple[str, Dict[str, Any], Optional[str]]:

    system_prompt = (
        "You are a helpful chat reply assistant.\n"
        f"{language_rules()}\n"
        f"Reply in {target_lang}. {get_output_rule(target_lang)}\n"
        f"{persona_instructions(persona_profile)}"
    )

    detected = None

    if source_lang == "auto":
        detected = detect_language_simple(text, model, temperature, persona_profile)

    prompt = {
        "task": "chat_reply",
        "source_lang": detected or source_lang,
        "target_lang": target_lang,
        "native_lang": native_lang,
        "text": text,
        "return_schema": {
            "detected_lang": "string or null",
            "reply": "string",
        },
    }

    data, usage, raw = call_json_chat(
        model=model,
        system_prompt=system_prompt,
        user_prompt=json.dumps(prompt, ensure_ascii=False),
        temperature=temperature,
    )

    if data.get("mock"):
        return data["message"], usage, detected

    return data.get("reply", raw), usage, data.get("detected_lang") or detected


# =========================
# Advanced Chat Coach
# =========================

def chat_reply_coach_advanced(
    text: str,
    source_lang: Lang,
    target_lang: Lang,
    native_lang: Lang,
    reply_style: str,
    temperature: float,
    model: str,
    persona_profile: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any], Optional[str]]:

    detected = None

    if source_lang == "auto":
        detected = detect_language_simple(text, model, temperature, persona_profile)

    system_prompt = (
        "You are an advanced AI cross-cultural chat coach.\n"
        "Provide exactly 3 practical reply options.\n"
        "Reply options must be in target_lang.\n"
        "Explanations must be in native_lang.\n"
        f"{language_rules()}\n"
        f"{persona_instructions(persona_profile)}"
    )

    prompt = {
        "task": "advanced_chat_coach",
        "source_text": text,
        "source_lang": detected or source_lang,
        "target_lang": target_lang,
        "native_lang": native_lang,
        "reply_style": reply_style,
        "important_output_rule": (
            f"Reply options must be in {target_lang}. "
            f"Tone notes, cultural notes and reason must be in {native_lang}. "
            "Do not use English unless target_lang or native_lang is en."
        ),
        "return_schema": {
            "detected_lang": "string or null",
            "reply_options": [
                {
                    "text": "reply text",
                    "naturalness_score": 1,
                    "tone": "tone description",
                }
            ],
            "tone_notes": "string",
            "cultural_notes": "string",
            "suggested_best_reply": "string",
            "reason": "string",
            "pronunciation_guide": {
                "lang": "string",
                "text": "string",
            },
        },
    }

    data, usage, raw = call_json_chat(
        model=model,
        system_prompt=system_prompt,
        user_prompt=json.dumps(prompt, ensure_ascii=False),
        temperature=temperature,
    )

    if data.get("mock"):
        data = {
            "reply_options": [
                {
                    "text": "Mock reply option 1",
                    "naturalness_score": 8,
                    "tone": reply_style,
                },
                {
                    "text": "Mock reply option 2",
                    "naturalness_score": 8,
                    "tone": reply_style,
                },
                {
                    "text": "Mock reply option 3",
                    "naturalness_score": 8,
                    "tone": reply_style,
                },
            ],
            "tone_notes": "Mock tone notes.",
            "cultural_notes": "Mock cultural notes.",
            "suggested_best_reply": "Mock reply option 1",
            "reason": "No available AI provider.",
        }

        return data, usage, detected

    if not data:
        data = {
            "reply_options": [{"text": raw}],
            "suggested_best_reply": raw,
        }

    return data, usage, data.get("detected_lang") or detected


# =========================
# Media Context
# =========================

def media_context_explain(
    text: str,
    source_lang: Lang,
    native_lang: Lang,
    context_type: str,
    temperature: float,
    model: str,
    persona_profile: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any], Optional[str]]:

    detected = None

    if source_lang == "auto":
        detected = detect_language_simple(text, model, temperature, persona_profile)

    system_prompt = (
        "You are a media and pop-culture context explainer.\n"
        "You explain lyrics, drama dialogue, internet slang and cultural context.\n"
        f"{language_rules()}\n"
        f"Explain in {native_lang}. {get_output_rule(native_lang)}\n"
        f"{persona_instructions(persona_profile)}"
    )

    prompt = {
        "task": "media_context",
        "source_lang": detected or source_lang,
        "native_lang": native_lang,
        "context_type": context_type,
        "text": text,
        "return_schema": {
            "detected_lang": "string or null",
            "clean_translation": "string",
            "key_phrases": [
                {
                    "phrase": "string",
                    "meaning": "string",
                    "note": "string",
                }
            ],
            "slang_pop_culture": [
                {
                    "term": "string",
                    "origin": "string",
                    "note": "string",
                }
            ],
            "tone_notes": "string",
            "cultural_notes": "string",
            "summary": "string",
            "recommended_understanding": "string",
            "pronunciation_guide": {
                "lang": "string",
                "text": "string",
            },
        },
    }

    data, usage, raw = call_json_chat(
        model=model,
        system_prompt=system_prompt,
        user_prompt=json.dumps(prompt, ensure_ascii=False),
        temperature=temperature,
    )

    if not data:
        data = {"clean_translation": raw}

    return data, usage, data.get("detected_lang") or detected


# =========================
# Screenshot Chat Analysis
# =========================

def analyze_screenshot_chat(
    image_bytes: bytes,
    image_name: str,
    assumed_lang: Optional[str],
    native_lang: str,
    target_lang: str,
    region_mode: str,
    temperature: float,
    model: str,
    persona_profile: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any], Optional[str]]:

    openai_client = get_openai_client()

    if not openai_client:
        return (
            {
                "summary": "Screenshot analysis requires OpenAI vision support.",
                "tone_notes": "DeepSeek fallback is not used for image analysis in this version.",
                "cultural_notes": "Please set OPENAI_API_KEY.",
                "reply_options": [],
            },
            mock_usage(model),
            assumed_lang,
        )

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    mime = "image/png"

    if image_name.lower().endswith(".jpg") or image_name.lower().endswith(".jpeg"):
        mime = "image/jpeg"
    elif image_name.lower().endswith(".webp"):
        mime = "image/webp"

    system_prompt = (
        "You are an AI chat screenshot analyst and cross-cultural communication coach.\n"
        f"{language_rules()}\n"
        f"Explain in {native_lang}. {get_output_rule(native_lang)}\n"
        "Analyze the screenshot carefully. Do not invent text that is not visible.\n"
        f"{persona_instructions(persona_profile)}\n"
        "Return valid JSON only. Do not include markdown."
    )

    user_text = {
        "task": "screenshot_chat_analysis",
        "assumed_lang": assumed_lang,
        "native_lang": native_lang,
        "target_lang": target_lang,
        "region_mode": region_mode,
        "return_schema": {
            "detected_lang": "string or null",
            "visible_text_summary": "string",
            "summary": "string",
            "tone_notes": "string",
            "relationship_vibe": "string",
            "hidden_meaning": "string",
            "cultural_notes": "string",
            "reply_options": [
                {
                    "text": "string",
                    "naturalness_score": 1,
                    "tone": "string",
                }
            ],
            "suggested_best_reply": "string",
            "reason": "string",
        },
    }

    try:
        response = openai_client.chat.completions.create(
            model=get_openai_model(model),
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(user_text, ensure_ascii=False),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{image_b64}",
                            },
                        },
                    ],
                },
            ],
        )

        content = response.choices[0].message.content or ""
        data = safe_json_loads(content)

        if not data:
            data = {"summary": content}

        return data, usage_from_response(response, "openai"), data.get("detected_lang") or assumed_lang

    except Exception as e:
        return (
            {
                "summary": "Screenshot analysis failed.",
                "tone_notes": str(e),
                "reply_options": [],
            },
            mock_usage(model),
            assumed_lang,
        )
