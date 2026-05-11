import os
import json
import time
from typing import Dict, Tuple, Any, List
from openai import OpenAI

MODEL_DEFAULT = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

_client = None
def _client_singleton():
    global _client
    if _client is None:
        _client = OpenAI()  # reads OPENAI_API_KEY from env
    return _client

def _to_lang_name(code: str) -> str:
    return {
        "zh": "Chinese",
        "ko": "Korean",
        "en": "English"
    }.get(code, code)

def _chat(messages, temperature=0.3) -> Tuple[str, Dict]:
    client = _client_singleton()
    start = time.time()
    resp = client.chat.completions.create(
        model=MODEL_DEFAULT,
        messages=messages,
        temperature=temperature,
    )
    latency_ms = int((time.time() - start) * 1000)
    content = resp.choices[0].message.content or ""
    usage = {
        "prompt_tokens": getattr(resp.usage, "prompt_tokens", None),
        "completion_tokens": getattr(resp.usage, "completion_tokens", None),
        "model": resp.model,
        "latency_ms": latency_ms,
    }
    return content, usage

def translate_text(text: str, source_lang: str, target_lang: str, native_lang: str, temperature: float = 0.2):
    src = "Auto-detect" if source_lang == "auto" else _to_lang_name(source_lang)
    tgt = _to_lang_name(target_lang)
    native = _to_lang_name(native_lang)
    system = (
        f"You are an expert translator for {tgt}. "
        f"User's native language is {native}. "
        "Translate the user's text into the target language while preserving meaning, tone, and nuance. "
        "If source language is not specified, detect it first. "
        "Provide only the translation."
    )
    user = f"Source language: {src}\nTarget language: {tgt}\nText:\n{text}"
    return _chat([
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ], temperature=temperature)

def correct_grammar(text: str, target_lang: str, native_lang: str, level: str = "intermediate"):
    tgt = _to_lang_name(target_lang)
    native = _to_lang_name(native_lang)
    system = (
        f"You are a {tgt} writing tutor. The learner's native language is {native}. "
        f"Correct grammar, spelling, spacing, and word choice at a {level} level. "
        "Steps:\n"
        "1) Provide the corrected version in the target language only.\n"
        "2) Briefly explain key corrections in the learner's native language.\n"
        "3) Give 1-2 short example sentences in the target language."
    )
    user = f"Target language: {tgt}\nText to correct:\n{text}"
    return _chat([
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ], temperature=0.2)

def suggest_natural_expression(text: str, target_lang: str, native_lang: str, tone_preference: str = "neutral"):
    tgt = _to_lang_name(target_lang)
    native = _to_lang_name(native_lang)
    system = (
        f"You are a {tgt} stylist and conversation coach. Learner's native language is {native}. "
        f"Suggest 2-3 natural rewrites matching this tone: {tone_preference}. "
        "Also give a brief rationale in the learner's native language. "
        "Keep responses concise."
    )
    user = f"Target language: {tgt}\nText:\n{text}"
    return _chat([
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ], temperature=0.6)

def explain_vocabulary(text: str, target_lang: str, native_lang: str, max_items: int = 5):
    tgt = _to_lang_name(target_lang)
    native = _to_lang_name(native_lang)
    system = (
        f"You are a bilingual vocabulary explainer for {tgt} learners whose native language is {native}. "
        f"Extract up to {max_items} useful words/phrases from the text for a learner of the target language. "
        "For each item, provide:\n"
        "- Meaning explained in the learner's native language\n"
        "- A short example sentence in the target language\n"
        "- A usage note or common mistake (brief)\n"
        "Keep lists short and readable."
    )
    user = f"Target language: {tgt}\nText:\n{text}"
    return _chat([
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ], temperature=0.3)

def analyze_tone(text: str, lang: str, native_lang: str):
    ln = _to_lang_name(lang)
    native = _to_lang_name(native_lang)
    system = (
        f"You are a {ln} tone analyst. The learner's native language is {native}. "
        "Classify tone as one of: polite, casual, formal. "
        "Provide:\n"
        "1) Detected tone label\n"
        "2) One-sentence reason in the learner's native language\n"
        "3) Rewrites of the same content in {ln} for: more polite, more neutral, more casual, more formal."
    )
    user = f"Language: {ln}\nText:\n{text}"
    return _chat([
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ], temperature=0.3)

def chat_reply_assistant(
    text: str,
    source_lang: str,
    target_lang: str,
    native_lang: str,
    temperature: float = 0.3,
    max_vocab: int = 6
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Returns (result_dict, usage)
    result_dict contains:
      - detected_source_lang: 'zh'|'ko'|'en'
      - translation: str (in target language)
      - vocabulary: list of {item, meaning_native, example_target, note}
      - reply_natural: str (in target language)
      - reply_polite: str (in target language)
      - reply_casual: str (in target language)
    """
    src = "Auto-detect" if source_lang == "auto" else _to_lang_name(source_lang)
    tgt = _to_lang_name(target_lang)
    native = _to_lang_name(native_lang)

    system = (
        "You are a multilingual chat reply assistant.\n"
        f"User's native language: {native}.\n"
        f"Target language for study and replies: {tgt}.\n"
        "Your job: given a user message, produce a structured JSON with:\n"
        "detected_source_lang: language code of the user message ('zh'|'ko'|'en')\n"
        "translation: translation of the user message into the target language\n"
        "vocabulary: up to N important words/phrases useful for learners; for each include:\n"
        "  - item (the word/phrase)\n"
        "  - meaning_native (explanation in the user's native language)\n"
        "  - example_target (a short example sentence in the target language)\n"
        "  - note (brief usage note)\n"
        "reply_natural: a natural, context-appropriate reply in the target language\n"
        "reply_polite: a more polite version of the reply in the target language\n"
        "reply_casual: a casual/friendly version in the target language\n"
        "Rules:\n"
        "- Output STRICT JSON only (no markdown, no code fences).\n"
        "- Use exactly these keys: detected_source_lang, translation, vocabulary, reply_natural, reply_polite, reply_casual.\n"
        "- detected_source_lang must be one of: 'zh', 'ko', 'en'.\n"
        "- Keep replies concise and natural.\n"
    )
    user = json.dumps({
        "source_language_hint": src,
        "target_language": tgt,
        "native_language": native,
        "max_vocab": max_vocab,
        "message": text
    }, ensure_ascii=False)

    content, usage = _chat([
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ], temperature=temperature)

    # Try parse JSON
    result: Dict[str, Any] = {}
    try:
        result = json.loads(content)
        # Ensure vocabulary is list
        if not isinstance(result.get("vocabulary", []), list):
            result["vocabulary"] = []
    except Exception:
        # Fallback minimal result
        result = {
            "detected_source_lang": source_lang if source_lang != "auto" else None,
            "translation": content,
            "vocabulary": [],
            "reply_natural": "",
            "reply_polite": "",
            "reply_casual": "",
        }
    return result, usage
