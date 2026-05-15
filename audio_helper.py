import io
import os
from typing import Optional

from gtts import gTTS
from langdetect import detect, DetectorFactory

from pypinyin import pinyin, Style
from hangul_romanize import Transliter
from hangul_romanize.rule import academic
import eng_to_ipa as ipa

from openai import OpenAI

try:
    import pycantonese
except Exception:
    pycantonese = None


DetectorFactory.seed = 0


def get_secret_value(key: str) -> Optional[str]:
    value = os.environ.get(key)

    try:
        import streamlit as st

        value = st.secrets.get(key) or value
    except Exception:
        pass

    return value


def get_openai_api_key() -> Optional[str]:
    return get_secret_value("OPENAI_API_KEY")


def normalize_lang(lang: Optional[str]) -> str:
    value = (lang or "").lower().strip()

    aliases = {
        "zh-cn": "zh",
        "zh_hans": "zh",
        "zh-hans": "zh",
        "mandarin": "zh",
        "cn": "zh",
        "cantonese": "yue",
        "zh-hk": "yue",
        "zh_hant": "yue",
        "zh-hant": "yue",
        "ko-kr": "ko",
        "kr": "ko",
        "en-us": "en",
        "en-au": "en",
        "en-gb": "en",
    }

    return aliases.get(value, value)


def to_pronunciation(text: str, lang: str) -> str:
    text = text or ""

    if not text.strip():
        return ""

    lang = normalize_lang(lang)

    try:
        if lang == "zh":
            pinyin_result = pinyin(text, style=Style.TONE, strict=False)

            return " ".join(
                item[0]
                for item in pinyin_result
                if item and item[0].strip()
            )

        if lang == "yue":
            if pycantonese:
                try:
                    jyutping_result = pycantonese.characters_to_jyutping(text)

                    return " ".join(
                        item[1]
                        for item in jyutping_result
                        if item and len(item) > 1 and item[1]
                    )
                except Exception:
                    pass

            return text

        if lang == "ko":
            transliter = Transliter(academic)
            result = []

            for token in text.split():
                try:
                    result.append(transliter.translit(token))
                except Exception:
                    result.append(token)

            return " ".join(result)

        if lang == "en":
            try:
                return ipa.convert(text)
            except Exception:
                return text

        detected_lang = detect(text)

        if detected_lang.startswith("zh"):
            return to_pronunciation(text, "zh")

        if detected_lang.startswith("ko"):
            return to_pronunciation(text, "ko")

        return to_pronunciation(text, "en")

    except Exception:
        return text


def synthesize_openai_tts(text: str, lang: str) -> Optional[bytes]:
    api_key = get_openai_api_key()
    text = text or ""

    if not api_key or not text.strip():
        return None

    try:
        client = OpenAI(api_key=api_key)

        response = client.audio.speech.create(
            model=get_secret_value("OPENAI_TTS_MODEL") or "gpt-4o-mini-tts",
            voice=get_secret_value("OPENAI_TTS_VOICE") or "alloy",
            input=text,
        )

        return response.read()

    except Exception:
        return None


def synthesize_gtts(text: str, lang: str) -> Optional[bytes]:
    text = text or ""

    if not text.strip():
        return None

    lang = normalize_lang(lang)

    lang_map = {
        "zh": "zh-CN",
        "en": "en",
        "ko": "ko",
    }

    tts_lang = lang_map.get(lang)

    if not tts_lang:
        return None

    try:
        tts = gTTS(text=text, lang=tts_lang)

        buffer = io.BytesIO()
        tts.write_to_fp(buffer)
        buffer.seek(0)

        return buffer.getvalue()

    except Exception:
        return None


def synthesize_tts(text: str, lang: str) -> Optional[bytes]:
    """
    Generate MP3 audio bytes.

    Priority:
    1. OpenAI TTS
    2. gTTS fallback for zh/en/ko

    Note:
    Cantonese (yue) intentionally does not fallback to gTTS zh-CN,
    because that would read Cantonese text with Mandarin pronunciation.
    """

    lang = normalize_lang(lang)
    audio = synthesize_openai_tts(text, lang)

    if audio:
        return audio

    if lang == "yue":
        return None

    return synthesize_gtts(text, lang)


def transcribe_audio(
    file_bytes: bytes,
    filename: str,
    preferred_lang: Optional[str] = None,
) -> Optional[str]:
    api_key = get_openai_api_key()

    if not api_key or not file_bytes:
        return None

    preferred_lang = normalize_lang(preferred_lang)

    whisper_lang_map = {
        "zh": "zh",
        "yue": "zh",
        "en": "en",
        "ko": "ko",
    }

    language = whisper_lang_map.get(preferred_lang)

    try:
        client = OpenAI(api_key=api_key)

        with io.BytesIO(file_bytes) as audio_file:
            audio_file.name = filename or "audio.wav"

            response = client.audio.transcriptions.create(
                model=get_secret_value("OPENAI_STT_MODEL") or "whisper-1",
                file=audio_file,
                language=language,
            )

        if hasattr(response, "text"):
            return response.text

        if isinstance(response, dict):
            return response.get("text")

        return None

    except Exception:
        return None
