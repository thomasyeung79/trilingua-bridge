import json
import os
from typing import Dict, Any, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

Lang = str


# =========================
# API Keys
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


# =========================
# Helpers
# =========================

def usage_from_response(response, provider: str) -> Dict[str, Any]:
    usage = getattr(response, "usage", None)

    model = getattr(response, "model", None)

    if provider == "deepseek" and model:
        model = f"deepseek/{model}"

    if provider == "openai" and model:
        model = f"openai/{model}"

    return {
        "model": model,
        "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
        "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
        "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
        "provider": provider,
    }


def mock_usage(model: str) -> Dict[str, Any]:
    return {
        "model": model or "mock",
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
        "provider": "mock",
    }


def safe_json_loads(text: str) -> Dict[str, Any]:
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
        return {"result": data}
    except Exception:
        return {}


def persona_instructions(persona_profile: Dict[str, Any]) -> str:
    if not persona_profile:
        return ""

    return (
        f"Persona: {persona_profile.get('code', '')}. "
        f"Style: {persona_profile.get('style', persona_profile.get('style_hint', ''))}."
    )


def language_rules() -> str:
    return (
        "Language code rules:\n"
        "- zh = Simplified Chinese / Mandarin Chinese\n"
        "- yue = Traditional Chinese / Cantonese\n"
        "- ko = Korean\n"
        "- en = English\n\n"
        "Output rules:\n"
        "- If target_lang is zh, output in Simplified Chinese only.\n"
        "- If target_lang is yue, output in Traditional Chinese, with Cantonese expressions when appropriate.\n"
        "- If target_lang is ko, output in Korean only.\n"
        "- If target_lang is en, output in English only.\n"
        "- Do not output English unless target_lang or output_lang is en.\n"
    )


def get_output_rule(lang: str) -> str:
    rules = {
        "zh": "Use Simplified Chinese only. Do not output English.",
        "yue": "Use Traditional Chinese and Cantonese-style wording when appropriate. Do not output English.",
        "ko": "Use Korean only. Do not output English.",
        "en": "Use English only.",
    }

    return rules.get(lang, "Use the requested output language.")


def get_default_model() -> str:
    return (
        get_secret_value("OPENAI_MODEL")
        or os.environ.get("OPENAI_MODEL")
        or "gpt-4o-mini"
    )


def get_deepseek_model() -> str:
    return (
        get_secret_value("DEEPSEEK_MODEL")
        or os.environ.get("DEEPSEEK_MODEL")
        or "deepseek-chat"
    )


# =========================
# AI Provider Calls
# =========================

def call_json_chat(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.4,
) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
    openai_model = model or get_default_model()

    openai_client = get_openai_client()

    if openai_client:
        try:
            response = openai_client.chat.completions.create(
                model=openai_model,
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

        except Exception:
            pass

    deepseek_client = get_deepseek_client()

    if deepseek_client:
        try:
            deepseek_model = get_deepseek_model()

            response = deepseek_client.chat.completions.create(
                model=deepseek_model,
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
            return (
                {
                    "mock": True,
                    "message": f"Both OpenAI and DeepSeek failed. Last error: {e}",
                },
                mock_usage(model),
                "",
            )

    return (
        {
            "mock": True,
            "message": "No available AI provider. Please set OPENAI_API_KEY or DEEPSEEK_API_KEY.",
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
    openai_model = model or get_default_model()
    openai_client = get_openai_client()

    if openai_client:
        try:
            response = openai_client.chat.completions.create(
                model=openai_model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            content = response.choices[0].message.content or ""
            return content, usage_from_response(response, "openai")

        except Exception:
            pass

    deepseek_client = get_deepseek_client()

    if deepseek_client:
        try:
            deepseek_model = get_deepseek_model()

            response = deepseek_client.chat.completions.create(
                model=deepseek_model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            content = response.choices[0].message.content or ""
            return content, usage_from_response(response, "deepseek")

        except Exception as e:
            return f"Both OpenAI and DeepSeek failed. Last error: {e}", mock_usage(model)

    return (
        "No available AI provider. Please set OPENAI_API_KEY or DEEPSEEK_API_KEY.",
        mock_usage(model),
    )


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

    system_prompt = (
        "You are a helpful cross-cultural translator. "
        "Keep tone natural, preserve meaning and intent. "
        f"{language_rules()} "
        f"{persona_instructions(persona_profile)}"
    )

    detect_source = source_lang == "auto"

    prompt = {
        "task": "translate",
        "detect_source": detect_source,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "native_lang": native_lang,
        "text": text,
        "important_output_rule": get_output_rule(target_lang),
        "return_json_schema": {
            "type": "object",
            "properties": {
                "detected_lang": {"type": ["string", "null"]},
                "translation": {"type": "string"},
            },
            "required": ["translation"],
        },
    }

    data, usage, raw_content = call_json_chat(
        model=model,
        system_prompt=system_prompt,
        user_prompt=json.dumps(prompt, ensure_ascii=False),
        temperature=temperature,
    )

    if data.get("mock"):
        return data["message"], usage, None

    detected = data.get("detected_lang")
    output = data.get("translation") or raw_content

    return output.strip(), usage, detected


# =========================
# Grammar Correction
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
        "You are a grammar coach. "
        f"{language_rules()} "
        f"Target language: {target_lang}. "
        f"Learner level: {level}. "
        f"Explain notes in {native_lang}. "
        f"{get_output_rule(native_lang)} "
        f"{persona_instructions(persona_profile)}"
    )

    prompt = {
        "task": "grammar_correction",
        "target_lang": target_lang,
        "native_lang": native_lang,
        "level": level,
        "text": text,
        "important_output_rule": get_output_rule(native_lang),
        "return_json_schema": {
            "type": "object",
            "properties": {
                "clean": {"type": "string"},
                "notes": {"type": "string"},
                "examples": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["clean"],
        },
    }

    data, usage, raw_content = call_json_chat(
        model=model,
        system_prompt=system_prompt,
        user_prompt=json.dumps(prompt, ensure_ascii=False),
        temperature=temperature,
    )

    if not data:
        data = {"clean": raw_content}

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
        f"{language_rules()} "
        f"Target language: {target_lang}. "
        f"Desired tone: {tone_preference}. "
        f"Explain notes in {native_lang}. "
        f"{get_output_rule(native_lang)} "
        f"{persona_instructions(persona_profile)}"
    )

    prompt = {
        "task": "natural_expression",
        "target_lang": target_lang,
        "native_lang": native_lang,
        "tone": tone_preference,
        "text": text,
        "important_output_rule": get_output_rule(native_lang),
        "return_json_schema": {
            "type": "object",
            "properties": {
                "suggestions": {"type": "array", "items": {"type": "string"}},
                "tone_notes": {"type": "string"},
                "better_version": {"type": "string"},
            },
            "required": ["better_version"],
        },
    }

    data, usage, raw_content = call_json_chat(
        model=model,
        system_prompt=system_prompt,
        user_prompt=json.dumps(prompt, ensure_ascii=False),
        temperature=temperature,
    )

    if not data:
        data = {"better_version": raw_content}

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
        "You are a concise vocabulary explainer for language learners. "
        f"{language_rules()} "
        f"Explain in {native_lang}. "
        f"{get_output_rule(native_lang)} "
        f"{persona_instructions(persona_profile)}"
    )

    prompt = {
        "task": "vocabulary_explain",
        "target_lang": target_lang,
        "native_lang": native_lang,
        "max_items": max_items,
        "text": text,
        "important_output_rule": get_output_rule(native_lang),
        "return_json_schema": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "term": {"type": "string"},
                            "meaning": {"type": "string"},
                            "example": {"type": "string"},
                        },
                        "required": ["term", "meaning"],
                    },
                }
            },
            "required": ["items"],
        },
    }

    data, usage, raw_content = call_json_chat(
        model=model,
        system_prompt=system_prompt,
        user_prompt=json.dumps(prompt, ensure_ascii=False),
        temperature=temperature,
    )

    if not data:
        data = {"items": [], "raw": raw_content}

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
        "You are a tone and intent analyzer. "
        f"{language_rules()} "
        f"Text language: {lang}. "
        f"Explain findings in {native_lang}. "
        f"{get_output_rule(native_lang)} "
        f"{persona_instructions(persona_profile)}"
    )

    prompt = {
        "task": "tone_analysis",
        "lang": lang,
        "native_lang": native_lang,
        "text": text,
        "important_output_rule": get_output_rule(native_lang),
        "return_json_schema": {
            "type": "object",
            "properties": {
                "tone_summary": {"type": "string"},
                "intent": {"type": "string"},
                "tips": {"type": "string"},
            },
            "required": ["tone_summary"],
        },
    }

    data, usage, raw_content = call_json_chat(
        model=model,
        system_prompt=system_prompt,
        user_prompt=json.dumps(prompt, ensure_ascii=False),
        temperature=temperature,
    )

    if not data:
        data = {"tone_summary": raw_content}

    return data, usage


# =========================
# Chat Reply Assistant - Legacy
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
        "You are a helpful bilingual communication assistant. "
        f"{language_rules()} "
        f"Generate a natural reply in {target_lang}. "
        f"Explain only if needed in {native_lang}. "
        f"{get_output_rule(target_lang)} "
        f"{persona_instructions(persona_profile)}"
    )

    detect_source = source_lang == "auto"

    prompt = {
        "task": "chat_reply",
        "detect_source": detect_source,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "native_lang": native_lang,
        "text": text,
        "important_output_rule": get_output_rule(target_lang),
        "return_json_schema": {
            "type": "object",
            "properties": {
                "detected_lang": {"type": ["string", "null"]},
                "reply": {"type": "string"},
            },
            "required": ["reply"],
        },
    }

    data, usage, raw_content = call_json_chat(
        model=model,
        system_prompt=system_prompt,
        user_prompt=json.dumps(prompt, ensure_ascii=False),
        temperature=temperature,
    )

    if data.get("mock"):
        return data["message"], usage, None

    return data.get("reply", raw_content), usage, data.get("detected_lang")


# =========================
# Advanced AI Chat Coach
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

    system_prompt = (
        "You are an advanced AI chat coach. "
        f"{language_rules()} "
        "Provide exactly 3 concise, natural replies in the target language. "
        "Also include tone notes, cultural notes, the best recommended reply, and a brief reason. "
        "Make the output practical for real messaging apps. "
        f"Replies must be in {target_lang}. "
        f"Explanations must be in {native_lang}. "
        f"{get_output_rule(native_lang)} "
        f"{persona_instructions(persona_profile)}"
    )

    detect_source = source_lang == "auto"

    prompt = {
        "task": "advanced_chat_coach",
        "detect_source": detect_source,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "native_lang": native_lang,
        "source_text": text,
        "reply_style": reply_style,
        "important_output_rule": (
            f"Reply options must be in {target_lang}. "
            f"Tone notes, cultural notes and reason must be in {native_lang}. "
            "Do not use English unless target_lang or native_lang is en."
        ),
        "constraints": {
            "num_replies": 3,
            "max_length": "one or two short sentences each",
        },
        "return_json_schema": {
            "type": "object",
            "properties": {
                "detected_lang": {"type": ["string", "null"]},
                "reply_options": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "naturalness_score": {"type": "number"},
                            "tone": {"type": "string"},
                        },
                        "required": ["text"],
                    },
                },
                "tone_notes": {"type": "string"},
                "cultural_notes": {"type": "string"},
                "suggested_best_reply": {"type": "string"},
                "reason": {"type": "string"},
                "pronunciation_guide": {
                    "type": "object",
                    "properties": {
                        "lang": {"type": "string"},
                        "text": {"type": "string"},
                    },
                },
            },
            "required": ["reply_options", "suggested_best_reply"],
        },
    }

    data, usage, raw_content = call_json_chat(
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
        return data, usage, None

    if not data:
        data = {
            "reply_options": [{"text": raw_content}],
            "suggested_best_reply": raw_content,
        }

    detected = data.get("detected_lang")
    return data, usage, detected


# =========================
# Media Context Explain
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

    system_prompt = (
        "You are a media and pop-culture explainer. "
        f"{language_rules()} "
        "You can explain K-pop lyrics, Korean drama dialogue, Cantonese drama dialogue, "
        "Chinese drama dialogue, English TV/movie dialogue, internet slang, and pop culture expressions. "
        "Explain in a way helpful for language learners and cross-cultural communication. "
        f"All explanations must be in {native_lang}. "
        f"{get_output_rule(native_lang)} "
        f"{persona_instructions(persona_profile)}"
    )

    detect_source = source_lang == "auto"

    prompt = {
        "task": "media_context",
        "detect_source": detect_source,
        "source_lang": source_lang,
        "context_type": context_type,
        "text": text,
        "output_lang": native_lang,
        "important_output_rule": get_output_rule(native_lang),
        "return_json_schema": {
            "type": "object",
            "properties": {
                "detected_lang": {"type": ["string", "null"]},
                "clean_translation": {"type": "string"},
                "key_phrases": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "phrase": {"type": "string"},
                            "meaning": {"type": "string"},
                            "note": {"type": "string"},
                        },
                        "required": ["phrase", "meaning"],
                    },
                },
                "slang_pop_culture": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "term": {"type": "string"},
                            "origin": {"type": "string"},
                            "note": {"type": "string"},
                        },
                        "required": ["term"],
                    },
                },
                "tone_notes": {"type": "string"},
                "cultural_notes": {"type": "string"},
                "summary": {"type": "string"},
                "recommended_understanding": {"type": "string"},
                "pronunciation_guide": {
                    "type": "object",
                    "properties": {
                        "lang": {"type": "string"},
                        "text": {"type": "string"},
                    },
                },
            },
            "required": ["clean_translation"],
        },
    }

    data, usage, raw_content = call_json_chat(
        model=model,
        system_prompt=system_prompt,
        user_prompt=json.dumps(prompt, ensure_ascii=False),
        temperature=temperature,
    )

    if data.get("mock"):
        data = {
            "clean_translation": "Mock explanation: no available AI provider.",
            "key_phrases": [],
            "slang_pop_culture": [],
            "summary": "Mock media context explanation.",
            "recommended_understanding": "Set OPENAI_API_KEY or DEEPSEEK_API_KEY to enable real AI output.",
        }
        return data, usage, None

    if not data:
        data = {"clean_translation": raw_content}

    detected = data.get("detected_lang")
    return data, usage, detected
