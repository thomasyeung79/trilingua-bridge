import os
import json
import time
from typing import Dict, Any, Callable, Optional


import streamlit as st
from dotenv import load_dotenv

try:
    from streamlit_mic_recorder import mic_recorder
    MIC_SUPPORTED = True
except Exception:
    mic_recorder = None
    MIC_SUPPORTED = False

from ui_helper import (
    TEXTS,
    UI_LANGS,
    UI_LANG_DISPLAY,
    STUDY_LANG_CODES,
    PERSONA_CODES,
    t,
    get_lang_display,
    persona_display,
    local_levels,
    local_tones,
    build_persona_profile,
    inject_css,
    section_header,
    hero,
    render_result,
    show_model_caption,
    normalize_usage,
    lang_label,
    feature_card,
)

from db_helper import init_db, ensure_history_columns, insert_history, fetch_history

from ai_helper import (
    translate_text,
    correct_grammar,
    suggest_natural_expression,
    explain_vocabulary,
    analyze_tone,
    chat_reply_coach_advanced,
    media_context_explain,
    explain_message_meaning,
    detect_language_simple,
)

try:
    from ai_helper import analyze_screenshot_chat
    HAVE_SCREENSHOT_ANALYZE = True
except Exception:
    analyze_screenshot_chat = None
    HAVE_SCREENSHOT_ANALYZE = False

from audio_helper import (
    to_pronunciation,
    synthesize_tts,
    transcribe_audio,
)


load_dotenv()

st.set_page_config(
    page_title="TriLingua Bridge",
    layout="centered",
    initial_sidebar_state="collapsed",
)

inject_css()

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        display: none;
    }

    [data-testid="collapsedControl"] {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================
# Initial State
# =========================

def init_state():
    defaults = {
        "ui_lang": "en",
        "page": "Home",
        "username": "",
        "native_lang": "zh",
        "target_lang": "ko",
        "persona_code": PERSONA_CODES[0],
        "temperature": 0.4,
        "model_input": "gpt-4o-mini",
        "ai_provider": "auto",
        "show_pron": False,
        "coach_region_mode": "cn-mainland",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


# =========================
# Database
# =========================

try:
    init_db()
    ensure_history_columns()
except Exception as e:
    st.warning(f"{t('db_init_failed')}: {e}")


# =========================
# Utilities
# =========================

def go_home_button():
    col1, col2 = st.columns([1, 3])

    with col1:
        if st.button(f"🏠 {t('back_home')}", use_container_width=True):
            st.session_state.page = "Home"
            st.rerun()

    with col2:
        display = get_lang_display()
        native_label = display.get(st.session_state.native_lang, st.session_state.native_lang)
        target_label = display.get(st.session_state.target_lang, st.session_state.target_lang)
        st.caption(
            f"{st.session_state.username} · "
            f"{native_label} → {target_label} · "
            f"{persona_display(st.session_state.persona_code)}"
        )


def get_persona_profile(source_lang: str, target_lang: str) -> Dict[str, Any]:
    return build_persona_profile(
        code=st.session_state.persona_code,
        source_lang=source_lang,
        target_lang=target_lang,
        ui_lang=st.session_state.ui_lang,
    )


def lang_for_stt(lang_code: Optional[str]) -> Optional[str]:
    if not lang_code or lang_code == "auto":
        return None

    if lang_code == "yue":
        return "zh"

    return lang_code


def run_ai_task(
    task_fn: Callable[..., Any],
    task_kwargs: Dict[str, Any],
    history_kwargs: Dict[str, Any],
    pron_lang: Optional[str] = None,
):
    start = time.perf_counter()

    try:
        with st.spinner(t("working")):
            output = task_fn(**task_kwargs)
    except Exception as e:
        st.error(f"{t('ai_call_failed')}: {e}")
        return None

    usage: Dict[str, Any] = {}
    detected = None

    if isinstance(output, tuple) and len(output) == 3:
        result, usage, detected = output

        if detected:
            usage = usage or {}
            usage["detected_lang"] = detected

            if history_kwargs.get("source_lang") == "auto":
                history_kwargs["source_lang"] = detected

    elif isinstance(output, tuple) and len(output) == 2:
        result, usage = output
    else:
        result = output

    usage = usage or {}
    latency_ms = int((time.perf_counter() - start) * 1000)

    st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
    render_result(result)

    if usage.get("detected_lang"):
        display = get_lang_display()
        detected_lang = usage["detected_lang"]
        st.caption(
            f"{t('detected_source')}: "
            f"{display.get(detected_lang, detected_lang)}"
        )

    output_lang_for_pron = (
        pron_lang
        or history_kwargs.get("target_lang")
        or history_kwargs.get("source_lang")
    )

    if (
        st.session_state.get("show_pron")
        and isinstance(result, str)
        and output_lang_for_pron in ("zh", "yue", "ko", "en")
    ):
        st.markdown(f"**{t('pronunciation_label')}**")
        st.write(to_pronunciation(result, output_lang_for_pron))

        if len(result) <= 800:
            with st.spinner(t("playing_audio")):
                audio_bytes = synthesize_tts(result, output_lang_for_pron)

            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")
            else:
                st.warning(t("tts_not_supported"))
        else:
            st.caption("Text too long for TTS. Use shorter text.")

    show_model_caption(usage, latency_ms)
    st.markdown("</div>", unsafe_allow_html=True)

    try:
        normalized_usage = normalize_usage(usage)

        insert_history(
            username=history_kwargs["username"],
            mode=history_kwargs["mode"],
            source_lang=history_kwargs["source_lang"],
            target_lang=history_kwargs["target_lang"],
            native_lang=history_kwargs["native_lang"],
            persona=history_kwargs["persona_code"],
            ui_lang=history_kwargs["ui_lang"],
            user_input=history_kwargs["user_input"],
            ai_output=(
                result
                if isinstance(result, str)
                else json.dumps(result, ensure_ascii=False)
            ),
            tokens_input=normalized_usage.get("prompt_tokens"),
            tokens_output=normalized_usage.get("completion_tokens"),
            model=normalized_usage.get("model"),
            latency_ms=latency_ms,
        )

    except Exception as e:
        st.warning(f"{t('history_save_failed')}: {e}")

    return result, usage


def voice_input_ui(text_area_key: str):
    with st.expander(f"🎙️ {t('voice_input')}", expanded=False):
        lang_option = st.selectbox(
            t("language_of_text"),
            ["auto"] + STUDY_LANG_CODES,
            index=0,
            format_func=lambda code: (
                t("auto_detect")
                if code == "auto"
                else get_lang_display().get(code, code)
            ),
            key=f"voice_lang_{text_area_key}",
        )

        uploaded_file = st.file_uploader(
            t("upload_audio"),
            type=["wav", "mp3", "m4a", "webm"],
            key=f"upload_{text_area_key}",
        )

        if st.button(t("transcribe"), key=f"transcribe_{text_area_key}"):
            if not uploaded_file:
                msg = TEXTS.get(st.session_state.ui_lang, {}).get(
                    "please_upload_audio_first",
                    "Please upload an audio file first.",
                )
                st.warning(msg)
            else:
                with st.spinner(t("transcribing")):
                    audio_data = uploaded_file.read()
                    transcript = transcribe_audio(
                        audio_data,
                        uploaded_file.name,
                        lang_for_stt(lang_option),
                    )

                if transcript:
                    st.session_state[text_area_key] = transcript
                    st.success(t("ok"))
                    st.rerun()
                else:
                    st.warning(t("stt_unavailable"))

        st.markdown("---")

        st.caption(
            TEXTS.get(st.session_state.ui_lang, {}).get(
                "live_mic_note",
                "Record from microphone.",
            )
        )

        if MIC_SUPPORTED:
            mic_data = mic_recorder(
                start_prompt=TEXTS.get(st.session_state.ui_lang, {}).get(
                    "start_recording",
                    "Start recording",
                ),
                stop_prompt=TEXTS.get(st.session_state.ui_lang, {}).get(
                    "stop_recording",
                    "Stop",
                ),
                just_once=True,
                format="wav",
                key=f"mic_{text_area_key}",
            )

            if mic_data and isinstance(mic_data, dict) and mic_data.get("bytes"):
                st.audio(mic_data["bytes"], format="audio/wav")

                with st.spinner(t("transcribing")):
                    transcript = transcribe_audio(
                        mic_data["bytes"],
                        "mic.wav",
                        lang_for_stt(lang_option),
                    )

                if transcript:
                    st.session_state[text_area_key] = transcript
                    st.success(t("ok"))
                    st.rerun()
                else:
                    st.warning(t("stt_unavailable"))

        else:
            st.info(
                TEXTS.get(st.session_state.ui_lang, {}).get(
                    "mic_not_installed",
                    "Live mic not available. Install streamlit-mic-recorder.",
                )
            )


# =========================
# Regional / Cultural Coach
# =========================

REGION_OPTIONS = [
    ("cn-mainland", "region_mainland_cn"),
    ("hk-cantonese", "region_hk_yue"),
    ("kr", "region_korean"),
    ("au-en", "region_au_en"),
    ("us-en", "region_us_en"),
]


def region_label(code: str) -> str:
    key_map = dict(REGION_OPTIONS)
    key = key_map.get(code, code)
    return TEXTS.get(st.session_state.ui_lang, {}).get(key, code)


def build_region_guidelines(region_code: str, target_lang: str) -> str:
    if region_code == "cn-mainland":
        return (
            "Mainland Chinese mode: Use Mandarin-friendly wording, moderate politeness, "
            "limited emojis, indirect suggestions, concise 1–3 sentences."
        )

    if region_code == "hk-cantonese":
        return (
            "Hong Kong Cantonese mode: Use Cantonese expressions with Traditional Chinese, "
            "casual but polite tone, light emojis ok, direct but friendly."
        )

    if region_code == "kr":
        return (
            "Korean mode: Adapt honorifics properly, polite endings if not close, "
            "avoid excessive emojis, indirect yet clear."
        )

    if region_code == "au-en":
        return (
            "Australian English mode: Friendly, relaxed phrasing, light emoji ok, "
            "direct yet casual tone."
        )

    if region_code == "us-en":
        return (
            "American English mode: Friendly, upbeat tone, clear and direct wording."
        )

    return "Adjust wording, politeness, emoji use, directness, length, and tone appropriately."


# =========================
# Naturalness
# =========================

def detect_language_code(
    text: str,
    model: str,
    temperature: float,
    persona_profile: Dict[str, Any],
) -> Optional[str]:
    return detect_language_simple(
        text=text,
        model=model,
        temperature=temperature,
        persona_profile=persona_profile,
    )


def evaluate_naturalness(
    sentence: str,
    eval_lang: str,
    native_lang: str,
    model: str,
    temperature: float,
    persona_profile: Dict[str, Any],
) -> Dict[str, Any]:
    prompt = (
        "Task: Evaluate how natural this sentence sounds.\n"
        "Return ONLY valid JSON with keys: verdict, score, reason, suggestion.\n"
        "verdict must be one of: natural, somewhat_natural, machine_translated.\n"
        "score must be an integer from 1 to 10.\n"
        "reason should be in the user's native language.\n"
        "suggestion should be a more natural version in the same language as the sentence.\n\n"
        f"User native language: {native_lang}\n"
        f"Sentence language: {eval_lang}\n\n"
        f"Sentence:\n{sentence}"
    )

    out = translate_text(
        text=prompt,
        source_lang="en",
        target_lang=native_lang,
        native_lang=native_lang,
        temperature=max(0.0, min(temperature, 0.5)),
        model=model,
        persona_profile=persona_profile,
    )

    content = out[0] if isinstance(out, tuple) else out

    data = {
        "verdict": "",
        "score": None,
        "reason": "",
        "suggestion": "",
    }

    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            data.update(
                {
                    "verdict": parsed.get("verdict", ""),
                    "score": parsed.get("score", None),
                    "reason": parsed.get("reason", ""),
                    "suggestion": parsed.get("suggestion", ""),
                }
            )
    except Exception:
        data["verdict"] = "somewhat_natural"
        data["score"] = 6
        data["reason"] = str(content)[:200]
        data["suggestion"] = ""

    return data


def render_naturalness_panel(title: str, eval_data: Dict[str, Any]):
    verdict = eval_data.get("verdict") or "-"

    try:
        score = int(eval_data.get("score")) if eval_data.get("score") is not None else "-"
    except Exception:
        score = "-"

    reason = eval_data.get("reason") or "-"
    suggestion = eval_data.get("suggestion") or ""

    st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
    st.markdown(f"**{title}**")
    st.write(
        f"{TEXTS.get(st.session_state.ui_lang, {}).get('naturalness_verdict', 'Verdict')}: {verdict}"
    )
    st.write(
        f"{TEXTS.get(st.session_state.ui_lang, {}).get('naturalness_score', 'Score')}: {score}"
    )
    st.write(
        f"{TEXTS.get(st.session_state.ui_lang, {}).get('naturalness_reason', 'Why')}: {reason}"
    )

    if suggestion:
        st.write(
            TEXTS.get(st.session_state.ui_lang, {}).get(
                "naturalness_suggestion",
                "More natural version",
            )
        )
        st.markdown(suggestion)

    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Home Dashboard
# =========================

def render_home_dashboard():
    st.caption("DEBUG: app render_home_dashboard loaded")
    
    hero(
        t("app_title"),
        TEXTS.get(st.session_state.ui_lang, {}).get("subtitle_v2", t("subtitle")),
        t("not_social"),
    )

    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="settings-title">{t("account_title")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="settings-sub">{t("account_note")}</div>',
        unsafe_allow_html=True,
    )

    col_user, col_login, col_logout = st.columns([3, 1, 1])

    with col_user:
        username_input = st.text_input(
            t("username"),
            value=st.session_state.username,
            key="home_username_input",
        )

    with col_login:
        if st.button(t("login"), use_container_width=True, key="home_login_btn"):
            st.session_state.username = username_input.strip()
            st.rerun()

    with col_logout:
        if st.session_state.username:
            if st.button(t("logout"), use_container_width=True, key="home_logout_btn"):
                st.session_state.username = ""
                st.rerun()

    if st.session_state.username:
        st.success(f"{t('username')}: {st.session_state.username}")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="settings-title">{t("prefs_title")}</div>',
        unsafe_allow_html=True,
    )

    ui_options = [UI_LANG_DISPLAY[code] for code in UI_LANGS]
    current_ui_index = UI_LANGS.index(st.session_state.ui_lang)

    col1, col2, col3 = st.columns(3)

    with col1:
        selected_ui_label = st.selectbox(
            t("ui_language"),
            ui_options,
            index=current_ui_index,
            key="home_ui_lang_select",
        )
        selected_ui_code = UI_LANGS[ui_options.index(selected_ui_label)]

        if selected_ui_code != st.session_state.ui_lang:
            st.session_state.ui_lang = selected_ui_code
            st.rerun()

    with col2:
        native_lang = st.selectbox(
            t("my_native"),
            STUDY_LANG_CODES,
            index=STUDY_LANG_CODES.index(st.session_state.native_lang),
            format_func=lang_label,
            key="home_native_lang_select",
        )
        st.session_state.native_lang = native_lang

    with col3:
        target_lang = st.selectbox(
            t("i_learn"),
            STUDY_LANG_CODES,
            index=STUDY_LANG_CODES.index(st.session_state.target_lang),
            format_func=lang_label,
            key="home_target_lang_select",
        )
        st.session_state.target_lang = target_lang

    col4, col5, col6 = st.columns(3)

    with col4:
        persona_code = st.selectbox(
            t("persona"),
            PERSONA_CODES,
            index=PERSONA_CODES.index(st.session_state.persona_code),
            format_func=persona_display,
            key="home_persona_code_select",
        )
        st.session_state.persona_code = persona_code

    with col5:
        temperature = st.slider(
            t("creativity"),
            0.0,
            1.0,
            st.session_state.temperature,
            0.1,
            key="home_temperature_slider",
        )
        st.session_state.temperature = temperature

    with col6:
        show_pron = st.checkbox(
            t("show_pron"),
            value=st.session_state.show_pron,
            key="home_show_pron_checkbox",
        )
        st.session_state.show_pron = show_pron

    provider_options = ["auto", "openai", "deepseek"]

    ai_provider = st.selectbox(
        "AI Provider",
        provider_options,
        index=provider_options.index(st.session_state.ai_provider),
        format_func=lambda value: {
            "auto": "Auto: OpenAI first, DeepSeek fallback",
            "openai": "OpenAI",
            "deepseek": "DeepSeek",
        }.get(value, value),
        key="home_ai_provider_select",
    )

    st.session_state.ai_provider = ai_provider
    os.environ["AI_PROVIDER"] = ai_provider

    model = st.text_input(
        t("model"),
        value=st.session_state.model_input,
        key="home_model_input_text",
    )
    st.session_state.model_input = model

    st.caption(t("tip"))
    st.markdown("</div>", unsafe_allow_html=True)

    if not st.session_state.username:
        st.info(t("account_note"))
        return

    section_header(
        TEXTS.get(st.session_state.ui_lang, {}).get("what_can_v2", t("what_can")),
        t("what_can_sub"),
    )

    col1, col2, col3 = st.columns(3)

    with col2:
        if feature_card(
            TEXTS.get(st.session_state.ui_lang, {}).get("mode_coach_v2", t("mode_coach")),
            TEXTS.get(st.session_state.ui_lang, {}).get("mode_coach_sub_v2", t("mode_coach_sub")),
            "🎯",
            key="card_coach_v2",
        ):
            st.session_state.page = "Coach"
            st.rerun()

    col4, col5, col6 = st.columns(3)

    with col4:
        if feature_card(t("mode_say"), t("mode_say_sub"), "🗣️", key="card_say"):
            st.session_state.page = "Say"
            st.rerun()

    with col5:
        if feature_card(t("mode_mean"), t("mode_mean_sub"), "❓", key="card_mean"):
            st.session_state.page = "Mean"
            st.rerun()

    with col6:
        if feature_card(t("mode_kpop"), t("mode_kpop_sub"), "🎵", key="card_media"):
            st.session_state.page = "Kpop"
            st.rerun()

    col7, col8, col9 = st.columns(3)

    with col7:
        if feature_card(t("feature_translate"), t("tip"), "🌐", key="card_translate"):
            st.session_state.page = "Translate"
            st.rerun()

    with col8:
        if feature_card(t("feature_grammar"), t("feature_grammar_sub"), "✍️", key="card_grammar"):
            st.session_state.page = "Grammar"
            st.rerun()

    with col9:
        if feature_card(t("feature_natural"), t("feature_natural_sub"), "🎯", key="card_natural"):
            st.session_state.page = "Natural"
            st.rerun()

    col10, col11, col12 = st.columns(3)

    with col10:
        if feature_card(t("feature_vocab"), t("feature_vocab_sub"), "📚", key="card_vocab"):
            st.session_state.page = "Vocabulary"
            st.rerun()

    with col11:
        if feature_card(t("feature_tone"), t("feature_tone_sub"), "🗣️", key="card_tone"):
            st.session_state.page = "Tone"
            st.rerun()

    with col12:
        if feature_card(t("nav_history"), t("history_sub"), "🕘", key="card_history"):
            st.session_state.page = "History"
            st.rerun()

    if st.button(f"ℹ️ {t('nav_about')}", use_container_width=True, key="card_about"):
        st.session_state.page = "About"
        st.rerun()


# =========================
# Page Routing
# =========================

page = st.session_state.page
username = st.session_state.username
native_lang = st.session_state.native_lang
target_lang = st.session_state.target_lang
persona_code = st.session_state.persona_code
temperature = st.session_state.temperature
model = st.session_state.model_input

if page != "Home" and not username:
    st.session_state.page = "Home"
    st.rerun()


if page == "Home":
    render_home_dashboard()


elif page in ["Say", "Translate"]:
    go_home_button()

    if page == "Say":
        section_header(t("mode_say"), t("mode_say_sub"))
        text_key = "say_text"
        mode_name = "say"
        button_label = t("run")
        text_label = t("input_text")
    else:
        section_header(t("feature_translate"), t("tip"))
        text_key = "translate_text"
        mode_name = "translate"
        button_label = t("translate_btn")
        text_label = t("enter_text_translate")

    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(text_label, height=180, key=text_key)
    st.markdown("</div>", unsafe_allow_html=True)

    voice_input_ui(text_key)

    col1, col2, col3 = st.columns(3)

    with col1:
        source_choice = st.selectbox(
            t("source_language"),
            ["auto"] + STUDY_LANG_CODES,
            index=0,
            format_func=lambda code: (
                t("auto_detect")
                if code == "auto"
                else get_lang_display().get(code, code)
            ),
            key=f"{mode_name}_source_lang",
        )

    with col2:
        page_target_lang = st.selectbox(
            t("filter_target"),
            STUDY_LANG_CODES,
            index=STUDY_LANG_CODES.index(target_lang),
            format_func=lambda code: get_lang_display().get(code, code),
            key=f"{mode_name}_target_lang",
        )

    with col3:
        run_button = st.button(button_label, use_container_width=True)

    if run_button:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            persona_profile = get_persona_profile(source_choice, page_target_lang)

            run_ai_task(
                task_fn=translate_text,
                task_kwargs=dict(
                    text=text,
                    source_lang=source_choice,
                    target_lang=page_target_lang,
                    native_lang=native_lang,
                    temperature=temperature,
                    model=model,
                    persona_profile=persona_profile,
                ),
                history_kwargs=dict(
                    username=username,
                    mode=mode_name,
                    source_lang=source_choice,
                    target_lang=page_target_lang,
                    native_lang=native_lang,
                    persona_code=persona_code,
                    ui_lang=st.session_state.ui_lang,
                    user_input=text,
                ),
                pron_lang=page_target_lang,
            )


elif page in ["Mean", "Coach", "Kpop"]:
    go_home_button()

    title_map = {
        "Mean": t("mode_mean"),
        "Coach": TEXTS.get(st.session_state.ui_lang, {}).get("mode_coach_v2", t("mode_coach")),
        "Kpop": t("mode_kpop"),
    }

    sub_map = {
        "Mean": t("mode_mean_sub"),
        "Coach": TEXTS.get(st.session_state.ui_lang, {}).get("mode_coach_sub_v2", t("mode_coach_sub")),
        "Kpop": t("mode_kpop_sub"),
    }

    mode_map = {
        "Mean": "mean",
        "Coach": "coach",
        "Kpop": "kpop",
    }

    section_header(title_map[page], sub_map[page])

    text_key = f"{mode_map[page]}_text"

    if page == "Coach":
        region_code = st.session_state.get("coach_region_mode", "cn-mainland")

        reg_col1, reg_col2 = st.columns([2, 2])

        with reg_col1:
            region_code = st.selectbox(
                TEXTS.get(st.session_state.ui_lang, {}).get("region_mode", "Regional mode"),
                [code for code, _ in REGION_OPTIONS],
                index=(
                    [code for code, _ in REGION_OPTIONS].index(region_code)
                    if region_code in [code for code, _ in REGION_OPTIONS]
                    else 0
                ),
                format_func=region_label,
                key="coach_region_mode",
            )

        with reg_col2:
            styles = [
                t("style_friend"),
                t("style_crush"),
                t("style_work"),
                t("style_formal"),
                t("style_cute"),
                t("style_cold"),
                t("style_kpop"),
                t("style_hk"),
            ]

            reply_style = st.selectbox(
                t("relation_mode"),
                styles,
                index=0,
                key="coach_style_select",
            )

    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("input_text"), height=180, key=text_key)
    st.markdown("</div>", unsafe_allow_html=True)

    voice_input_ui(text_key)

    if page == "Kpop":
        col1, col2 = st.columns(2)

        with col1:
            source_choice = st.selectbox(
                t("language_of_text"),
                ["auto"] + STUDY_LANG_CODES,
                index=0,
                format_func=lambda code: (
                    t("auto_detect")
                    if code == "auto"
                    else get_lang_display().get(code, code)
                ),
                key="media_source_lang",
            )

        with col2:
            ctx_type = st.selectbox(
                t("context_type"),
                [
                    t("ctx_kpop"),
                    t("ctx_kdrama"),
                    t("ctx_cantodrama"),
                    t("ctx_cdrama"),
                    t("ctx_eng_tv"),
                    t("ctx_inet"),
                    t("ctx_pop"),
                ],
                index=0,
                key="media_ctx_type",
            )

        run_button = st.button(t("run"), use_container_width=True)

    elif page == "Coach":
        col1, col2 = st.columns(2)

        with col1:
            source_choice = st.selectbox(
                t("language_of_text"),
                ["auto"] + STUDY_LANG_CODES,
                index=0,
                format_func=lambda code: (
                    t("auto_detect")
                    if code == "auto"
                    else get_lang_display().get(code, code)
                ),
                key="coach_source_lang",
            )

        with col2:
            run_button = st.button(t("run"), use_container_width=True)

        with st.expander(
            TEXTS.get(st.session_state.ui_lang, {}).get(
                "screenshot_mode",
                "📷 Analyze chat screenshot",
            ),
            expanded=False,
        ):
            s_col1, s_col2 = st.columns(2)

            with s_col1:
                ss_lang = st.selectbox(
                    t("language_of_text"),
                    ["auto"] + STUDY_LANG_CODES,
                    index=0,
                    format_func=lambda code: (
                        t("auto_detect")
                        if code == "auto"
                        else get_lang_display().get(code, code)
                    ),
                    key="screenshot_lang",
                )

            with s_col2:
                analyze_btn = st.button(
                    TEXTS.get(st.session_state.ui_lang, {}).get(
                        "analyze_screenshot_btn",
                        "Analyze screenshot",
                    ),
                    use_container_width=True,
                    key="btn_analyze_screenshot",
                )

            image_file = st.file_uploader(
                TEXTS.get(st.session_state.ui_lang, {}).get(
                    "upload_screenshot",
                    "Upload a chat screenshot",
                ),
                type=["png", "jpg", "jpeg", "webp"],
                key="screenshot_uploader",
            )

            if analyze_btn:
                if not image_file:
                    st.warning(
                        TEXTS.get(st.session_state.ui_lang, {}).get(
                            "please_upload_image_first",
                            "Please upload an image first.",
                        )
                    )
                else:
                    image_data = image_file.read()
                    persona_profile = get_persona_profile(ss_lang, native_lang)
                    persona_profile["region_mode"] = region_code
                    persona_profile["region_guidelines"] = build_region_guidelines(
                        region_code,
                        target_lang,
                    )

                    if HAVE_SCREENSHOT_ANALYZE and callable(analyze_screenshot_chat):
                        run_ai_task(
                            task_fn=analyze_screenshot_chat,
                            task_kwargs=dict(
                                image_bytes=image_data,
                                image_name=image_file.name,
                                assumed_lang=None if ss_lang == "auto" else ss_lang,
                                native_lang=native_lang,
                                target_lang=target_lang,
                                region_mode=region_code,
                                temperature=temperature,
                                model=model,
                                persona_profile=persona_profile,
                            ),
                            history_kwargs=dict(
                                username=username,
                                mode="screenshot",
                                source_lang=ss_lang,
                                target_lang=native_lang,
                                native_lang=native_lang,
                                persona_code=persona_code,
                                ui_lang=st.session_state.ui_lang,
                                user_input=f"[screenshot] {image_file.name}",
                            ),
                            pron_lang=None,
                        )
                    else:
                        st.warning(
                            TEXTS.get(st.session_state.ui_lang, {}).get(
                                "screenshot_not_available",
                                "Screenshot analysis is not available. Please update ai_helper.",
                            )
                        )

    else:
        col1, col2 = st.columns(2)

        with col1:
            source_choice = st.selectbox(
                t("language_of_text"),
                ["auto"] + STUDY_LANG_CODES,
                index=0,
                format_func=lambda code: (
                    t("auto_detect")
                    if code == "auto"
                    else get_lang_display().get(code, code)
                ),
                key=f"{mode_map[page]}_source_lang",
            )

        with col2:
            run_button = st.button(t("run"), use_container_width=True)

    if run_button:
        if not text.strip():
            st.warning(t("enter_text_warn"))

        else:
            if page == "Coach":
                persona_profile = get_persona_profile(source_choice, target_lang)
                persona_profile["region_mode"] = region_code
                persona_profile["region_guidelines"] = build_region_guidelines(
                    region_code,
                    target_lang,
                )

                style_with_region = f"{reply_style} | region_mode={region_code}"

                result_pair = run_ai_task(
                    task_fn=chat_reply_coach_advanced,
                    task_kwargs=dict(
                        text=text,
                        source_lang=source_choice,
                        target_lang=target_lang,
                        native_lang=native_lang,
                        reply_style=style_with_region,
                        temperature=temperature,
                        model=model,
                        persona_profile=persona_profile,
                    ),
                    history_kwargs=dict(
                        username=username,
                        mode="coach",
                        source_lang=source_choice,
                        target_lang=target_lang,
                        native_lang=native_lang,
                        persona_code=persona_code,
                        ui_lang=st.session_state.ui_lang,
                        user_input=text,
                    ),
                    pron_lang=target_lang,
                )

                try:
                    detected_code = (
                        detect_language_code(text, model, temperature, persona_profile)
                        or source_choice
                    )

                    if detected_code in ("zh", "yue", "ko", "en"):
                        eval_data = evaluate_naturalness(
                            sentence=text,
                            eval_lang=detected_code,
                            native_lang=native_lang,
                            model=model,
                            temperature=temperature,
                            persona_profile=persona_profile,
                        )

                        render_naturalness_panel(
                            TEXTS.get(st.session_state.ui_lang, {}).get(
                                "naturalness_score_title",
                                "Naturalness Score",
                            ),
                            eval_data,
                        )

                except Exception:
                    pass


            elif page == "Mean":

                persona_profile = get_persona_profile(source_choice, native_lang)

                run_ai_task(

                    task_fn=explain_message_meaning,

                    task_kwargs=dict(

                        text=text,

                        source_lang=source_choice,

                        native_lang=native_lang,

                        temperature=temperature,

                        model=model,

                        persona_profile=persona_profile,

                    ),

                    history_kwargs=dict(

                        username=username,

                        mode="mean",

                        source_lang=source_choice,

                        target_lang=native_lang,

                        native_lang=native_lang,

                        persona_code=persona_code,

                        ui_lang=st.session_state.ui_lang,

                        user_input=text,

                    ),

                    pron_lang=native_lang,

                )



            else:
                persona_profile = get_persona_profile(source_choice, native_lang)

                run_ai_task(
                    task_fn=media_context_explain,
                    task_kwargs=dict(
                        text=text,
                        source_lang=source_choice,
                        native_lang=native_lang,
                        context_type=ctx_type,
                        temperature=temperature,
                        model=model,
                        persona_profile=persona_profile,
                    ),
                    history_kwargs=dict(
                        username=username,
                        mode="kpop",
                        source_lang=source_choice,
                        target_lang=native_lang,
                        native_lang=native_lang,
                        persona_code=persona_code,
                        ui_lang=st.session_state.ui_lang,
                        user_input=text,
                    ),
                    pron_lang=native_lang,
                )


elif page == "Grammar":
    go_home_button()
    section_header(t("feature_grammar"), t("feature_grammar_sub"))

    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_correct"), height=150, key="grammar_text")
    st.markdown("</div>", unsafe_allow_html=True)

    voice_input_ui("grammar_text")

    col1, col2 = st.columns(2)

    with col1:
        levels, level_map = local_levels()
        level_label = st.selectbox(t("learner_level"), levels, index=1)
        level_code = level_map[level_label]

    with col2:
        run_button = st.button(t("correct_btn"), use_container_width=True)

    if run_button:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            persona_profile = get_persona_profile(target_lang, target_lang)

            run_ai_task(
                task_fn=correct_grammar,
                task_kwargs=dict(
                    text=text,
                    target_lang=target_lang,
                    native_lang=native_lang,
                    level=level_code,
                    temperature=temperature,
                    model=model,
                    persona_profile=persona_profile,
                ),
                history_kwargs=dict(
                    username=username,
                    mode="grammar",
                    source_lang=target_lang,
                    target_lang=target_lang,
                    native_lang=native_lang,
                    persona_code=persona_code,
                    ui_lang=st.session_state.ui_lang,
                    user_input=text,
                ),
                pron_lang=target_lang,
            )


elif page == "Natural":
    go_home_button()
    section_header(t("feature_natural"), t("feature_natural_sub"))

    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_natural"), height=150, key="natural_text")
    st.markdown("</div>", unsafe_allow_html=True)

    voice_input_ui("natural_text")

    col1, col2 = st.columns(2)

    with col1:
        tones, tone_map = local_tones()
        tone_label = st.selectbox(t("desired_tone"), tones, index=0)
        tone_code = tone_map[tone_label]

    with col2:
        run_button = st.button(t("suggest_btn"), use_container_width=True)

    if run_button:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            persona_profile = get_persona_profile(target_lang, target_lang)

            run_ai_task(
                task_fn=suggest_natural_expression,
                task_kwargs=dict(
                    text=text,
                    target_lang=target_lang,
                    native_lang=native_lang,
                    tone_preference=tone_code,
                    temperature=temperature,
                    model=model,
                    persona_profile=persona_profile,
                ),
                history_kwargs=dict(
                    username=username,
                    mode="natural",
                    source_lang=target_lang,
                    target_lang=target_lang,
                    native_lang=native_lang,
                    persona_code=persona_code,
                    ui_lang=st.session_state.ui_lang,
                    user_input=text,
                ),
                pron_lang=target_lang,
            )

            try:
                eval_data = evaluate_naturalness(
                    sentence=text,
                    eval_lang=target_lang,
                    native_lang=native_lang,
                    model=model,
                    temperature=temperature,
                    persona_profile=persona_profile,
                )

                render_naturalness_panel(
                    TEXTS.get(st.session_state.ui_lang, {}).get(
                        "naturalness_score_title",
                        "Naturalness Score",
                    ),
                    eval_data,
                )
            except Exception:
                pass


elif page == "Vocabulary":
    go_home_button()
    section_header(t("feature_vocab"), t("feature_vocab_sub"))

    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_vocab"), height=150, key="vocab_text")
    st.markdown("</div>", unsafe_allow_html=True)

    voice_input_ui("vocab_text")

    col1, col2 = st.columns(2)

    with col1:
        max_items = st.slider(t("max_items"), 3, 12, 6, 1)

    with col2:
        run_button = st.button(t("explain_vocab_btn"), use_container_width=True)

    if run_button:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            persona_profile = get_persona_profile("auto", target_lang)

            run_ai_task(
                task_fn=explain_vocabulary,
                task_kwargs=dict(
                    text=text,
                    target_lang=target_lang,
                    native_lang=native_lang,
                    max_items=max_items,
                    temperature=temperature,
                    model=model,
                    persona_profile=persona_profile,
                ),
                history_kwargs=dict(
                    username=username,
                    mode="vocabulary",
                    source_lang="auto",
                    target_lang=target_lang,
                    native_lang=native_lang,
                    persona_code=persona_code,
                    ui_lang=st.session_state.ui_lang,
                    user_input=text,
                ),
                pron_lang=target_lang,
            )


elif page == "Tone":
    go_home_button()
    section_header(t("feature_tone"), t("feature_tone_sub"))

    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_tone"), height=150, key="tone_text")
    st.markdown("</div>", unsafe_allow_html=True)

    voice_input_ui("tone_text")

    col1, col2 = st.columns(2)

    with col1:
        tone_lang = st.selectbox(
            t("language_of_text"),
            STUDY_LANG_CODES,
            index=STUDY_LANG_CODES.index(target_lang),
            format_func=lambda code: get_lang_display().get(code, code),
        )

    with col2:
        run_button = st.button(t("analyze_tone_btn"), use_container_width=True)

    if run_button:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            persona_profile = get_persona_profile(tone_lang, tone_lang)

            run_ai_task(
                task_fn=analyze_tone,
                task_kwargs=dict(
                    text=text,
                    lang=tone_lang,
                    native_lang=native_lang,
                    temperature=temperature,
                    model=model,
                    persona_profile=persona_profile,
                ),
                history_kwargs=dict(
                    username=username,
                    mode="tone",
                    source_lang=tone_lang,
                    target_lang=tone_lang,
                    native_lang=native_lang,
                    persona_code=persona_code,
                    ui_lang=st.session_state.ui_lang,
                    user_input=text,
                ),
                pron_lang=tone_lang,
            )


elif page == "History":
    go_home_button()
    section_header(t("history_title"), t("history_sub"))

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        filter_mode = st.selectbox(
            t("filter_mode"),
            [
                "All",
                "say",
                "mean",
                "coach",
                "kpop",
                "translate",
                "grammar",
                "natural",
                "vocabulary",
                "tone",
                "screenshot",
            ],
            index=0,
        )

    with col2:
        filter_source = st.selectbox(
            t("filter_source"),
            ["All", "auto"] + STUDY_LANG_CODES,
            index=0,
        )

    with col3:
        filter_target = st.selectbox(
            t("filter_target"),
            ["All"] + STUDY_LANG_CODES,
            index=0,
        )

    with col4:
        filter_persona = st.selectbox(
            t("filter_persona"),
            ["All"] + PERSONA_CODES,
            index=0,
            format_func=lambda code: (
                code if code == "All" else persona_display(code)
            ),
        )

    search_text = st.text_input(t("search_in"))
    limit = st.slider(t("show_last"), 10, 200, 50, 10)

    try:
        rows = fetch_history(
            username=username,
            limit=limit,
            mode=None if filter_mode == "All" else filter_mode,
            source_lang=None if filter_source == "All" else filter_source,
            target_lang=None if filter_target == "All" else filter_target,
            persona=None if filter_persona == "All" else filter_persona,
            search=search_text.strip() or None,
        )
    except Exception as e:
        st.warning(f"{t('history_load_failed')}: {e}")
        rows = []

    if not rows:
        st.info(t("no_history"))
    else:
        display = get_lang_display()

        for row in rows:
            timestamp = row.get("timestamp")

            try:
                if isinstance(timestamp, (int, float)):
                    timestamp_value = (
                        timestamp / 1000
                        if timestamp and timestamp > 1e12
                        else timestamp
                    )
                    timestamp_text = time.strftime(
                        "%Y-%m-%d %H:%M:%S",
                        time.localtime(timestamp_value),
                    )
                else:
                    timestamp_text = str(timestamp)
            except Exception:
                timestamp_text = str(timestamp)

            mode_value = row.get("mode", "")
            source_value = row.get("source_lang", "")
            target_value = row.get("target_lang", "")
            persona_value = row.get("persona") or ""

            source_label = display.get(source_value, source_value)
            target_label = display.get(target_value, target_value)
            persona_label = (
                persona_display(persona_value)
                if persona_value
                else ""
            )

            title = (
                f"{timestamp_text} • {mode_value} • "
                f"{source_label} → {target_label} • {persona_label}"
            )

            st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
            st.markdown(f"**{title}**")

            with st.expander(t("input_label")):
                st.write(row.get("user_input", ""))

            with st.expander(t("output_label")):
                output_text = row.get("ai_output") or ""

                try:
                    st.json(json.loads(output_text))
                except Exception:
                    st.markdown(output_text)

            st.caption(
                f'{t("model_info_prefix")}: {row.get("model", "-")} • '
                f'{t("tokens_label")}: '
                f'{row.get("tokens_input", "-")}/'
                f'{row.get("tokens_output", "-")} • '
                f'{t("latency_label")}: '
                f'{row.get("latency_ms", "-")} ms'
            )

            st.markdown("</div>", unsafe_allow_html=True)


elif page == "About":
    go_home_button()
    section_header(t("about_title"))
    st.write(t("about_desc"))


st.caption("© 2026 TriLingua Bridge")
