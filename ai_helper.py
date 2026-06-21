import base64
import json
import os
from typing import Any, Optional

from dotenv import load_dotenv
from openai import OpenAI

try:
    from error_monitor import capture_error
except Exception:

    def capture_error(*args, **kwargs):
        pass  # no-op fallback


try:
    from anthropic import Anthropic

    HAVE_ANTHROPIC = True
except Exception:
    Anthropic = None
    HAVE_ANTHROPIC = False

try:
    import requests
except Exception:
    requests = None


load_dotenv()

Lang = str


# =========================
# Secrets / Clients
# =========================


def get_secret_value(key: str) -> str | None:
    value = os.environ.get(key)

    try:
        import streamlit as st

        value = st.secrets.get(key) or value
    except Exception:
        pass

    return value


def get_ai_provider() -> str:
    provider = (get_secret_value("AI_PROVIDER") or "auto").lower().strip()

    if provider not in ("auto", "openai", "deepseek", "anthropic"):
        return "auto"

    return provider


def get_openai_client() -> OpenAI | None:
    api_key = get_secret_value("OPENAI_API_KEY")

    if not api_key:
        return None

    return OpenAI(api_key=api_key)


def get_deepseek_client() -> OpenAI | None:
    api_key = get_secret_value("DEEPSEEK_API_KEY")

    if not api_key:
        return None

    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )


def get_openai_model(model: str | None = None) -> str:
    return model or get_secret_value("OPENAI_MODEL") or "gpt-4o-mini"


def get_deepseek_model(model: str | None = None) -> str:
    return model or get_secret_value("DEEPSEEK_MODEL") or "deepseek-chat"


# =========================
# Common Helpers
# =========================


def safe_json_loads(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)

        if isinstance(data, dict):
            return data

        return {"result": data}

    except Exception:
        return {}


def usage_from_response(response, provider: str) -> dict[str, Any]:
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


def mock_usage(model: str | None = None, provider: str = "mock") -> dict[str, Any]:
    return {
        "model": model or provider,
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
        "provider": provider,
    }


def language_rules() -> str:
    return """
Language code rules:
- zh = Simplified Chinese / Mandarin Chinese
- yue = Traditional Chinese / Cantonese
- ko = Korean
- ja = Japanese
- en = English

Output rules:
- If target_lang is zh, output Simplified Chinese.
- If target_lang is yue, output Traditional Chinese with Cantonese wording when appropriate.
- If target_lang is ko, output Korean.
- If target_lang is ja, output Japanese.
- If target_lang is en, output English.
- Do not output Korean unless target_lang or output_lang is ko.
- Do not output Japanese unless target_lang or output_lang is ja.
- Do not output English unless target_lang or output_lang is en.
- Do not mix languages unless the user explicitly asks for bilingual output.

Phonetic input rules:
- Users may type Mandarin, Cantonese, Korean, or Japanese using Latin letters instead of native script.
- Treat pinyin such as "wo xiang qu", "ni hao", "xiexie" as Mandarin Chinese (zh) when the task/source/target context points to Chinese.
- Treat Jyutping or Cantonese romanization such as "ngo5 soeng2 heoi3", "nei5 hou2", "m4 goi1" as Cantonese (yue).
- Treat Korean romanization such as "annyeong haseyo", "gomawo", "mianhae" as Korean (ko).
- Treat Japanese romanization such as "konnichiwa", "arigatou", "sumimasen" as Japanese (ja).
- Do not treat phonetic Latin input as English merely because it uses the Latin alphabet.
- If phonetic input is ambiguous, infer from source_lang, target_lang, native_lang, region/cultural mode, and the user's selected learning language.
- When correcting, translating, explaining, or coaching, first infer the intended native-script phrase, then complete the requested task.
"""


def strict_language_guard() -> str:
    return """
Strict language compliance:
- Obey target_lang, output_lang, and native_lang exactly.
- For translation, the translated text must be in target_lang only.
- For explanations, explanations must be in native_lang only.
- All headings, labels, reasons, tone notes, tips, caveats, and suggestions explanations must be in native_lang only.
- Never switch to Korean just because the app supports Korean.
- Never switch to Japanese just because the app supports Japanese.
- Never infer a different target language from previous tasks.
- The current request's target_lang is the only target language that matters.
- Romanized phonetic input may be interpreted as zh, yue, ko, or ja, but final output must still obey the requested output language.
"""


def quality_guard(native_lang: str) -> str:
    return f"""
Quality and safety guard:
- Explanations must be in native_lang ({native_lang}) only. Do not write English explanations unless native_lang is en.
- JSON fields named notes, reason, tips, intent, tone_notes, tone_summary, cultural_notes, caution, explanation, or why must be written in native_lang ({native_lang}) only.
- JSON fields named clean, better_version, suggestions, examples, reply_options, or translated_text may be in target_lang when they are the actual user-facing sentence, but their explanations must still be in native_lang.
- Do not invent intent, identity, emotion, relationship, or context that the user did not provide.
- If the sentence is odd, insulting, self-deprecating, rude, or ambiguous, handle it neutrally.
- For grammar correction, preserve the original meaning as closely as possible and only fix grammar.
- Do not create playful, demeaning, insulting, or animal-related alternative sentences unless the user explicitly asks for them.
- If the original sentence is self-insulting or potentially offensive, briefly note in native_lang that it may sound self-deprecating or rude, then provide a neutral safer alternative that avoids the insult.
- If the input contains "pig", "猪", "豬", "돼지", or similar animal/self-insult wording, do not suggest "piglet", "cute pig", "可爱的猪", "小猪", "돼지", or any other animal-based alternative. Use neutral alternatives such as admitting a mistake, feeling embarrassed, or clarifying the intended meaning.
- Examples should demonstrate the grammar or tone pattern with neutral content, not intensify the user's wording.
"""


def phonetic_input_context(*langs: str) -> str:
    relevant = {lang for lang in langs if lang in ("zh", "yue", "ko", "ja", "auto")}

    if not relevant:
        return ""

    return (
        "The input may be phonetic Latin text rather than English. "
        "Support Mandarin pinyin, Cantonese Jyutping/romanization, and Korean romanization. "
        "Infer the intended zh/yue/ko phrase from context before answering."
    )


EXPLANATION_KEYS = {
    "notes",
    "reason",
    "tips",
    "intent",
    "tone_notes",
    "tone_summary",
    "cultural_notes",
    "caution",
    "explanation",
    "why",
    "meaning",
    "note",
    "message",
    "error",
    "summary",
    "hidden_meaning",
    "recommended_understanding",
}


def has_english_explanation(text: str, native_lang: str) -> bool:
    if native_lang == "en" or not text:
        return False

    letters = sum(1 for char in text if ("a" <= char.lower() <= "z"))
    if letters < 18:
        return False

    return letters / max(len(text), 1) > 0.35


def repair_explanation_text(
    text: str,
    native_lang: str,
    model: str,
    temperature: float,
) -> str:
    if not has_english_explanation(text, native_lang):
        return text

    system_prompt = (
        "You are a strict translation and localization repair tool.\n"
        f"Rewrite the text into native_lang={native_lang} only.\n"
        "Preserve meaning, but remove English explanations.\n"
        "If the text contains self-deprecating or insulting animal wording, make the explanation neutral and do not add animal-based alternatives.\n"
        f"{get_output_rule(native_lang)}"
    )
    user_prompt = f"Repair this explanation text. Return only the repaired text, no markdown fences.\n\n{text}"
    repaired, _ = call_plain_chat(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=min(temperature, 0.2),
    )
    if "failed:" in repaired.lower() or "both openai and deepseek failed" in repaired.lower():
        return text
    return repaired.strip() or text


def localized_fallback_text(native_lang: str, key: str) -> str:
    texts = {
        "zh": {
            "reply_1": "暂时无法生成回复选项。",
            "reply_2": "请稍后重试，或检查 AI 服务配置。",
            "reply_3": "当前只能显示本地兜底提示。",
            "tone_notes": "暂时无法分析语气。",
            "cultural_notes": "暂时无法生成文化说明。",
            "reason": "AI 服务暂时不可用，请检查 API Key 或网络配置。",
        },
        "yue": {
            "reply_1": "暫時未能生成回覆選項。",
            "reply_2": "請稍後再試，或者檢查 AI 服務設定。",
            "reply_3": "而家只可以顯示本地備用提示。",
            "tone_notes": "暫時未能分析語氣。",
            "cultural_notes": "暫時未能生成文化說明。",
            "reason": "AI 服務暫時用唔到，請檢查 API Key 或網絡設定。",
        },
        "ko": {
            "reply_1": "지금은 답장 선택지를 만들 수 없습니다.",
            "reply_2": "잠시 후 다시 시도하거나 AI 서비스 설정을 확인해 주세요.",
            "reply_3": "현재는 로컬 대체 안내만 표시됩니다.",
            "tone_notes": "지금은 말투를 분석할 수 없습니다.",
            "cultural_notes": "지금은 문화적 설명을 만들 수 없습니다.",
            "reason": "AI 서비스를 사용할 수 없습니다. API Key 또는 네트워크 설정을 확인해 주세요.",
        },
        "en": {
            "reply_1": "Unable to generate reply options right now.",
            "reply_2": "Please try again later or check the AI service settings.",
            "reply_3": "Only a local fallback message is available.",
            "tone_notes": "Tone analysis is unavailable right now.",
            "cultural_notes": "Cultural notes are unavailable right now.",
            "reason": "The AI service is unavailable. Check your API key or network settings.",
        },
        "ja": {
            "reply_1": "現在、返信オプションを生成できません。",
            "reply_2": "後でもう一度試すか、AIサービスの設定を確認してください。",
            "reply_3": "現在はローカルフォールバックメッセージのみ表示されています。",
            "tone_notes": "現在、トーン分析を利用できません。",
            "cultural_notes": "現在、文化的な解説を生成できません。",
            "reason": "AIサービスが利用できません。APIキーまたはネットワーク設定を確認してください。",
        },
    }
    return texts.get(native_lang, texts["en"]).get(key, texts["en"].get(key, ""))


def repair_json_explanation_language(
    value: Any,
    native_lang: str,
    model: str,
    temperature: float,
    parent_key: str = "",
) -> Any:
    if native_lang == "en":
        return value

    if isinstance(value, dict):
        return {
            key: repair_json_explanation_language(
                item,
                native_lang,
                model,
                temperature,
                key,
            )
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            repair_json_explanation_language(
                item,
                native_lang,
                model,
                temperature,
                parent_key,
            )
            for item in value
        ]

    if isinstance(value, str) and parent_key in EXPLANATION_KEYS:
        return repair_explanation_text(value, native_lang, model, temperature)

    return value


def get_output_rule(lang: str) -> str:
    rules = {
        "zh": "Use Simplified Chinese only. Do not output English, Korean, or Japanese.",
        "yue": "Use Traditional Chinese / Cantonese-style wording only. Do not output English, Korean, or Japanese.",
        "ko": "Use Korean only. Do not output Chinese, English, or Japanese unless quoting source text.",
        "ja": "Use Japanese only. Do not output Chinese, Korean, or English unless quoting source text.",
        "en": "Use English only. Do not output Chinese, Korean, or Japanese unless quoting source text.",
    }

    return rules.get(lang, "Use the requested output language only.")


def persona_instructions(persona_profile: dict[str, Any]) -> str:
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


def _call_openai_json(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    client = get_openai_client()

    if not client:
        raise RuntimeError("OpenAI API key is missing.")

    response = client.chat.completions.create(
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


def _call_deepseek_json(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    client = get_deepseek_client()

    if not client:
        raise RuntimeError("DeepSeek API key is missing.")

    response = client.chat.completions.create(
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


def _call_openai_plain(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
) -> tuple[str, dict[str, Any]]:
    client = get_openai_client()

    if not client:
        raise RuntimeError("OpenAI API key is missing.")

    response = client.chat.completions.create(
        model=get_openai_model(model),
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content or ""
    return content, usage_from_response(response, "openai")


def _call_deepseek_plain(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
) -> tuple[str, dict[str, Any]]:
    client = get_deepseek_client()

    if not client:
        raise RuntimeError("DeepSeek API key is missing.")

    response = client.chat.completions.create(
        model=get_deepseek_model(),
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content or ""
    return content, usage_from_response(response, "deepseek")


# =========================
# Anthropic / Claude
# =========================


def get_anthropic_client() -> Optional["Anthropic"]:
    if not HAVE_ANTHROPIC:
        return None
    api_key = get_secret_value("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return Anthropic(api_key=api_key)


def get_anthropic_model(model: str | None = None) -> str:
    return model or get_secret_value("ANTHROPIC_MODEL") or "claude-sonnet-4-20250514"


def _call_anthropic_json(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    client = get_anthropic_client()
    if not client:
        raise RuntimeError("Anthropic API key is missing.")

    response = client.messages.create(
        model=get_anthropic_model(model),
        temperature=temperature,
        max_tokens=4096,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt},
        ],
    )

    content = (
        "".join(block.text for block in response.content if block.type == "text")
        if hasattr(response.content, "__iter__")
        else (response.content[0].text if response.content else "")
    )

    data = safe_json_loads(content)
    usage_obj = getattr(response, "usage", None)
    usage = {
        "model": f"anthropic/{get_anthropic_model(model)}",
        "prompt_tokens": getattr(usage_obj, "input_tokens", None) if usage_obj else None,
        "completion_tokens": getattr(usage_obj, "output_tokens", None) if usage_obj else None,
        "provider": "anthropic",
    }
    return data, usage, content


def _call_anthropic_plain(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
) -> tuple[str, dict[str, Any]]:
    client = get_anthropic_client()
    if not client:
        raise RuntimeError("Anthropic API key is missing.")

    response = client.messages.create(
        model=get_anthropic_model(model),
        temperature=temperature,
        max_tokens=4096,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt},
        ],
    )

    content = (
        "".join(block.text for block in response.content if block.type == "text")
        if hasattr(response.content, "__iter__")
        else (response.content[0].text if response.content else "")
    )

    usage_obj = getattr(response, "usage", None)
    usage = {
        "model": f"anthropic/{get_anthropic_model(model)}",
        "prompt_tokens": getattr(usage_obj, "input_tokens", None) if usage_obj else None,
        "completion_tokens": getattr(usage_obj, "output_tokens", None) if usage_obj else None,
        "provider": "anthropic",
    }
    return content, usage


def call_json_chat(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.4,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    system_prompt = (
        system_prompt + "\nReturn valid JSON only. Do not include markdown." + "\n" + strict_language_guard()
    )

    provider = get_ai_provider()

    if provider == "openai":
        try:
            return _call_openai_json(model, system_prompt, user_prompt, temperature)
        except Exception as e:
            return (
                {"mock": True, "message": f"OpenAI failed: {e}"},
                mock_usage(model, "openai"),
                "",
            )

    if provider == "deepseek":
        try:
            return _call_deepseek_json(model, system_prompt, user_prompt, temperature)
        except Exception as e:
            return (
                {"mock": True, "message": f"DeepSeek failed: {e}"},
                mock_usage(model, "deepseek"),
                "",
            )

    if provider == "anthropic":
        try:
            return _call_anthropic_json(model, system_prompt, user_prompt, temperature)
        except Exception as e:
            return (
                {"mock": True, "message": f"Anthropic failed: {e}"},
                mock_usage(model, "anthropic"),
                "",
            )

    # Auto-fallback: try OpenAI → Anthropic → DeepSeek
    openai_error = ""

    try:
        return _call_openai_json(model, system_prompt, user_prompt, temperature)
    except Exception as e:
        openai_error = str(e)

    try:
        return _call_anthropic_json(model, system_prompt, user_prompt, temperature)
    except Exception as e:
        anthropic_error = str(e)

    try:
        return _call_deepseek_json(model, system_prompt, user_prompt, temperature)
    except Exception as e:
        deepseek_error = str(e)

        capture_error(
            "ai_provider_failure",
            extra={"stage": "json", "providers": "openai,anthropic,deepseek"},
        )

        return (
            {
                "mock": True,
                "message": (
                    "All providers failed.\n\n"
                    f"OpenAI Error: {openai_error}\n"
                    f"Anthropic Error: {anthropic_error}\n"
                    f"DeepSeek Error: {deepseek_error}"
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
) -> tuple[str, dict[str, Any]]:
    system_prompt = system_prompt + "\n" + strict_language_guard()
    provider = get_ai_provider()

    if provider == "openai":
        try:
            return _call_openai_plain(model, system_prompt, user_prompt, temperature)
        except Exception as e:
            return f"OpenAI failed: {e}", mock_usage(model, "openai")

    if provider == "deepseek":
        try:
            return _call_deepseek_plain(model, system_prompt, user_prompt, temperature)
        except Exception as e:
            return f"DeepSeek failed: {e}", mock_usage(model, "deepseek")

    if provider == "anthropic":
        try:
            return _call_anthropic_plain(model, system_prompt, user_prompt, temperature)
        except Exception as e:
            return f"Anthropic failed: {e}", mock_usage(model, "anthropic")

    openai_error = ""

    try:
        return _call_openai_plain(model, system_prompt, user_prompt, temperature)
    except Exception as e:
        openai_error = str(e)

    try:
        return _call_anthropic_plain(model, system_prompt, user_prompt, temperature)
    except Exception as e:
        anthropic_error = str(e)

    try:
        return _call_deepseek_plain(model, system_prompt, user_prompt, temperature)
    except Exception as e:
        capture_error(
            "ai_provider_failure",
            extra={"stage": "plain", "providers": "openai,anthropic,deepseek"},
        )
        return (
            f"All providers failed.\nOpenAI: {openai_error}\nAnthropic: {anthropic_error}\nDeepSeek: {e}",
            mock_usage(model),
        )


# =========================
# Language Detection
# =========================


def detect_language_simple(
    text: str,
    model: str,
    temperature: float,
    persona_profile: dict[str, Any],
) -> str | None:
    system_prompt = (
        "You are a strict language detector. "
        'Return JSON only: {"lang":"zh|yue|ko|ja|en"}.\n'
        "Do not translate the text.\n"
        "If the text is Latin letters but resembles Mandarin pinyin, return zh.\n"
        "If it resembles Cantonese Jyutping/romanization, especially with tone numbers like ngo5 or m4 goi1, return yue.\n"
        "If it resembles Korean romanization such as annyeong, gomawo, jinjja, return ko.\n"
        "If it resembles Japanese romanization such as konnichiwa, arigatou, sumimasen, or desu, return ja.\n"
        "Only return en when the text is actually English, not merely Latin-script phonetic input."
    )

    prompt = {
        "task": "detect_language",
        "allowed_codes": ["zh", "yue", "ko", "ja", "en"],
        "text": text,
        "hint": (
            "If the text is clearly Cantonese or Traditional Chinese Cantonese wording, return yue. "
            "Latin-script phonetic input is supported: pinyin=zh, Jyutping/Cantonese romanization=yue, Korean romanization=ko."
        ),
    }

    data, _, _ = call_json_chat(
        model=model,
        system_prompt=system_prompt,
        user_prompt=json.dumps(prompt, ensure_ascii=False),
        temperature=min(temperature, 0.2),
    )

    lang = data.get("lang")

    if lang in ("zh", "yue", "ko", "ja", "en"):
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
    persona_profile: dict[str, Any],
) -> tuple[str, dict[str, Any], str | None]:
    detected = None

    if source_lang == "auto":
        detected = detect_language_simple(
            text=text,
            model=model,
            temperature=temperature,
            persona_profile=persona_profile,
        )

    effective_source = detected or source_lang

    system_prompt = (
        "You are a helpful cross-cultural translator. "
        "Translate naturally and preserve tone, intent, and cultural meaning.\n"
        f"{language_rules()}\n"
        f"{strict_language_guard()}\n"
        f"Target language for this request: {target_lang}\n"
        f"Mandatory output rule: {get_output_rule(target_lang)}\n"
        f"{persona_instructions(persona_profile)}"
    )

    prompt = {
        "task": "translate",
        "source_lang": effective_source,
        "target_lang": target_lang,
        "native_lang": native_lang,
        "text": text,
        "phonetic_input_context": phonetic_input_context(effective_source, target_lang, native_lang),
        "important_output_rule": get_output_rule(target_lang),
        "do_not_use_other_target_languages": True,
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
# Meaning Analysis
# =========================


def explain_message_meaning(
    text: str,
    source_lang: Lang,
    native_lang: Lang,
    temperature: float,
    model: str,
    persona_profile: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], str | None]:
    detected = None

    if source_lang == "auto":
        detected = detect_language_simple(
            text=text,
            model=model,
            temperature=temperature,
            persona_profile=persona_profile,
        )

    system_prompt = (
        "You are a cross-cultural meaning and tone analyst.\n"
        "Do not only translate. Explain tone, hidden meaning, intent, and possible subtext.\n"
        f"{language_rules()}\n"
        f"{strict_language_guard()}\n"
        f"{quality_guard(native_lang)}\n"
        f"All explanations must be in native_lang: {native_lang}.\n"
        f"{get_output_rule(native_lang)}\n"
        f"{persona_instructions(persona_profile)}"
    )

    prompt = {
        "task": "meaning_analysis",
        "source_lang": detected or source_lang,
        "native_lang": native_lang,
        "text": text,
        "phonetic_input_context": phonetic_input_context(detected or source_lang, native_lang),
        "important_output_rule": get_output_rule(native_lang),
        "return_schema": {
            "detected_lang": "string or null",
            "clean_translation": "string",
            "tone_summary": f"string in {native_lang}",
            "intent": f"string in {native_lang}",
            "hidden_meaning": f"string in {native_lang}",
            "cultural_notes": f"string in {native_lang}",
            "tips": f"string in {native_lang}",
        },
    }

    data, usage, raw = call_json_chat(
        model=model,
        system_prompt=system_prompt,
        user_prompt=json.dumps(prompt, ensure_ascii=False),
        temperature=temperature,
    )

    if not data:
        data = {"summary": raw}

    data = repair_json_explanation_language(data, native_lang, model, temperature)
    return data, usage, data.get("detected_lang") or detected


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
    persona_profile: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    system_prompt = (
        "You are a grammar coach for multilingual learners.\n"
        f"{language_rules()}\n"
        f"{strict_language_guard()}\n"
        f"{quality_guard(native_lang)}\n"
        f"Corrected text must be in target_lang: {target_lang}.\n"
        f"Explanations must be in native_lang: {native_lang}. {get_output_rule(native_lang)}\n"
        f"{persona_instructions(persona_profile)}"
    )

    prompt = {
        "task": "grammar_correction",
        "target_lang": target_lang,
        "native_lang": native_lang,
        "level": level,
        "text": text,
        "phonetic_input_context": phonetic_input_context(target_lang, native_lang),
        "quality_rules": (
            "clean should only correct grammar and preserve meaning. "
            "notes must be in native_lang. examples must be neutral practice examples, "
            "not semantic alternatives that intensify or mock the user's sentence. "
            "If the text uses self-insulting animal wording, do not create animal-based examples or alternatives."
        ),
        "return_schema": {
            "clean": "corrected version",
            "notes": f"brief explanation in {native_lang}",
            "examples": [
                f"neutral grammar practice example in {target_lang}, not using insults or animal wording",
                f"neutral grammar practice example in {target_lang}, not using insults or animal wording",
            ],
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

    data = repair_json_explanation_language(data, native_lang, model, temperature)
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
    persona_profile: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    system_prompt = (
        "You are a natural expression coach. "
        "Improve the user's sentence so it sounds natural.\n"
        f"{language_rules()}\n"
        f"{strict_language_guard()}\n"
        f"{quality_guard(native_lang)}\n"
        f"Better version must be in target_lang: {target_lang}.\n"
        f"Explanations must be in native_lang: {native_lang}. {get_output_rule(native_lang)}\n"
        f"{persona_instructions(persona_profile)}"
    )

    prompt = {
        "task": "natural_expression",
        "target_lang": target_lang,
        "native_lang": native_lang,
        "tone_preference": tone_preference,
        "text": text,
        "phonetic_input_context": phonetic_input_context(target_lang, native_lang),
        "quality_rules": (
            "Do not turn self-deprecating, insulting, or odd input into more insulting alternatives. "
            "If needed, provide a safer neutral version and explain the concern in native_lang. "
            "If input contains pig/猪/豬/돼지 or similar animal self-insult wording, avoid all animal-based alternatives."
        ),
        "return_schema": {
            "better_version": "string",
            "suggestions": [f"safe neutral alternative in {target_lang}, avoiding insults and animal wording"],
            "tone_notes": f"string in {native_lang}",
            "naturalness_score": "1-10",
            "reason": f"string in {native_lang}",
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

    data = repair_json_explanation_language(data, native_lang, model, temperature)
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
    persona_profile: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    system_prompt = (
        "You are a vocabulary and phrase explainer.\n"
        f"{language_rules()}\n"
        f"{strict_language_guard()}\n"
        f"{quality_guard(native_lang)}\n"
        f"Explain in native_lang: {native_lang}. {get_output_rule(native_lang)}\n"
        f"{persona_instructions(persona_profile)}"
    )

    prompt = {
        "task": "vocabulary_explanation",
        "target_lang": target_lang,
        "native_lang": native_lang,
        "max_items": max_items,
        "text": text,
        "phonetic_input_context": phonetic_input_context(target_lang, native_lang),
        "return_schema": {
            "items": [
                {
                    "term": "word or phrase",
                    "meaning": f"meaning in {native_lang}",
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

    data = repair_json_explanation_language(data, native_lang, model, temperature)
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
    persona_profile: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    system_prompt = (
        "You are a tone and intent analyzer.\n"
        f"{language_rules()}\n"
        f"{strict_language_guard()}\n"
        f"{quality_guard(native_lang)}\n"
        f"Explain in native_lang: {native_lang}. {get_output_rule(native_lang)}\n"
        f"{persona_instructions(persona_profile)}"
    )

    prompt = {
        "task": "tone_analysis",
        "lang": lang,
        "native_lang": native_lang,
        "text": text,
        "phonetic_input_context": phonetic_input_context(lang, native_lang),
        "quality_rules": (
            "Analyze only the provided sentence. Do not infer the speaker's identity or intent beyond the text. "
            "All explanation fields must be in native_lang. "
            "For self-insulting animal wording, identify the wording as self-deprecating or potentially rude and suggest neutral wording."
        ),
        "return_schema": {
            "tone_summary": f"string in {native_lang}",
            "intent": f"string in {native_lang}",
            "tips": f"string in {native_lang}",
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

    data = repair_json_explanation_language(data, native_lang, model, temperature)
    return data, usage


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
    persona_profile: dict[str, Any],
    conversation_context: list[dict[str, str]] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], str | None]:
    detected = None

    if source_lang == "auto":
        detected = detect_language_simple(text, model, temperature, persona_profile)

    system_prompt = (
        "You are an advanced AI cross-cultural chat coach.\n"
        "Provide exactly 3 practical reply options.\n"
        f"Reply options must be in target_lang: {target_lang}.\n"
        f"Explanations must be in native_lang: {native_lang}.\n"
        f"{language_rules()}\n"
        f"{strict_language_guard()}\n"
        f"{quality_guard(native_lang)}\n"
        f"{persona_instructions(persona_profile)}"
    )

    prompt = {
        "task": "advanced_chat_coach",
        "source_text": text,
        "source_lang": detected or source_lang,
        "target_lang": target_lang,
        "native_lang": native_lang,
        "phonetic_input_context": phonetic_input_context(detected or source_lang, target_lang, native_lang),
        "reply_style": reply_style,
        "important_output_rule": (
            f"Reply options must be in {target_lang}. "
            f"Tone notes, cultural notes and reason must be in {native_lang}. "
            "Do not create demeaning, self-insulting, or animal-based alternatives. "
            "Do not use Korean unless target_lang or native_lang is ko. "
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
            "tone_notes": f"string in {native_lang}",
            "cultural_notes": f"string in {native_lang}",
            "suggested_best_reply": "string",
            "reason": f"string in {native_lang}",
            "pronunciation_guide": {
                "lang": "string",
                "text": "string",
            },
        },
    }

    if conversation_context:
        prompt["conversation_history"] = [
            {"role": turn.get("role", "user"), "content": turn.get("text", "")} for turn in conversation_context
        ]

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
                    "text": localized_fallback_text(native_lang, "reply_1"),
                    "naturalness_score": 8,
                    "tone": reply_style,
                },
                {
                    "text": localized_fallback_text(native_lang, "reply_2"),
                    "naturalness_score": 8,
                    "tone": reply_style,
                },
                {
                    "text": localized_fallback_text(native_lang, "reply_3"),
                    "naturalness_score": 8,
                    "tone": reply_style,
                },
            ],
            "tone_notes": localized_fallback_text(native_lang, "tone_notes"),
            "cultural_notes": localized_fallback_text(native_lang, "cultural_notes"),
            "suggested_best_reply": localized_fallback_text(native_lang, "reply_1"),
            "reason": localized_fallback_text(native_lang, "reason"),
        }

        data = repair_json_explanation_language(data, native_lang, model, temperature)
        return data, usage, detected

    if not data:
        data = {
            "reply_options": [{"text": raw}],
            "suggested_best_reply": raw,
        }

    data = repair_json_explanation_language(data, native_lang, model, temperature)
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
    persona_profile: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], str | None]:
    detected = None

    if source_lang == "auto":
        detected = detect_language_simple(text, model, temperature, persona_profile)

    system_prompt = (
        "You are a media and pop-culture context explainer.\n"
        "You explain lyrics, drama dialogue, internet slang and cultural context.\n"
        f"{language_rules()}\n"
        f"{strict_language_guard()}\n"
        f"{quality_guard(native_lang)}\n"
        f"Explain in native_lang: {native_lang}. {get_output_rule(native_lang)}\n"
        f"{persona_instructions(persona_profile)}"
    )

    prompt = {
        "task": "media_context",
        "source_lang": detected or source_lang,
        "native_lang": native_lang,
        "context_type": context_type,
        "text": text,
        "phonetic_input_context": phonetic_input_context(detected or source_lang, native_lang),
        "return_schema": {
            "detected_lang": "string or null",
            "clean_translation": "string",
            "key_phrases": [
                {
                    "phrase": "string",
                    "meaning": f"string in {native_lang}",
                    "note": f"string in {native_lang}",
                }
            ],
            "slang_pop_culture": [
                {
                    "term": "string",
                    "origin": "string",
                    "note": f"string in {native_lang}",
                }
            ],
            "tone_notes": f"string in {native_lang}",
            "cultural_notes": f"string in {native_lang}",
            "summary": f"string in {native_lang}",
            "recommended_understanding": f"string in {native_lang}",
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

    data = repair_json_explanation_language(data, native_lang, model, temperature)
    return data, usage, data.get("detected_lang") or detected


# =========================
# Screenshot Chat Analysis
# =========================


def analyze_screenshot_chat(
    image_bytes: bytes,
    image_name: str,
    assumed_lang: str | None,
    native_lang: str,
    target_lang: str,
    region_mode: str,
    temperature: float,
    model: str,
    persona_profile: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], str | None]:
    openai_client = get_openai_client()

    # Localized error texts for screenshot analysis
    _screenshot_err = {
        "summary": {
            "en": "Screenshot analysis requires an OpenAI vision model.",
            "zh": "截图分析需要 OpenAI 视觉模型支持。",
            "yue": "截圖分析需要 OpenAI 視覺模型支援。",
            "ko": "스크린샷 분석에는 OpenAI 비전 모델이 필요합니다.",
            "ja": "スクリーンショット分析にはOpenAI視覚モデルが必要です。",
        },
        "tone_notes": {
            "en": "Screenshot analysis does not automatically switch to other providers in the current version.",
            "zh": "当前版本不会把图片分析自动切换到其他提供商。",
            "yue": "目前版本唔會自動切換截圖分析到其他提供商。",
            "ko": "현재 버전에서는 스크린샷 분석이 다른 제공업체로 자동 전환되지 않습니다.",
            "ja": "現在のバージョンではスクリーンショット分析は他のプロバイダーに自動切り替えされません。",
        },
        "cultural_notes": {
            "en": "Please configure OPENAI_API_KEY in your environment.",
            "zh": "请先配置 OPENAI_API_KEY。",
            "yue": "請先設定 OPENAI_API_KEY。",
            "ko": "OPENAI_API_KEY를 설정해 주세요.",
            "ja": "OPENAI_API_KEYを環境変数に設定してください。",
        },
        "failed": {
            "en": "Screenshot analysis failed.",
            "zh": "截图分析失败。",
            "yue": "截圖分析失敗。",
            "ko": "스크린샷 분석에 실패했습니다.",
            "ja": "スクリーンショット分析に失敗しました。",
        },
        "error": {
            "en": "An error occurred during analysis. Please try again.",
            "zh": "分析过程中发生错误，请重试。",
            "yue": "分析過程中發生錯誤，請再試一次。",
            "ko": "분석 중 오류가 발생했습니다. 다시 시도해 주세요.",
            "ja": "分析中にエラーが発生しました。もう一度お試しください。",
        },
    }

    if not openai_client:
        _e = _screenshot_err
        _nl = native_lang
        data = {
            "summary": _e["summary"].get(_nl, _e["summary"]["en"]),
            "tone_notes": _e["tone_notes"].get(_nl, _e["tone_notes"]["en"]),
            "cultural_notes": _e["cultural_notes"].get(_nl, _e["cultural_notes"]["en"]),
            "reply_options": [],
        }
        return (
            data,
            mock_usage(model, "openai"),
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
        f"{strict_language_guard()}\n"
        f"{quality_guard(native_lang)}\n"
        f"Explain in native_lang: {native_lang}. {get_output_rule(native_lang)}\n"
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
            "summary": f"string in {native_lang}",
            "tone_notes": f"string in {native_lang}",
            "relationship_vibe": f"string in {native_lang}",
            "hidden_meaning": f"string in {native_lang}",
            "cultural_notes": f"string in {native_lang}",
            "reply_options": [
                {
                    "text": "string",
                    "naturalness_score": 1,
                    "tone": "string",
                }
            ],
            "suggested_best_reply": "string",
            "reason": f"string in {native_lang}",
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

        data = repair_json_explanation_language(data, native_lang, model, temperature)
        return data, usage_from_response(response, "openai"), data.get("detected_lang") or assumed_lang

    except Exception:
        _e = _screenshot_err
        _nl = native_lang
        data = {
            "summary": _e["failed"].get(_nl, _e["failed"]["en"]),
            "tone_notes": _e["error"].get(_nl, _e["error"]["en"]),
            "reply_options": [],
        }
        data = repair_json_explanation_language(data, native_lang, model, temperature)
        return (
            data,
            mock_usage(model, "openai"),
            assumed_lang,
        )
