import html
import json
from typing import Dict, Any, List, Tuple

import streamlit as st


UI_LANGS = ["en", "zh", "ko", "yue"]

UI_LANG_DISPLAY = {
    "en": "English",
    "zh": "简体中文",
    "ko": "한국어",
    "yue": "繁體中文 / 粵語",
}

STUDY_LANG_CODES = ["zh", "yue", "ko", "en"]

PERSONA_CODES = [
    "neutral",
    "friendly",
    "teacher",
    "strict",
]


LANG_DISPLAY_BY_UI = {
    "en": {
        "zh": "Mandarin Chinese (Simplified)",
        "yue": "Cantonese (Traditional)",
        "ko": "Korean",
        "en": "English",
        "auto": "Auto-detect",
    },
    "zh": {
        "zh": "简体中文（普通话）",
        "yue": "繁體中文（粵語）",
        "ko": "韩语",
        "en": "英语",
        "auto": "自动检测",
    },
    "ko": {
        "zh": "중국어 간체 / 보통화",
        "yue": "광둥어 / 번체 중국어",
        "ko": "한국어",
        "en": "영어",
        "auto": "자동 감지",
    },
    "yue": {
        "zh": "普通話 / 簡體中文",
        "yue": "粵語 / 繁體中文",
        "ko": "韓文",
        "en": "英文",
        "auto": "自動偵測",
    },
}


def t(key: str) -> str:
    lang = st.session_state.get("ui_lang", "en")
    return TEXTS.get(lang, TEXTS["en"]).get(key, key)


def get_lang_display() -> Dict[str, str]:
    lang = st.session_state.get("ui_lang", "en")
    return LANG_DISPLAY_BY_UI.get(lang, LANG_DISPLAY_BY_UI["en"])


def lang_label(code: str) -> str:
    return get_lang_display().get(code, code)


def persona_display(code: str) -> str:
    labels = {
        "neutral": {
            "en": "Neutral",
            "zh": "中性",
            "ko": "중립",
            "yue": "中性",
        },
        "friendly": {
            "en": "Friendly",
            "zh": "友好",
            "ko": "친근함",
            "yue": "友善",
        },
        "teacher": {
            "en": "Teacher",
            "zh": "老师风格",
            "ko": "선생님 스타일",
            "yue": "老師風格",
        },
        "strict": {
            "en": "Strict",
            "zh": "严格",
            "ko": "엄격함",
            "yue": "嚴格",
        },
    }

    lang = st.session_state.get("ui_lang", "en")
    return labels.get(code, {}).get(lang, code)


def local_levels() -> Tuple[List[str], Dict[str, str]]:
    lang = st.session_state.get("ui_lang", "en")

    if lang == "zh":
        labels = ["A1 初级", "A2 初中级", "B1 中级", "B2 中高级", "C1 高级", "C2 近母语"]
    elif lang == "ko":
        labels = ["A1 초급", "A2 초중급", "B1 중급", "B2 중상급", "C1 고급", "C2 원어민 수준"]
    elif lang == "yue":
        labels = ["A1 初學", "A2 初中級", "B1 中級", "B2 中高級", "C1 高級", "C2 接近母語"]
    else:
        labels = ["A1", "A2", "B1", "B2", "C1", "C2"]

    codes = ["a1", "a2", "b1", "b2", "c1", "c2"]
    return labels, dict(zip(labels, codes))


def local_tones() -> Tuple[List[str], Dict[str, str]]:
    lang = st.session_state.get("ui_lang", "en")

    tone_data = {
        "en": [
            ("neutral", "Neutral"),
            ("friendly", "Friendly"),
            ("polite", "Polite"),
            ("cute", "Cute"),
            ("formal", "Formal"),
            ("casual", "Casual"),
        ],
        "zh": [
            ("neutral", "中性"),
            ("friendly", "友好"),
            ("polite", "礼貌"),
            ("cute", "可爱"),
            ("formal", "正式"),
            ("casual", "随意"),
        ],
        "ko": [
            ("neutral", "중립"),
            ("friendly", "친근함"),
            ("polite", "공손함"),
            ("cute", "귀여움"),
            ("formal", "격식"),
            ("casual", "캐주얼"),
        ],
        "yue": [
            ("neutral", "中性"),
            ("friendly", "友善"),
            ("polite", "禮貌"),
            ("cute", "可愛"),
            ("formal", "正式"),
            ("casual", "隨意"),
        ],
    }

    pairs = tone_data.get(lang, tone_data["en"])
    labels = [label for _, label in pairs]
    codes = [code for code, _ in pairs]

    return labels, dict(zip(labels, codes))


def build_persona_profile(
    code: str,
    source_lang: str,
    target_lang: str,
    ui_lang: str,
) -> Dict[str, Any]:
    base = {
        "role": "You are TriLingua Bridge, a cross-cultural communication coach.",
        "source_lang": source_lang,
        "target_lang": target_lang,
        "ui_lang": ui_lang,
        "style": code,
    }

    if code == "friendly":
        base["style_hint"] = "Encouraging, concise, warm."
    elif code == "teacher":
        base["style_hint"] = "Explain simply, highlight patterns, provide 1-2 examples."
    elif code == "strict":
        base["style_hint"] = "Be direct and precise, minimal emojis."
    else:
        base["style_hint"] = "Balanced and helpful."

    return base


def inject_css():
    st.markdown(
        """
        <style>
        :root {
            --bg: #f7f8fa;
            --panel: #ffffff;
            --panel-soft: #fbfcfe;
            --text: #111827;
            --muted: #6b7280;
            --line: #e5e7eb;
            --line-strong: #d1d5db;
            --accent: #2563eb;
            --accent-soft: #eff6ff;
            --shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        }

        html, body, [data-testid="stAppViewContainer"] {
            background: var(--bg) !important;
            color: var(--text);
        }

        .block-container {
            max-width: 1040px;
            padding-top: 2.25rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3, p {
            letter-spacing: 0;
        }

        div[data-testid="stButton"] > button {
            border-radius: 8px;
            border: 1px solid var(--line-strong);
            background: #ffffff;
            color: var(--text);
            font-weight: 650;
            min-height: 42px;
            transition: border-color 0.12s ease, box-shadow 0.12s ease, transform 0.12s ease;
        }

        div[data-testid="stButton"] > button:hover {
            border-color: var(--accent);
            color: var(--accent);
            box-shadow: 0 6px 18px rgba(37, 99, 235, 0.12);
            transform: translateY(-1px);
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stNumberInput"] input {
            border-radius: 8px !important;
        }

        .hero-box {
            padding: 22px;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: var(--panel);
            box-shadow: var(--shadow);
            margin-bottom: 18px;
        }
        
        .hero-kicker {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
        }

        .hero-logo {
            width: 42px;
            height: 42px;
            flex: 0 0 42px;
            border-radius: 8px;
            background: #111827;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 850;
            font-size: 1.05rem;
            box-shadow: 0 8px 20px rgba(17, 24, 39, 0.18);
        }

        .hero-kicker-text {
            color: var(--text);
            font-size: 0.92rem;
            font-weight: 750;
            line-height: 1.25;
        }

        .hero-kicker-sub {
            color: var(--muted);
            font-size: 0.84rem;
            line-height: 1.35;
            margin-top: 2px;
        }

        .hero-title {
            font-size: 2.15rem;
            line-height: 1.12;
            font-weight: 800;
            margin-bottom: 0.35rem;
            color: var(--text);
        }

        .hero-sub {
            color: var(--muted);
            margin-bottom: 0.35rem;
            font-size: 1.02rem;
            line-height: 1.55;
        }

        .settings-card,
        .output-wrap,
        .output-card {
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 16px;
            margin: 12px 0;
            background: var(--panel);
            box-shadow: var(--shadow);
        }

        .input-wrap {
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 12px;
            background: var(--panel-soft);
            margin-bottom: 12px;
        }

        .settings-title {
            font-weight: 750;
            font-size: 1.05rem;
            margin-bottom: 4px;
            color: var(--text);
        }

        .settings-sub,
        .section-sub,
        .feature-card-sub {
            color: var(--muted);
        }

        .section-title {
            font-weight: 780;
            font-size: 1.18rem;
            margin-top: 22px;
            margin-bottom: 4px;
            color: var(--text);
        }

        .section-sub {
            margin-bottom: 14px;
            line-height: 1.5;
        }

        .feature-card {
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 16px 14px;
            min-height: 116px;
            text-align: left;
            background: var(--panel);
            margin-bottom: 8px;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.035);
            transition: border-color 0.12s ease, box-shadow 0.12s ease, transform 0.12s ease;
        }

        .feature-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 10px 26px rgba(15, 23, 42, 0.08);
            border-color: var(--accent);
        }

        .feature-card-icon {
            width: 34px;
            height: 34px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            background: var(--accent-soft);
            margin-bottom: 10px;
            font-size: 1.15rem;
        }

        .feature-card-title {
            font-weight: 750;
            font-size: 0.98rem;
            margin-bottom: 4px;
            color: var(--text);
        }

        .feature-card-sub {
            font-size: 0.86rem;
            line-height: 1.42;
        }

        .result-title {
            font-size: 1.05rem;
            font-weight: 760;
            margin: 4px 0 12px;
            color: var(--text);
        }

        .result-section-title {
            font-size: 1rem;
            font-weight: 760;
            margin: 22px 0 8px;
            color: var(--text);
        }

        .reply-card {
            display: flex;
            gap: 12px;
            border: 1px solid var(--line);
            background: #ffffff;
            border-radius: 8px;
            padding: 14px;
            margin: 10px 0;
        }

        .reply-index {
            width: 28px;
            height: 28px;
            flex: 0 0 28px;
            border-radius: 999px;
            background: var(--accent-soft);
            color: var(--accent);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 750;
            font-size: 0.9rem;
        }

        .reply-body {
            min-width: 0;
        }

        .reply-text {
            font-size: 1rem;
            line-height: 1.55;
            font-weight: 650;
            color: var(--text);
        }

        .reply-meta {
            margin-top: 6px;
            font-size: 0.86rem;
            color: var(--muted);
        }

        [data-testid="stExpander"] {
            border-radius: 8px;
            border-color: var(--line);
            background: var(--panel);
        }

        .stAlert {
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, sub: str = ""):
    title = html.escape(str(title))
    sub = html.escape(str(sub))

    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

    if sub:
        st.markdown(f'<div class="section-sub">{sub}</div>', unsafe_allow_html=True)


def hero(title: str, sub: str = "", note: str = ""):
    st.caption("DEBUG: ui_helper hero loaded")

    title = html.escape(str(title))
    sub = html.escape(str(sub))
    note = html.escape(str(note))

    note_html = ""
    if note:
        note_html = f'<div class="hero-kicker-sub">{note}</div>'

    sub_html = ""
    if sub:
        sub_html = f'<div class="hero-sub">{sub}</div>'

    html_block = (
        '<div class="hero-box">'
        '<div class="hero-kicker">'
        '<div class="hero-logo">TL</div>'
        '<div>'
        '<div class="hero-kicker-text">Mandarin · Cantonese · Korean · English</div>'
        f'{note_html}'
        '</div>'
        '</div>'
        f'<div class="hero-title">{title}</div>'
        f'{sub_html}'
        '</div>'
    )

    st.markdown(html_block, unsafe_allow_html=True)


def looks_like_json(value: str) -> bool:
    if not isinstance(value, str):
        return False

    value = value.strip()

    return (
        value.startswith("{") and value.endswith("}")
    ) or (
        value.startswith("[") and value.endswith("]")
    )


def render_structured_response(obj: Dict[str, Any]):
    st.markdown('<div class="output-card">', unsafe_allow_html=True)

    if "reply_options" in obj:
        st.markdown(f'<div class="result-title">{t("reply_options")}</div>', unsafe_allow_html=True)

        for index, option in enumerate(obj.get("reply_options", []), 1):
            if isinstance(option, dict):
                text = html.escape(str(option.get("text", "")))
                score = option.get("naturalness_score", "")
                tone = html.escape(str(option.get("tone", "")))

                meta = []
                if score not in ("", None):
                    meta.append(f'{t("naturalness_score")}: {score}')
                if tone:
                    meta.append(f'{t("feature_tone")}: {tone}')

                meta_text = " · ".join(meta)

                st.markdown(
                    f"""
                    <div class="reply-card">
                        <div class="reply-index">{index}</div>
                        <div class="reply-body">
                            <div class="reply-text">{text}</div>
                            <div class="reply-meta">{html.escape(meta_text)}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div class="reply-card">
                        <div class="reply-index">{index}</div>
                        <div class="reply-body">
                            <div class="reply-text">{html.escape(str(option))}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    section_map = [
        ("tone_notes", "tone_notes"),
        ("cultural_notes", "cultural_notes"),
        ("suggested_best_reply", "suggested_best_reply"),
        ("reason", "why_this_works"),
        ("clean_translation", "clean_translation"),
        ("summary", "summary"),
        ("recommended_understanding", "recommended_understanding"),
        ("tone_summary", "tone_summary"),
        ("intent", "intent"),
        ("tips", "tips"),
        ("clean", "corrected_version"),
        ("notes", "notes"),
        ("better_version", "better_version"),
    ]

    for data_key, text_key in section_map:
        if obj.get(data_key):
            st.markdown(f"### {t(text_key)}")
            st.write(obj[data_key])

    list_sections = [
        ("suggestions", "suggestions"),
        ("examples", "examples"),
    ]

    for data_key, text_key in list_sections:
        if obj.get(data_key):
            st.markdown(
                f'<div class="result-section-title">{html.escape(t(text_key))}</div>',
                unsafe_allow_html=True,
            )

            for item in obj[data_key]:
                st.markdown(f"- {item}")

    if obj.get("items"):
        st.markdown(f"### {t('items')}")
        for item in obj["items"]:
            if isinstance(item, dict):
                term = item.get("term", "")
                meaning = item.get("meaning", "")
                example = item.get("example", "")
                st.markdown(f"- **{term}**: {meaning}")
                if example:
                    st.caption(example)
            else:
                st.markdown(f"- {item}")

    if obj.get("key_phrases"):
        st.markdown(f"### {t('key_phrases')}")
        for item in obj["key_phrases"]:
            if isinstance(item, dict):
                phrase = item.get("phrase", "")
                meaning = item.get("meaning", "")
                note = item.get("note", "")
                st.markdown(f"- **{phrase}**: {meaning}")
                if note:
                    st.caption(note)
            else:
                st.markdown(f"- {item}")

    if obj.get("slang_pop_culture"):
        st.markdown(f"### {t('slang_pop_culture')}")
        for item in obj["slang_pop_culture"]:
            if isinstance(item, dict):
                term = item.get("term", "")
                origin = item.get("origin", "")
                note = item.get("note", "")
                st.markdown(f"- **{term}** ({origin})")
                if note:
                    st.caption(note)
            else:
                st.markdown(f"- {item}")

    if obj.get("pronunciation_guide"):
        st.markdown(f"### {t('pronunciation')}")
        pronunciation = obj["pronunciation_guide"]

        if isinstance(pronunciation, dict):
            lang = pronunciation.get("lang", "")
            text = pronunciation.get("text", "")
            st.write(f"{lang}: {text}")
        else:
            st.write(pronunciation)

    st.markdown("</div>", unsafe_allow_html=True)


def render_result(result: Any):
    if result is None:
        st.info("No result.")
        return

    if isinstance(result, str) and looks_like_json(result):
        try:
            result = json.loads(result)
        except Exception:
            pass

    if isinstance(result, dict):
        structured_keys = {
            "reply_options",
            "tone_notes",
            "cultural_notes",
            "suggested_best_reply",
            "clean_translation",
            "key_phrases",
            "slang_pop_culture",
            "summary",
            "recommended_understanding",
            "pronunciation_guide",
            "tone_summary",
            "intent",
            "tips",
            "clean",
            "notes",
            "examples",
            "suggestions",
            "better_version",
            "items",
        }

        if set(result.keys()) & structured_keys:
            render_structured_response(result)
            return

        st.json(result)
        return

    if isinstance(result, list):
        st.json(result)
        return

    st.markdown(str(result))


def show_model_caption(usage: Dict[str, Any], latency_ms: int):
    usage = usage or {}
    model = usage.get("model", "-")
    prompt_tokens = usage.get("prompt_tokens", "-")
    completion_tokens = usage.get("completion_tokens", "-")
    latency = latency_ms if latency_ms is not None else "-"

    st.caption(
        f"{t('model_info_prefix')}: {model} • "
        f"{t('tokens_label')}: {prompt_tokens}/{completion_tokens} • "
        f"{t('latency_label')}: {latency} ms"
    )


def normalize_usage(usage: Dict[str, Any]) -> Dict[str, Any]:
    usage = usage or {}

    return {
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "model": usage.get("model"),
    }


def feature_card(title: str, sub: str, icon: str = "", key: str = "") -> bool:
    safe_title = html.escape(str(title))
    safe_sub = html.escape(str(sub))
    safe_icon = html.escape(str(icon))

    st.markdown(
        f"""
        <div class="feature-card">
            <div class="feature-card-icon">{safe_icon}</div>
            <div class="feature-card-title">{safe_title}</div>
            <div class="feature-card-sub">{safe_sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return st.button(title, key=key, use_container_width=True)


TEXTS = {
    "en": {
        "app_title": "TriLingua Bridge",
        "subtitle": "A multilingual toolkit for Mandarin, Cantonese, Korean, and English.",
        "subtitle_v2": "Cross-cultural communication coach for Mandarin, Cantonese, Korean, and English.",
        "ui_language": "UI language",
        "account_title": "Account",
        "account_note": "We only store your task history locally on this app's database.",
        "username": "Username",
        "login": "Login",
        "logout": "Logout",
        "prefs_title": "Preferences",
        "my_native": "My native language",
        "i_learn": "I'm learning",
        "persona": "Persona",
        "creativity": "Creativity",
        "model": "Model",
        "ai_provider": "AI Provider",
        "show_pron": "Show pronunciation and TTS",
        "tip": "Tip: Keep inputs short and specific for best results.",
        "nav_home": "Home",
        "mode_say": "Say it better",
        "mode_say_sub": "Say something more naturally",
        "mode_mean": "What do they mean?",
        "mode_mean_sub": "Explain hidden meanings and tone",
        "mode_kpop": "Lyrics & Drama Context",
        "mode_kpop_sub": "K-pop lyrics / dramas / internet context",
        "mode_coach": "AI Chat Coach",
        "mode_coach_sub": "Culturally tuned replies",
        "feature_translate": "Translate",
        "feature_grammar": "Grammar",
        "feature_grammar_sub": "Correct mistakes with level notes",
        "feature_natural": "Natural Expression",
        "feature_natural_sub": "Make it sound native-like",
        "feature_vocab": "Vocabulary",
        "feature_vocab_sub": "Explain key words/phrases",
        "feature_tone": "Tone Analysis",
        "feature_tone_sub": "Politeness, formality, directness",
        "nav_history": "History",
        "nav_about": "About",
        "what_can": "What can it do?",
        "what_can_v2": "Your cross-cultural chat assistant",
        "what_can_sub": "Choose a task and keep your language, tone, and cultural context aligned.",
        "not_social": "This is not a social platform.",
        "back_home": "Back to Home",
        "input_text": "Enter or paste your text",
        "run": "Run",
        "enter_text_translate": "Enter text to translate",
        "translate_btn": "Translate",
        "source_language": "Source language",
        "language_of_text": "Language of the text",
        "auto_detect": "Auto-detect",
        "working": "Working...",
        "ai_call_failed": "AI call failed",
        "db_init_failed": "Database init failed",
        "history_save_failed": "Failed to save history",
        "detected_source": "Detected source",
        "pronunciation_label": "Pronunciation",
        "playing_audio": "Generating audio...",
        "tts_not_supported": "TTS not supported for this language.",
        "voice_input": "Voice input",
        "upload_audio": "Upload audio file",
        "transcribe": "Transcribe",
        "transcribing": "Transcribing...",
        "ok": "OK",
        "stt_unavailable": "Speech-to-text not available.",
        "please_upload_audio_first": "Please upload an audio file first.",
        "live_mic_note": "Record from your microphone.",
        "start_recording": "Start recording",
        "stop_recording": "Stop",
        "mic_not_installed": "Live mic not available. Install streamlit-mic-recorder.",
        "relation_mode": "Relationship / style",
        "ctx_kpop": "K-pop lyrics",
        "ctx_kdrama": "Korean drama",
        "ctx_cantodrama": "Cantonese drama",
        "ctx_cdrama": "Chinese drama",
        "ctx_eng_tv": "English TV",
        "ctx_inet": "Internet slang",
        "ctx_pop": "Pop culture",
        "context_type": "Context type",
        "enter_text_correct": "Enter text to correct",
        "correct_btn": "Correct grammar",
        "learner_level": "Learner level",
        "enter_text_natural": "Enter your draft",
        "desired_tone": "Desired tone",
        "suggest_btn": "Suggest",
        "enter_text_vocab": "Enter text to explain vocabulary",
        "max_items": "Max items",
        "explain_vocab_btn": "Explain vocabulary",
        "enter_text_tone": "Enter text to analyze tone",
        "analyze_tone_btn": "Analyze tone",
        "history_title": "History",
        "history_sub": "Your recent tasks",
        "filter_mode": "Mode",
        "filter_source": "Source",
        "filter_target": "Target",
        "search_in": "Search in history",
        "show_last": "Show last N items",
        "history_load_failed": "Failed to load history",
        "no_history": "No history yet.",
        "input_label": "Input",
        "output_label": "Output",
        "model_info_prefix": "Model",
        "tokens_label": "Tokens",
        "latency_label": "Latency",
        "about_title": "About",
        "about_desc": "TriLingua Bridge v2 — cross-cultural communication coach.",
        "enter_text_warn": "Please enter some text first.",
        "naturalness_score_title": "Naturalness Score",
        "naturalness_verdict": "Verdict",
        "naturalness_score": "Score",
        "naturalness_reason": "Why",
        "naturalness_suggestion": "More natural version",
        "region_mode": "Regional / cultural mode",
        "region_mainland_cn": "Mainland Chinese mode",
        "region_hk_yue": "Hong Kong Cantonese mode",
        "region_korean": "Korean mode",
        "region_au_en": "Australian English mode",
        "region_us_en": "American English mode",
        "screenshot_mode": "Analyze chat screenshot",
        "analyze_screenshot_btn": "Analyze screenshot",
        "upload_screenshot": "Upload a chat screenshot",
        "please_upload_image_first": "Please upload an image first.",
        "screenshot_not_available": "Screenshot analysis not available.",
        "mode_coach_v2": "AI Chat Coach",
        "mode_coach_sub_v2": "Culturally tuned replies for CN/HK/KR/AU/US",
        "style_friend": "Friend",
        "style_crush": "Crush",
        "style_work": "Work",
        "style_formal": "Formal",
        "style_cute": "Cute",
        "style_cold": "A bit cold",
        "style_kpop": "K-pop vibe",
        "style_hk": "HK local vibe",
        "reply_options": "Reply Options",
        "tone_notes": "Tone Notes",
        "cultural_notes": "Cultural Notes",
        "suggested_best_reply": "Suggested Best Reply",
        "why_this_works": "Why this works",
        "pronunciation": "Pronunciation",
        "examples": "Examples",
        "corrected_version": "Corrected Version",
        "notes": "Notes",
        "clean_translation": "Clean Translation",
        "summary": "Summary",
        "recommended_understanding": "Recommended Understanding",
        "tone_summary": "Tone Summary",
        "intent": "Intent",
        "tips": "Tips",
        "better_version": "Better Version",
        "items": "Items",
        "key_phrases": "Key Phrases",
        "slang_pop_culture": "Slang / Pop Culture",
        "suggestions": "Suggestions",
    },
    "zh": {
        "app_title": "TriLingua Bridge",
        "subtitle": "面向普通话、粤语、韩语、英语的多语言沟通工具。",
        "subtitle_v2": "跨文化沟通教练（支持普通话 / 粤语 / 韩语 / 英语）",
        "ui_language": "界面语言",
        "account_title": "账号",
        "account_note": "仅在本地数据库保存历史记录。",
        "username": "用户名",
        "login": "登录",
        "logout": "退出登录",
        "prefs_title": "偏好设置",
        "my_native": "我的母语",
        "i_learn": "我在学习",
        "persona": "人设",
        "creativity": "创造性",
        "model": "模型",
        "ai_provider": "AI 模型服务",
        "show_pron": "显示发音与朗读",
        "tip": "提示：输入越具体越好。",
        "nav_home": "首页",
        "mode_say": "更自然地表达",
        "mode_say_sub": "让你的句子听起来更自然",
        "mode_mean": "Ta 在表达什么？",
        "mode_mean_sub": "解释潜台词与语气",
        "mode_kpop": "歌词与影视语境",
        "mode_kpop_sub": "K-pop / 影视 / 网络语境解析",
        "mode_coach": "AI 聊天教练",
        "mode_coach_sub": "根据文化语境生成回复",
        "feature_translate": "翻译",
        "feature_grammar": "语法",
        "feature_grammar_sub": "按级别纠错并提示",
        "feature_natural": "自然表达",
        "feature_natural_sub": "像母语者一样表达",
        "feature_vocab": "词汇",
        "feature_vocab_sub": "解释重点词组",
        "feature_tone": "语气分析",
        "feature_tone_sub": "礼貌 / 正式 / 直接程度",
        "nav_history": "历史",
        "nav_about": "关于",
        "what_can": "能做什么？",
        "what_can_v2": "你的跨文化聊天助手",
        "what_can_sub": "选择任务，并保持语言、语气和文化语境一致。",
        "not_social": "本应用不是社交平台。",
        "back_home": "返回首页",
        "input_text": "请输入文本",
        "run": "运行",
        "enter_text_translate": "输入要翻译的文本",
        "translate_btn": "翻译",
        "source_language": "源语言",
        "language_of_text": "文本语言",
        "auto_detect": "自动检测",
        "working": "处理中...",
        "ai_call_failed": "AI 调用失败",
        "db_init_failed": "数据库初始化失败",
        "history_save_failed": "保存历史失败",
        "detected_source": "检测到的源语言",
        "pronunciation_label": "发音",
        "playing_audio": "生成语音中...",
        "tts_not_supported": "当前语言暂不支持 TTS。",
        "voice_input": "语音输入",
        "upload_audio": "上传音频文件",
        "transcribe": "转写",
        "transcribing": "转写中...",
        "ok": "完成",
        "stt_unavailable": "语音识别不可用。",
        "please_upload_audio_first": "请先上传音频文件。",
        "live_mic_note": "使用麦克风录音。",
        "start_recording": "开始录音",
        "stop_recording": "停止",
        "mic_not_installed": "未安装 streamlit-mic-recorder，无法使用麦克风录音。",
        "relation_mode": "关系 / 风格",
        "ctx_kpop": "K-pop 歌词",
        "ctx_kdrama": "韩剧台词",
        "ctx_cantodrama": "港剧对白",
        "ctx_cdrama": "国剧台词",
        "ctx_eng_tv": "英文影视",
        "ctx_inet": "网络用语",
        "ctx_pop": "流行文化",
        "context_type": "语境类型",
        "enter_text_correct": "输入要纠正的文本",
        "correct_btn": "语法纠错",
        "learner_level": "学习者级别",
        "enter_text_natural": "输入你的草稿",
        "desired_tone": "期望语气",
        "suggest_btn": "给出更自然说法",
        "enter_text_vocab": "输入文本以解释词汇",
        "max_items": "最多条目",
        "explain_vocab_btn": "解释词汇",
        "enter_text_tone": "输入文本以分析语气",
        "analyze_tone_btn": "分析语气",
        "history_title": "历史记录",
        "history_sub": "最近的任务",
        "filter_mode": "模式",
        "filter_source": "源语言",
        "filter_target": "目标语言",
        "search_in": "历史中搜索",
        "show_last": "显示最近 N 条",
        "history_load_failed": "加载历史失败",
        "no_history": "暂无历史。",
        "input_label": "输入",
        "output_label": "输出",
        "model_info_prefix": "模型",
        "tokens_label": "Tokens",
        "latency_label": "延迟",
        "about_title": "关于",
        "about_desc": "TriLingua Bridge v2 — 跨文化沟通教练。",
        "enter_text_warn": "请先输入文本。",
        "naturalness_score_title": "自然度评分",
        "naturalness_verdict": "判断",
        "naturalness_score": "分数",
        "naturalness_reason": "原因",
        "naturalness_suggestion": "更自然版本",
        "region_mode": "地区 / 文化模式",
        "region_mainland_cn": "大陆普通话模式",
        "region_hk_yue": "香港粤语模式",
        "region_korean": "韩国语模式",
        "region_au_en": "澳式英语模式",
        "region_us_en": "美式英语模式",
        "screenshot_mode": "聊天截图分析",
        "analyze_screenshot_btn": "分析截图",
        "upload_screenshot": "上传聊天截图",
        "please_upload_image_first": "请先上传图片。",
        "screenshot_not_available": "截图分析暂不可用。",
        "mode_coach_v2": "AI 聊天教练",
        "mode_coach_sub_v2": "针对大陆 / 香港 / 韩国 / 澳洲 / 美国文化风格调优",
        "style_friend": "朋友",
        "style_crush": "心动对象",
        "style_work": "同事 / 工作",
        "style_formal": "正式",
        "style_cute": "可爱",
        "style_cold": "冷一点",
        "style_kpop": "K-pop 氛围",
        "style_hk": "香港本地味",
        "reply_options": "回复建议",
        "tone_notes": "语气说明",
        "cultural_notes": "文化说明",
        "suggested_best_reply": "推荐回复",
        "why_this_works": "为什么这样回复",
        "pronunciation": "发音",
        "examples": "示例",
        "corrected_version": "纠正后的版本",
        "notes": "说明",
        "clean_translation": "自然翻译",
        "summary": "总结",
        "recommended_understanding": "推荐理解",
        "tone_summary": "语气总结",
        "intent": "意图",
        "tips": "建议",
        "better_version": "更自然版本",
        "items": "词汇条目",
        "key_phrases": "重点短语",
        "slang_pop_culture": "俚语 / 流行文化",
        "suggestions": "建议",
    },
}

TEXTS["ko"] = {
    **TEXTS["en"],
    **{
        "app_title": "TriLingua Bridge",
        "subtitle": "중국어, 광둥어, 한국어, 영어를 위한 다국어 소통 도구.",
        "subtitle_v2": "중국어 / 광둥어 / 한국어 / 영어를 위한 다문화 커뮤니케이션 코치.",
        "ui_language": "인터페이스 언어",
        "account_title": "계정",
        "account_note": "작업 기록은 이 앱의 로컬 데이터베이스에만 저장됩니다.",
        "username": "사용자명",
        "login": "로그인",
        "logout": "로그아웃",
        "prefs_title": "설정",
        "my_native": "모국어",
        "i_learn": "학습 언어",
        "persona": "페르소나",
        "creativity": "창의성",
        "model": "모델",
        "ai_provider": "AI 제공자",
        "show_pron": "발음과 TTS 표시",
        "tip": "팁: 입력은 짧고 구체적일수록 좋아요.",

        "nav_home": "홈",
        "back_home": "홈으로 돌아가기",
        "nav_history": "기록",
        "nav_about": "소개",

        "what_can": "무엇을 할 수 있나요?",
        "what_can_v2": "나만의 다문화 채팅 도우미",
        "what_can_sub": "작업을 선택하고 언어, 말투, 문화적 맥락을 맞춰 보세요.",
        "not_social": "이 앱은 소셜 플랫폼이 아닙니다.",

        "mode_say": "더 자연스럽게 말하기",
        "mode_say_sub": "문장을 더 자연스럽게 표현해요",
        "mode_mean": "무슨 뜻일까요?",
        "mode_mean_sub": "숨은 의미와 말투를 설명해요",
        "mode_kpop": "가사와 드라마 맥락",
        "mode_kpop_sub": "K-pop / 드라마 / 인터넷 맥락 설명",
        "mode_coach": "AI 채팅 코치",
        "mode_coach_sub": "문화 맥락에 맞춘 답장",
        "mode_coach_v2": "AI 채팅 코치",
        "mode_coach_sub_v2": "중국 / 홍콩 / 한국 / 호주 / 미국 문화에 맞춘 답장",

        "feature_translate": "번역",
        "feature_grammar": "문법",
        "feature_grammar_sub": "수준에 맞춰 문법을 교정해요",
        "feature_natural": "자연스러운 표현",
        "feature_natural_sub": "원어민처럼 자연스럽게 바꿔요",
        "feature_vocab": "어휘",
        "feature_vocab_sub": "핵심 단어와 표현을 설명해요",
        "feature_tone": "말투 분석",
        "feature_tone_sub": "공손함 / 격식 / 직접성을 분석해요",

        "input_text": "텍스트를 입력하거나 붙여넣으세요",
        "run": "실행",
        "enter_text_translate": "번역할 텍스트를 입력하세요",
        "translate_btn": "번역",
        "source_language": "원문 언어",
        "language_of_text": "텍스트 언어",
        "auto_detect": "자동 감지",
        "working": "처리 중...",
        "ai_call_failed": "AI 호출 실패",
        "db_init_failed": "데이터베이스 초기화 실패",
        "history_save_failed": "기록 저장 실패",
        "detected_source": "감지된 원문 언어",

        "voice_input": "음성 입력",
        "upload_audio": "오디오 파일 업로드",
        "transcribe": "전사",
        "transcribing": "전사 중...",
        "ok": "완료",
        "stt_unavailable": "음성 인식을 사용할 수 없습니다.",
        "please_upload_audio_first": "먼저 오디오 파일을 업로드하세요.",
        "live_mic_note": "마이크로 녹음하세요.",
        "start_recording": "녹음 시작",
        "stop_recording": "정지",
        "mic_not_installed": "streamlit-mic-recorder가 설치되지 않았습니다.",

        "pronunciation_label": "발음",
        "playing_audio": "음성 생성 중...",
        "tts_not_supported": "이 언어는 TTS를 지원하지 않습니다.",

        "relation_mode": "관계 / 스타일",
        "style_friend": "친구",
        "style_crush": "썸 / 호감 상대",
        "style_work": "직장 / 업무",
        "style_formal": "격식",
        "style_cute": "귀여움",
        "style_cold": "조금 차갑게",
        "style_kpop": "K-pop 느낌",
        "style_hk": "홍콩 로컬 느낌",

        "ctx_kpop": "K-pop 가사",
        "ctx_kdrama": "한국 드라마",
        "ctx_cantodrama": "홍콩 드라마",
        "ctx_cdrama": "중국 드라마",
        "ctx_eng_tv": "영어권 영상",
        "ctx_inet": "인터넷 표현",
        "ctx_pop": "대중문화",
        "context_type": "맥락 유형",

        "enter_text_correct": "교정할 텍스트를 입력하세요",
        "correct_btn": "문법 교정",
        "learner_level": "학습자 레벨",
        "enter_text_natural": "초안을 입력하세요",
        "desired_tone": "원하는 말투",
        "suggest_btn": "제안하기",
        "enter_text_vocab": "어휘를 설명할 텍스트를 입력하세요",
        "max_items": "최대 항목 수",
        "explain_vocab_btn": "어휘 설명",
        "enter_text_tone": "말투를 분석할 텍스트를 입력하세요",
        "analyze_tone_btn": "말투 분석",

        "history_title": "기록",
        "history_sub": "최근 작업",
        "filter_mode": "모드",
        "filter_source": "원문",
        "filter_target": "목표",
        "filter_persona": "페르소나",
        "search_in": "기록 검색",
        "show_last": "최근 N개 표시",
        "history_load_failed": "기록 불러오기 실패",
        "no_history": "아직 기록이 없습니다.",
        "input_label": "입력",
        "output_label": "출력",

        "model_info_prefix": "모델",
        "tokens_label": "토큰",
        "latency_label": "지연 시간",

        "about_title": "소개",
        "about_desc": "TriLingua Bridge v2 — 다문화 커뮤니케이션 코치.",
        "enter_text_warn": "먼저 텍스트를 입력하세요.",

        "naturalness_score_title": "자연스러움 점수",
        "naturalness_verdict": "판단",
        "naturalness_score": "점수",
        "naturalness_reason": "이유",
        "naturalness_suggestion": "더 자연스러운 표현",

        "region_mode": "지역 / 문화 모드",
        "region_mainland_cn": "중국 본토 모드",
        "region_hk_yue": "홍콩 광둥어 모드",
        "region_korean": "한국어 모드",
        "region_au_en": "호주 영어 모드",
        "region_us_en": "미국 영어 모드",

        "screenshot_mode": "채팅 스크린샷 분석",
        "analyze_screenshot_btn": "스크린샷 분석",
        "upload_screenshot": "채팅 스크린샷 업로드",
        "please_upload_image_first": "먼저 이미지를 업로드하세요.",
        "screenshot_not_available": "스크린샷 분석을 사용할 수 없습니다.",

        "reply_options": "답장 추천",
        "tone_notes": "말투 설명",
        "cultural_notes": "문화 설명",
        "suggested_best_reply": "추천 답장",
        "why_this_works": "이 답장이 자연스러운 이유",
        "pronunciation": "발음",
        "examples": "예문",
        "corrected_version": "수정된 문장",
        "notes": "설명",
        "clean_translation": "자연스러운 번역",
        "summary": "요약",
        "recommended_understanding": "추천 이해",
        "tone_summary": "말투 요약",
        "intent": "의도",
        "tips": "팁",
        "better_version": "더 자연스러운 표현",
        "items": "항목",
        "key_phrases": "핵심 표현",
        "slang_pop_culture": "속어 / 대중문화",
        "suggestions": "제안",
    },
}

TEXTS["yue"] = {
    **TEXTS["zh"],
    **{
        "subtitle": "面向普通話、粵語、韓文、英文嘅多語言溝通工具。",
        "subtitle_v2": "跨文化溝通教練（支援普通話 / 粵語 / 韓文 / 英文）",
        "ui_language": "介面語言",
        "account_title": "帳號",
        "account_note": "只會喺本地資料庫保存歷史記錄。",
        "username": "用戶名",
        "login": "登入",
        "logout": "登出",
        "prefs_title": "偏好設定",
        "my_native": "我嘅母語",
        "i_learn": "我想學",
        "creativity": "創意度",
        "ai_provider": "AI 模型服務",
        "show_pron": "顯示發音同朗讀",
        "what_can_v2": "你嘅跨文化聊天助手",
        "what_can_sub": "揀一個任務，保持語言、語氣同文化語境一致。",
        "mode_coach": "AI 聊天教練",
        "mode_coach_sub": "按文化語境生成回覆",
        "mode_coach_v2": "AI 聊天教練",
        "mode_coach_sub_v2": "針對大陸 / 香港 / 韓國 / 澳洲 / 美國文化風格調整",
        "feature_translate": "翻譯",
        "feature_grammar": "文法",
        "feature_natural": "自然表達",
        "feature_vocab": "詞彙",
        "feature_tone": "語氣分析",
        "nav_history": "歷史",
        "nav_about": "關於",
        "run": "運行",
        "translate_btn": "翻譯",
        "filter_target": "目標語言",
        "reply_options": "回覆建議",
        "tone_notes": "語氣說明",
        "cultural_notes": "文化說明",
        "suggested_best_reply": "推薦回覆",
        "why_this_works": "點解咁回",
        "pronunciation": "發音",
        "summary": "總結",
        "suggestions": "建議",
    },
}
