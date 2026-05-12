import os
import re
from typing import Dict, Any, List, Optional, Tuple

# OpenAI SDK
try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # allow import without SDK during static analysis

# -------------- Model / Client setup --------------
def get_default_model() -> str:
    # You can override via .env: OPENAI_MODEL=gpt-4o-mini
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def _get_client() -> Any:
    """
    Create an OpenAI client. Supports optional OPENAI_BASE_URL for proxies/compat endpoints.
    Requires OPENAI_API_KEY in environment.
    """
    if OpenAI is None:
        raise RuntimeError("openai Python SDK not found. Install with: pip install openai>=1.0.0")
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in environment")
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)

def _extract_usage(resp: Any, fallback_model: str) -> Dict[str, Any]:
    # Robust usage extraction across variants
    model = getattr(resp, "model", None) or fallback_model
    usage_obj = getattr(resp, "usage", None)
    pt = getattr(usage_obj, "prompt_tokens", None) if usage_obj else None
    ct = getattr(usage_obj, "completion_tokens", None) if usage_obj else None
    return {"model": model, "prompt_tokens": pt, "completion_tokens": ct}

def _chat(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.3,
) -> Tuple[str, Dict[str, Any]]:
    """
    Wrapper around Chat Completions API returning (text, usage_dict).
    usage_dict keys: model, prompt_tokens, completion_tokens
    """
    client = _get_client()
    mdl = model or get_default_model()
    try:
        resp = client.chat.completions.create(
            model=mdl,
            messages=messages,
            temperature=float(temperature),
        )
        text = (resp.choices[0].message.content or "").strip()
        usage = _extract_usage(resp, mdl)
        return text, usage
    except Exception as e:
        # Fallback error text and minimal usage
        err_msg = f"(AI error) {e}"
        return err_msg, {"model": mdl, "prompt_tokens": None, "completion_tokens": None}

# -------------- Language helpers --------------
LANG_NAME = {
    "en": "English",
    "zh": "Chinese",
    "ko": "Korean",
}

def _lang_name(code: str) -> str:
    return LANG_NAME.get(code, code)

def detect_lang_code(text: str) -> str:
    """
    Lightweight heuristic detector for ['zh', 'ko', 'en'].
    Prefers the script with stronger signal; falls back to 'en'.
    """
    if not text or not text.strip():
        return "en"

    hangul = re.findall(r"[\uac00-\ud7a3]", text)
    han = re.findall(r"[\u4e00-\u9fff]", text)
    latin = re.findall(r"[A-Za-z]", text)

    h_count = len(hangul)
    c_count = len(han)
    l_count = len(latin)

    if h_count >= 2 and h_count >= c_count:
        return "ko"
    if c_count >= 2 and c_count > h_count:
        return "zh"
    if l_count >= 1:
        return "en"
    return "en"

# -------------- Persona helpers --------------
# Internal map: persona_code -> prompt-facing label
PERSONA_MAP = {
    "korean_friend": "Korean Friend",
    "korean_teacher": "Korean Teacher",
    "workplace": "Workplace Assistant",
    "travel": "Travel Assistant",
    "kpop_friend": "K-pop Fan Friend",
}

def _persona_str(persona_or_code: Optional[str]) -> str:
    """
    Accepts either a code ('korean_friend') or a readable label ('Korean Friend').
    Falls back to a friendly default if empty.
    """
    if not persona_or_code:
        return "Korean Friend"
    return PERSONA_MAP.get(persona_or_code, persona_or_code)

# -------------- System prompt --------------
def _mk_system(native_lang: str, target_lang: Optional[str] = None) -> str:
    """
    Build a concise system prompt that enforces:
    - Explanations in native language
    - Examples/rewrites in target language (when provided)
    """
    nat = _lang_name(native_lang)
    tgt = _lang_name(target_lang) if target_lang else None
    base = [
        "You are TriLingua Bridge, a concise, friendly tri-lingual assistant for Chinese, Korean, and English learners.",
        f"- Use {nat} for explanations, notes, and meta comments.",
    ]
    if tgt:
        base.append(f"- Use {tgt} for all examples, rewrites, and suggested replies.")
    base.append("- Keep formatting clean and readable with short sections and bullet points as needed.")
    base.append("- Do not add lengthy prefaces or disclaimers.")
    return "\n".join(base)

# -------------- Output format helpers --------------
def _mk_header(title: str) -> str:
    return f"## {title}\n"

def _kv(label: str, value: str) -> str:
    return f"- {label}: {value}\n"

# -------------- Feature: Translation --------------
def translate_text(
    text: str,
    source_lang: str = "auto",
    target_lang: str = "ko",
    native_lang: str = "en",
    temperature: float = 0.3,
    model: Optional[str] = None,
) -> Tuple[str, Dict[str, Any], str]:
    """
    Returns (result_text, usage_dict, detected_lang_code).
    """
    text = (text or "").strip()
    detected = detect_lang_code(text) if source_lang == "auto" else source_lang
    tgt_name = _lang_name(target_lang)
    det_name = _lang_name(detected)

    sys = _mk_system(native_lang=native_lang, target_lang=target_lang)
    # Remove the model-generated "Detected language" line to avoid duplication.
    usr = f"""
Task: Translate the user's message into {tgt_name}, then extract key vocabulary.

User message (original):
{text}

Output requirements:
1) Section 'Translation ({tgt_name})' with a clear, natural translation in {tgt_name}.
2) Section 'Important vocabulary' (5–8 bullets). For each item:
   - Headword (in {tgt_name} when appropriate, or original if it's a source-locked term)
   - Short gloss in {tgt_name}
   - One-sentence explanation in {_lang_name(native_lang)}
   - One short example sentence in {tgt_name}
Be concise and practical.
""".strip()

    content, usage = _chat(
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": usr}],
        model=model,
        temperature=temperature,
    )

    # Prepend a small header with detection info to keep structure consistent
    header = []
    header.append(_mk_header("Detected source language"))
    header.append(det_name + "\n")
    result = "\n".join(header) + content
    return result, usage, detected

# -------------- Feature: Grammar correction --------------
def correct_grammar(
    text: str,
    target_lang: str = "ko",
    native_lang: str = "en",
    level: str = "intermediate",
    persona: str = "korean_teacher",
    temperature: float = 0.3,
    model: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    tgt = _lang_name(target_lang)
    sys = _mk_system(native_lang=native_lang, target_lang=target_lang)
    role = _persona_str(persona)
    usr = f"""
Role: {role}. Correct and improve the user's {tgt} sentence(s).

User text:
{text}

Requirements:
- Provide 'Corrected version' (only {tgt}) with minimal necessary edits.
- Provide 'Why' in {_lang_name(native_lang)}: short bullet points explaining main mistakes (grammar, word choice, politeness).
- Provide 'Better alternatives' (2–3) in {tgt} with brief labels (e.g., 'more polite', 'more casual').
- Keep it concise and level-appropriate for a {level} learner.
""".strip()

    content, usage = _chat(
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": usr}],
        model=model,
        temperature=temperature,
    )
    return content, usage

# -------------- Feature: Natural expression --------------
def suggest_natural_expression(
    text: str,
    target_lang: str = "ko",
    native_lang: str = "en",
    tone_preference: str = "neutral",
    persona: str = "korean_friend",
    temperature: float = 0.4,
    model: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    tgt = _lang_name(target_lang)
    sys = _mk_system(native_lang=native_lang, target_lang=target_lang)
    role = _persona_str(persona)
    usr = f"""
Role: {role}. Rewrite to sound natural in {tgt}.

Original:
{text}

Produce:
- 'Natural version' in {tgt} (aligned with tone: {tone_preference}).
- 'Why this works' in {_lang_name(native_lang)}: brief notes on word choice and tone.
- 'Other options' (2–3) in {tgt} with small tone labels (e.g., casual/polite/formal).
""".strip()

    content, usage = _chat(
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": usr}],
        model=model,
        temperature=temperature,
    )
    return content, usage

# -------------- Feature: Vocabulary explanation --------------
def explain_vocabulary(
    text: str,
    target_lang: str = "ko",
    native_lang: str = "en",
    max_items: int = 6,
    persona: str = "korean_teacher",
    temperature: float = 0.3,
    model: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    tgt = _lang_name(target_lang)
    sys = _mk_system(native_lang=native_lang, target_lang=target_lang)
    role = _persona_str(persona)
    usr = f"""
Role: {role}. Extract up to {max_items} important vocabulary items relevant to the text.
Text:
{text}

For each item, output:
- Headword (in {tgt} if it's target-language vocab, otherwise original form)
- Short meaning in {tgt}
- Brief explanation in {_lang_name(native_lang)}
- 1 short example sentence in {tgt}
""".strip()

    content, usage = _chat(
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": usr}],
        model=model,
        temperature=temperature,
    )
    return content, usage

# -------------- Feature: Tone analysis --------------
def analyze_tone(
    text: str,
    lang: str = "ko",
    native_lang: str = "en",
    persona: str = "korean_friend",
    temperature: float = 0.3,
    model: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    lng = _lang_name(lang)
    sys = _mk_system(native_lang=native_lang, target_lang=lang)
    role = _persona_str(persona)
    usr = f"""
Role: {role}. Analyze the tone of this {lng} message and suggest responses.

Message:
{text}

Output:
- 'Tone snapshot' in {_lang_name(native_lang)}: attitude, emotion, formality, politeness level (0–10 each).
- 'How it might be perceived' in {_lang_name(native_lang)}.
- 'Reply options' in {lng}: 3 concise options (natural / polite / casual).
- 'Recommended reply' in {lng} with one-sentence reason in {_lang_name(native_lang)}.
""".strip()

    content, usage = _chat(
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": usr}],
        model=model,
        temperature=temperature,
    )
    return content, usage

# -------------- Tool: Chat reply assistant --------------
def chat_reply_assistant(
    text: str,
    source_lang: str = "auto",
    target_lang: str = "ko",
    native_lang: str = "en",
    persona: str = "korean_friend",
    temperature: float = 0.4,
    model: Optional[str] = None,
) -> Tuple[str, Dict[str, Any], str]:
    detected = detect_lang_code(text) if source_lang == "auto" else source_lang
    tgt = _lang_name(target_lang)
    det = _lang_name(detected)
    sys = _mk_system(native_lang=native_lang, target_lang=target_lang)
    role = _persona_str(persona)
    usr = f"""
Role: {role}. The user received a message in {det} and wants to reply in {tgt}.

Incoming message:
{text}

Provide:
- 'Quick read' in {_lang_name(native_lang)}: tone, intent, possible subtext.
- 'Natural reply options' in {tgt}: 3–4 short variants with tone labels.
- 'Recommended reply' in {tgt} and a one-sentence reason in {_lang_name(native_lang)}.
""".strip()

    content, usage = _chat(
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": usr}],
        model=model,
        temperature=temperature,
    )

    header = []
    header.append(_mk_header("Detected language"))
    header.append(det + "\n")
    result = "\n".join(header) + content
    return result, usage, detected

# -------------- Optional core modes (kept for reuse/extension) --------------
def mode_what_i_want_to_say(
    text: str,
    source_lang: str = "auto",
    target_lang: str = "ko",
    native_lang: str = "en",
    persona: str = "korean_friend",
    temperature: float = 0.4,
    model: Optional[str] = None,
) -> Tuple[str, Dict[str, Any], str]:
    detected = detect_lang_code(text) if source_lang == "auto" else source_lang
    tgt = _lang_name(target_lang)
    det = _lang_name(detected)
    sys = _mk_system(native_lang=native_lang, target_lang=target_lang)
    role = _persona_str(persona)
    usr = f"""
Role: {role}. The user will say something in their own words; produce versions in {tgt}.

User intent:
{text}

Output sections:
1) 'Direct translation' in {tgt} (literal but correct).
2) 'Natural version' in {tgt} (most idiomatic).
3) 'Young/casual' in {tgt}.
4) 'Polite' in {tgt}.
5) 'Close-friend' in {tgt}.
6) 'Tone notes' in {_lang_name(native_lang)}: when to use each.
Keep each version concise (one or two short sentences).
""".strip()

    content, usage = _chat(
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": usr}],
        model=model,
        temperature=temperature,
    )

    pre = _mk_header("Detected source language") + det + "\n"
    return pre + content, usage, detected

def mode_what_does_this_mean(
    text: str,
    lang: str = "ko",
    native_lang: str = "en",
    persona: str = "korean_friend",
    temperature: float = 0.3,
    model: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    lng = _lang_name(lang)
    sys = _mk_system(native_lang=native_lang, target_lang=lang)
    role = _persona_str(persona)
    usr = f"""
Role: {role}. Explain the meaning of this {lng} message.

Message:
{text}

Output:
- 'Literal meaning' in {_lang_name(native_lang)} (word-for-word gist).
- 'Natural meaning' in {_lang_name(native_lang)} (what they probably mean).
- 'Hidden emotion/tone' and 'Social vibe' in {_lang_name(native_lang)}.
- 'How to interpret it' in {_lang_name(native_lang)}.
- 'How you could reply' in {lng}: 2–3 short options.
""".strip()

    content, usage = _chat(
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": usr}],
        model=model,
        temperature=temperature,
    )
    return content, usage

def mode_ai_chat_coach(
    text: str,
    lang: str = "ko",
    native_lang: str = "en",
    target_lang: str = "ko",
    persona: str = "korean_friend",
    temperature: float = 0.4,
    model: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    lng = _lang_name(lang)
    tgt = _lang_name(target_lang)
    sys = _mk_system(native_lang=native_lang, target_lang=target_lang)
    role = _persona_str(persona)
    usr = f"""
Role: {role}. Analyze this chat snippet and coach the user to reply naturally in {tgt}.

Chat snippet ({lng}):
{text}

Provide:
- 'Atmosphere & other person’s attitude' in {_lang_name(native_lang)} (2–3 bullets).
- 'What to avoid' in {_lang_name(native_lang)} (e.g., too formal / MT-sounding).
- 'Good reply patterns' in {_lang_name(native_lang)} with mini templates in {tgt}.
- 'Recommended reply' in {tgt} (1–2 lines).
- 'Why this works' in {_lang_name(native_lang)} (1–2 bullets).
""".strip()

    content, usage = _chat(
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": usr}],
        model=model,
        temperature=temperature,
    )
    return content, usage

def mode_kpop_kdrama_context(
    text: str,
    native_lang: str = "en",
    persona: str = "korean_teacher",
    temperature: float = 0.35,
    model: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    # Always Korean source in concept; provide both English and Chinese meaning.
    sys = _mk_system(native_lang=native_lang, target_lang="ko")
    role = _persona_str(persona)
    usr = f"""
Role: {role}. Analyze a Korean lyric or drama line.

Korean line:
{text}

Output:
- 'Meaning (English)' — concise translation in English.
- 'Meaning (Chinese)' — concise translation in Simplified Chinese.
- 'Word breakdown' — key words/phrases with glosses (Korean + short gloss).
- 'Grammar notes' — short points in {_lang_name(native_lang)}.
- 'Natural usage' — how natives would use/say it, with 1–2 Korean examples.
- 'Casual example' — one short Korean line.
- 'Cultural note' — brief context in {_lang_name(native_lang)}.
Keep it compact and practical.
""".strip()

    content, usage = _chat(
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": usr}],
        model=model,
        temperature=temperature,
    )
    return content, usage
