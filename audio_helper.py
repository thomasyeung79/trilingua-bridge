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


def to_pronunciation(text: str, lang: str) -> str:
    """
    Convert text into pronunciation guide.

    zh  -> Mandarin Pinyin
    yue -> Cantonese Jyutping
    ko  -> Korean Romanization
    en  -> English IPA
    """

    text = text or ""

    if not text.strip():
        return ""

    lang = (lang or "").lower()

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


def synthesize_tts(text: str, lang: str) -> Optional[bytes]:
    """
    Generate MP3 audio bytes using gTTS.

    Note:
    gTTS does not have strong Cantonese support.
    For yue, this version falls back to zh-CN.
    """

    text = text or ""

    if not text.strip():
        return None

    lang_map = {
        "zh": "zh-CN",
        "yue": "zh-CN",
        "en": "en",
        "ko": "ko",
    }

    tts_lang = lang_map.get((lang or "").lower())

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


def get_openai_api_key() -> Optional[str]:
    """
    Get OpenAI API key from Streamlit secrets or environment variable.
    """

    api_key = os.environ.get("OPENAI_API_KEY")

    try:
        import streamlit as st

        api_key = st.secrets.get("OPENAI_API_KEY") or api_key

    except Exception:
        pass

    return api_key


def transcribe_audio(
    file_bytes: bytes,
    filename: str,
    preferred_lang: Optional[str] = None,
) -> Optional[str]:
    """
    Transcribe audio using OpenAI Whisper API.

    yue is passed as zh because Whisper language parameter
    does not always support Cantonese as a separate code.
    """

    api_key = get_openai_api_key()

    if not api_key:
        return None

    client = OpenAI(api_key=api_key)

    whisper_lang_map = {
        "zh": "zh",
        "yue": "zh",
        "en": "en",
        "ko": "ko",
    }

    language = whisper_lang_map.get((preferred_lang or "").lower())

    try:
        with io.BytesIO(file_bytes) as audio_file:
            audio_file.name = filename or "audio.wav"

            response = client.audio.transcriptions.create(
                model="whisper-1",
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
