import json
import time
from typing import Dict, Any, Callable, Optional

import streamlit as st
from dotenv import load_dotenv

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
)

from db_helper import init_db, insert_history, fetch_history

from ai_helper import (
    translate_text,
    correct_grammar,
    suggest_natural_expression,
    explain_vocabulary,
    analyze_tone,
    chat_reply_assistant,
)

from audio_helper import (
    to_pronunciation,
    synthesize_tts,
    transcribe_audio,
)


load_dotenv()

st.set_page_config(
    page_title="TriLingua Bridge",
    layout="centered",
)

inject_css()


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
        "show_pron": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


try:
    init_db()
except Exception as e:
    st.warning(f"{t('db_init_failed')}: {e}")


def go_home_button():
    if st.button(f"🏠 {t('back_home')}", use_container_width=True):
        st.session_state.page = "Home"
        st.rerun()


def get_persona_profile(source_lang: str, target_lang: str) -> Dict[str, Any]:
    return build_persona_profile(
        code=st.session_state.persona_code,
        source_lang=source_lang,
        target_lang=target_lang,
        ui_lang=st.session_state.ui_lang,
    )


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
        return

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
        and output_lang_for_pron in ("zh", "ko", "en")
    ):
        st.markdown(f"**{t('pronunciation_label')}**")
        st.write(to_pronunciation(result, output_lang_for_pron))

        with st.spinner(t("playing_audio")):
            audio_bytes = synthesize_tts(result, output_lang_for_pron)

        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3")
        else:
            st.warning(t("tts_not_supported"))

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
                st.warning(t("upload_audio"))
                return

            with st.spinner(t("transcribing")):
                audio_data = uploaded_file.read()
                transcript = transcribe_audio(
                    audio_data,
                    uploaded_file.name,
                    None if lang_option == "auto" else lang_option,
                )

            if transcript:
                st.session_state[text_area_key] = transcript
                st.success(t("ok"))
                st.rerun()
            else:
                st.warning(t("stt_unavailable"))


ui_label = TEXTS[st.session_state.ui_lang]["ui_language"]
ui_options = [UI_LANG_DISPLAY[code] for code in UI_LANGS]
current_ui_index = UI_LANGS.index(st.session_state.ui_lang)

selected_ui_label = st.sidebar.selectbox(
    ui_label,
    ui_options,
    index=current_ui_index,
    key="ui_lang_select",
)

selected_ui_code = UI_LANGS[ui_options.index(selected_ui_label)]

if selected_ui_code != st.session_state.ui_lang:
    st.session_state.ui_lang = selected_ui_code
    st.rerun()


st.sidebar.markdown(
    f'<div class="sb-title">{t("account_title")}</div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    f'<div class="sb-sub">{t("account_note")}</div>',
    unsafe_allow_html=True,
)

col_user, col_login = st.sidebar.columns([3, 1])

with col_user:
    username_input = st.text_input(
        t("username"),
        value=st.session_state.username,
        key="username_input",
    )

with col_login:
    if st.button(t("login"), use_container_width=True):
        st.session_state.username = username_input.strip()
        st.rerun()


if not st.session_state.username:
    hero(t("app_title"), t("subtitle"), t("not_social"))
    st.caption(t("account_note"))
    st.stop()


st.sidebar.success(f"{t('username')}: {st.session_state.username}")

if st.sidebar.button(t("logout"), use_container_width=True):
    st.session_state.username = ""
    st.rerun()


st.sidebar.markdown(
    f'<div class="sb-title">{t("prefs_title")}</div>',
    unsafe_allow_html=True,
)

lang_display = get_lang_display()

# =========================
# Native Language
# =========================

native_lang = st.sidebar.selectbox(
    t("my_native"),
    STUDY_LANG_CODES,
    index=STUDY_LANG_CODES.index(st.session_state.native_lang),
    format_func=lambda code: lang_display.get(code, code),
    key="native_lang_select",
)

st.session_state.native_lang = native_lang


# =========================
# Target Language
# =========================

target_lang = st.sidebar.selectbox(
    t("i_learn"),
    STUDY_LANG_CODES,
    index=STUDY_LANG_CODES.index(st.session_state.target_lang),
    format_func=lambda code: lang_display.get(code, code),
    key="target_lang_select",
)

st.session_state.target_lang = target_lang


# =========================
# Swap Button
# =========================

if st.sidebar.button(f"⇄ {t('swap')}", use_container_width=True):
    st.session_state.native_lang, st.session_state.target_lang = (
        st.session_state.target_lang,
        st.session_state.native_lang,
    )

    st.rerun()


# =========================
# Persona
# =========================

persona_code = st.sidebar.selectbox(
    t("persona"),
    PERSONA_CODES,
    index=PERSONA_CODES.index(st.session_state.persona_code),
    format_func=persona_display,
    key="persona_code_select",
)

st.session_state.persona_code = persona_code


# =========================
# Temperature
# =========================

temperature = st.sidebar.slider(
    t("creativity"),
    0.0,
    1.0,
    st.session_state.temperature,
    0.1,
    key="temperature_slider",
)

st.session_state.temperature = temperature


# =========================
# Model
# =========================

model = st.sidebar.text_input(
    t("model"),
    value=st.session_state.model_input,
    key="model_input_text",
)

st.session_state.model_input = model


# =========================
# Pronunciation Toggle
# =========================

show_pron = st.sidebar.checkbox(
    t("show_pron"),
    value=st.session_state.show_pron,
    key="show_pron_checkbox",
)

st.session_state.show_pron = show_pron


st.sidebar.info(t("tip"))

NAV_ITEMS = [
    ("Home", f"🏠 {t('nav_home')}"),
    ("Say", f"🗣️ {t('mode_say')}"),
    ("Mean", f"❓ {t('mode_mean')}"),
    ("Coach", f"🎯 {t('mode_coach')}"),
    ("Kpop", f"🎵 {t('mode_kpop')}"),
    ("Chat", f"💬 {t('feature_chat')}"),
    ("Translate", f"🌐 {t('feature_translate')}"),
    ("Grammar", f"✍️ {t('feature_grammar')}"),
    ("Natural", f"🎯 {t('feature_natural')}"),
    ("Vocabulary", f"📚 {t('feature_vocab')}"),
    ("Tone", f"🗣️ {t('feature_tone')}"),
    ("History", f"🕘 {t('nav_history')}"),
    ("About", f"ℹ️ {t('nav_about')}"),
]

nav_labels = [label for _, label in NAV_ITEMS]
page_from_label = {label: page_id for page_id, label in NAV_ITEMS}
label_from_page = {page_id: label for page_id, label in NAV_ITEMS}

selected_label = st.sidebar.radio(
    t("nav_title"),
    nav_labels,
    index=nav_labels.index(
        label_from_page.get(st.session_state.page, nav_labels[0])
    ),
)

selected_page = page_from_label[selected_label]

if selected_page != st.session_state.page:
    st.session_state.page = selected_page
    st.rerun()


page = st.session_state.page
username = st.session_state.username


if page == "Home":
    hero(t("app_title"), t("subtitle"), t("not_social"))

    section_header(t("what_can"), t("what_can_sub"))

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            f"🗣️ {t('mode_say')}\n\n{t('mode_say_sub')}",
            use_container_width=True,
        ):
            st.session_state.page = "Say"
            st.rerun()

    with col2:
        if st.button(
            f"❓ {t('mode_mean')}\n\n{t('mode_mean_sub')}",
            use_container_width=True,
        ):
            st.session_state.page = "Mean"
            st.rerun()

    col3, col4 = st.columns(2)

    with col3:
        if st.button(
            f"🎯 {t('mode_coach')}\n\n{t('mode_coach_sub')}",
            use_container_width=True,
        ):
            st.session_state.page = "Coach"
            st.rerun()

    with col4:
        if st.button(
            f"🎵 {t('mode_kpop')}\n\n{t('mode_kpop_sub')}",
            use_container_width=True,
        ):
            st.session_state.page = "Kpop"
            st.rerun()

    section_header(t("more_tools"), t("more_tools_sub"), accent="green")

    col5, col6 = st.columns(2)

    with col5:
        if st.button(f"🌐 {t('feature_translate')}", use_container_width=True):
            st.session_state.page = "Translate"
            st.rerun()

    with col6:
        if st.button(f"✍️ {t('feature_grammar')}", use_container_width=True):
            st.session_state.page = "Grammar"
            st.rerun()

    col7, col8 = st.columns(2)

    with col7:
        if st.button(f"🎯 {t('feature_natural')}", use_container_width=True):
            st.session_state.page = "Natural"
            st.rerun()

    with col8:
        if st.button(f"📚 {t('feature_vocab')}", use_container_width=True):
            st.session_state.page = "Vocabulary"
            st.rerun()

    if st.button(f"🗣️ {t('feature_tone')}", use_container_width=True):
        st.session_state.page = "Tone"
        st.rerun()


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

    col1, col2 = st.columns(2)

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
        run_button = st.button(button_label, use_container_width=True)

    if run_button:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            persona_profile = get_persona_profile(source_choice, target_lang)

            run_ai_task(
                task_fn=translate_text,
                task_kwargs=dict(
                    text=text,
                    source_lang=source_choice,
                    target_lang=target_lang,
                    native_lang=native_lang,
                    temperature=temperature,
                    model=model,
                    persona_profile=persona_profile,
                ),
                history_kwargs=dict(
                    username=username,
                    mode=mode_name,
                    source_lang=source_choice,
                    target_lang=target_lang,
                    native_lang=native_lang,
                    persona_code=persona_code,
                    ui_lang=st.session_state.ui_lang,
                    user_input=text,
                ),
                pron_lang=target_lang,
            )


elif page in ["Mean", "Coach", "Kpop"]:
    go_home_button()

    title_map = {
        "Mean": t("mode_mean"),
        "Coach": t("mode_coach"),
        "Kpop": t("mode_kpop"),
    }

    sub_map = {
        "Mean": t("mode_mean_sub"),
        "Coach": t("mode_coach_sub"),
        "Kpop": t("mode_kpop_sub"),
    }

    mode_map = {
        "Mean": "mean",
        "Coach": "coach",
        "Kpop": "kpop",
    }

    section_header(title_map[page], sub_map[page])

    text_key = f"{mode_map[page]}_text"

    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("input_text"), height=180, key=text_key)
    st.markdown("</div>", unsafe_allow_html=True)

    voice_input_ui(text_key)

    if page == "Kpop":
        source_choice = "ko"
        run_button = st.button(t("run"), use_container_width=True)
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

                run_ai_task(
                    task_fn=chat_reply_assistant,
                    task_kwargs=dict(
                        text=text,
                        source_lang=source_choice,
                        target_lang=target_lang,
                        native_lang=native_lang,
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

            else:
                output_lang = native_lang if page == "Mean" else target_lang
                persona_profile = get_persona_profile(source_choice, output_lang)

                run_ai_task(
                    task_fn=translate_text,
                    task_kwargs=dict(
                        text=text,
                        source_lang=source_choice,
                        target_lang=output_lang,
                        native_lang=native_lang,
                        temperature=temperature,
                        model=model,
                        persona_profile=persona_profile,
                    ),
                    history_kwargs=dict(
                        username=username,
                        mode=mode_map[page],
                        source_lang=source_choice,
                        target_lang=output_lang,
                        native_lang=native_lang,
                        persona_code=persona_code,
                        ui_lang=st.session_state.ui_lang,
                        user_input=text,
                    ),
                    pron_lang=output_lang,
                )


elif page == "Chat":
    go_home_button()

    section_header(t("feature_chat"), t("tip"))

    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("your_message"), height=160, key="chat_message")
    st.markdown("</div>", unsafe_allow_html=True)

    voice_input_ui("chat_message")

    col1, col2 = st.columns(2)

    with col1:
        source_choice = st.selectbox(
            t("msg_language"),
            ["auto"] + STUDY_LANG_CODES,
            index=0,
            format_func=lambda code: (
                t("auto_detect")
                if code == "auto"
                else get_lang_display().get(code, code)
            ),
            key="chat_source_lang",
        )

    with col2:
        run_button = st.button(t("generate_reply"), use_container_width=True)

    if run_button:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            persona_profile = get_persona_profile(source_choice, target_lang)

            run_ai_task(
                task_fn=chat_reply_assistant,
                task_kwargs=dict(
                    text=text,
                    source_lang=source_choice,
                    target_lang=target_lang,
                    native_lang=native_lang,
                    temperature=temperature,
                    model=model,
                    persona_profile=persona_profile,
                ),
                history_kwargs=dict(
                    username=username,
                    mode="chat",
                    source_lang=source_choice,
                    target_lang=target_lang,
                    native_lang=native_lang,
                    persona_code=persona_code,
                    ui_lang=st.session_state.ui_lang,
                    user_input=text,
                ),
                pron_lang=target_lang,
            )


elif page == "Grammar":
    go_home_button()

    section_header(t("feature_grammar"), t("tip"))

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

    section_header(t("feature_natural"), t("tip"))

    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(
        t("enter_text_natural"),
        height=150,
        key="natural_text",
    )
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


elif page == "Vocabulary":
    go_home_button()

    section_header(t("feature_vocab"), t("tip"))

    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(
        t("enter_text_vocab"),
        height=150,
        key="vocab_text",
    )
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

    section_header(t("feature_tone"), t("tip"))

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
                "chat",
                "translate",
                "grammar",
                "natural",
                "vocabulary",
                "tone",
            ],
            index=0,
        )

    with col2:
        filter_source = st.selectbox(
            t("filter_source"),
            ["All", "auto", "zh", "ko", "en"],
            index=0,
        )

    with col3:
        filter_target = st.selectbox(
            t("filter_target"),
            ["All", "zh", "ko", "en"],
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
