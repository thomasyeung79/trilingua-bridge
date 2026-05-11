import os
import time
from typing import Dict, Tuple
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
        "Keep the output clean and readable. Provide only the translation."
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