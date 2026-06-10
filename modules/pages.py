"""Page rendering functions for TriLingua Bridge — extracted from app.py."""

import hashlib
import html
import io
import csv
import json
import os
import time
from typing import Dict, Any, Callable, Optional

import streamlit as st

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
    section_header,
    hero,
    render_result,
    show_model_caption,
    normalize_usage,
    lang_label,
    feature_card,
)

from db_helper import (
    insert_history,
    fetch_history,
    create_user,
    authenticate_user,
    insert_learning_event,
    fetch_learning_summary,
    add_saved_item,
    fetch_saved_items,
    add_vocab_item,
    fetch_vocab_items,
)

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

from audio_helper import to_pronunciation, synthesize_tts, transcribe_audio

try:
    from streamlit_mic_recorder import mic_recorder
    MIC_SUPPORTED = True
except Exception:
    mic_recorder = None
    MIC_SUPPORTED = False


# ═══════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════

REGION_OPTIONS = [
    ("cn-mainland", "region_mainland_cn"),
    ("hk-cantonese", "region_hk_yue"),
    ("kr", "region_korean"),
    ("jp", "region_jp"),
    ("au-en", "region_au_en"),
    ("us-en", "region_us_en"),
]

# Max messages in Coach conversation memory (each turn = 2 messages: user + assistant)
MAX_CONVERSATION_MESSAGES = 12

# Max recent messages to include as AI context
MAX_CONTEXT_MESSAGES = 8


# ═══════════════════════════════════════════════════
# Shared utilities
# ═══════════════════════════════════════════════════

def ui_text(key: str, fallback: str) -> str:
    return TEXTS.get(st.session_state.ui_lang, {}).get(key, fallback)


def can_save_user(username: Optional[str] = None) -> bool:
    active_username = username if username is not None else st.session_state.get("username", "")
    return bool(active_username) and active_username != "guest" and st.session_state.get("auth_mode") == "password"


def queue_text_area_update(text_area_key: str, value: str):
    pending = st.session_state.setdefault("_pending_text_area_updates", {})
    pending[text_area_key] = value


def apply_pending_text_area_update(text_area_key: str):
    pending = st.session_state.get("_pending_text_area_updates", {})
    if text_area_key in pending:
        st.session_state[text_area_key] = pending.pop(text_area_key)


def ui_panel():
    try:
        return st.container(border=True)
    except TypeError:
        return st.container()


def result_to_text(result: Any) -> str:
    if result is None:
        return ""
    if isinstance(result, str):
        return result
    try:
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception:
        return str(result)


def stable_key_fragment(*parts: Any) -> str:
    raw = "|".join(str(part or "") for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def region_label(code: str) -> str:
    key_map = dict(REGION_OPTIONS)
    key = key_map.get(code, code)
    return TEXTS.get(st.session_state.ui_lang, {}).get(key, code)


def provider_health_label(provider: str) -> str:
    openai_ready = bool(os.environ.get("OPENAI_API_KEY"))
    deepseek_ready = bool(os.environ.get("DEEPSEEK_API_KEY"))
    anthropic_ready = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if provider == "openai":
        return ui_text("provider_ready", "Ready") if openai_ready else ui_text("provider_missing_key", "Missing API key")
    if provider == "deepseek":
        return ui_text("provider_ready", "Ready") if deepseek_ready else ui_text("provider_missing_key", "Missing API key")
    if provider == "anthropic":
        return ui_text("provider_ready", "Ready") if anthropic_ready else ui_text("provider_missing_key", "Missing API key")
    if openai_ready or deepseek_ready or anthropic_ready:
        return ui_text("provider_auto_ready", "Auto fallback ready")
    return ui_text("provider_missing_key", "Missing API key")


def provider_option_label(value: str) -> str:
    labels = {
        "auto": ui_text("provider_auto_option", "Auto: OpenAI first, DeepSeek fallback"),
        "openai": "OpenAI",
        "deepseek": "DeepSeek",
        "anthropic": "Anthropic Claude",
    }
    return labels.get(value, value)


def mode_display_label(value: str) -> str:
    labels = {
        "say": t("mode_say"),
        "mean": t("mode_mean"),
        "coach": TEXTS.get(st.session_state.ui_lang, {}).get("mode_coach_v2", t("mode_coach")),
        "kpop": t("mode_kpop"),
        "translate": t("feature_translate"),
        "grammar": t("feature_grammar"),
        "natural": t("feature_natural"),
        "vocabulary": t("feature_vocab"),
        "tone": t("feature_tone"),
        "screenshot": t("screenshot_mode"),
    }
    return labels.get((value or "").lower(), value or "-")


def mode_filter_label(value: str) -> str:
    labels = {"All": ui_text("all_filter", "All")}
    return labels.get(value, mode_display_label(value))


def filter_lang_label(value: str) -> str:
    if value == "All":
        return ui_text("all_filter", "All")
    if value == "auto":
        return t("auto_detect")
    return get_lang_display().get(value, value)


# ═══════════════════════════════════════════════════
# Initial state
# ═══════════════════════════════════════════════════

def init_state():
    defaults = {
        "ui_lang": "en",
        "page": "Home",
        "username": "",
        "auth_mode": "",
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


# ═══════════════════════════════════════════════════
# Navigation helpers
# ═══════════════════════════════════════════════════

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
        username_label = (
            ui_text("guest_user", "Guest")
            if st.session_state.username == "guest"
            else st.session_state.username
        )
        st.caption(
            f"{username_label} · {native_label} → {target_label} · "
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


def quick_action_button(label: str, page_name: str, key: str):
    if st.button(label, use_container_width=True, key=key):
        st.session_state.page = page_name
        st.rerun()


def workspace_nav_button(label: str, page_name: str, key: str):
    if st.button(label, key=key, use_container_width=True):
        st.session_state.page = page_name
        st.rerun()


# ═══════════════════════════════════════════════════
# Rendering helpers
# ═══════════════════════════════════════════════════

def product_note(title: str, body: str, icon: str = "💡"):
    safe_title = html.escape(str(title))
    safe_body = html.escape(str(body))
    safe_icon = html.escape(str(icon))
    st.markdown(
        f"""
        <div class="product-note">
            <div class="product-note-icon">{safe_icon}</div>
            <div>
                <div class="product-note-title">{safe_title}</div>
                <div class="product-note-body">{safe_body}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def phonetic_input_caption():
    st.caption(
        ui_text(
            "phonetic_input_tip",
            "Pinyin, Jyutping/Cantonese romanization, and Korean romanization are supported.",
        )
    )


def example_buttons(text_area_key: str, examples: Dict[str, str]):
    if not examples:
        return
    st.caption(ui_text("try_examples", "Try an example:"))
    cols = st.columns(min(len(examples), 3))
    for index, (label, sample) in enumerate(examples.items()):
        with cols[index % len(cols)]:
            st.button(
                label,
                key=f"example_{text_area_key}_{index}",
                use_container_width=True,
                on_click=queue_text_area_update,
                args=(text_area_key, sample),
            )


def task_examples(task: str) -> Dict[str, str]:
    examples = {
        "say": {
            "Casual chat": "I want to say: I am a little tired today, but I still want to meet you.",
            "Polite request": "Can you help me check this message before I send it?",
            "Friendly reply": "Sorry I replied late. I was busy with class today.",
        },
        "translate": {
            "CN → EN": "我今天有点累，但我还是想把这个项目继续做完。",
            "EN → ZH": "Could you please upload the original PNG files to the group chat?",
            "CN → KO": "谢谢你今天帮我，我真的很感激。",
        },
        "mean": {
            "Hidden meaning": "haha it's okay, maybe next time",
            "Tone check": "Do whatever you want.",
            "Korean chat": "괜찮아요 ㅎㅎ 다음에 봐요",
        },
        "coach": {
            "Ask naturally": "I want to ask a classmate to send the final diagram files to the WhatsApp group.",
            "Dating chat": "She said she is busy this weekend. I want to reply naturally, not too needy.",
            "Group work": "My teammate has not uploaded his part yet. I want to remind him politely.",
        },
        "kpop": {
            "Lyric meaning": "You make me feel like eleven",
            "Drama line": "라면 먹고 갈래?",
            "Internet slang": "어쩔티비",
        },
        "grammar": {
            "English": "I am very tired today so I cannot to go school.",
            "Korean": "저는 학교에 가요 어제.",
            "Chinese": "我昨天去学校了但是我很累的。",
        },
        "natural": {
            "Simple": "I am sorry for replying late because I was busy.",
            "Polite": "Please give me the file when you have time.",
            "Friendly": "I think your project is very good and I want to know more.",
        },
        "vocabulary": {
            "K-pop": "comeback, bias, stan, visual, main vocalist",
            "Study": "assignment, rubric, submission, extension, feedback",
            "Daily chat": "awkward, casual, polite, straightforward",
        },
        "tone": {
            "Blunt?": "You should have done this earlier.",
            "Friendly?": "No worries, take your time!",
            "Too cold?": "Ok.",
        },
    }

    localized_labels = {
        "zh": {
            "Casual chat": "日常聊天",
            "Polite request": "礼貌请求",
            "Friendly reply": "友好回复",
            "CN → EN": "中译英",
            "EN → ZH": "英译中",
            "CN → KO": "中译韩",
            "Hidden meaning": "潜台词",
            "Tone check": "语气检查",
            "Korean chat": "韩文聊天",
            "Ask naturally": "自然提问",
            "Dating chat": "暧昧聊天",
            "Group work": "小组合作",
            "Lyric meaning": "歌词理解",
            "Drama line": "韩剧台词",
            "Internet slang": "网络流行语",
            "English": "英文",
            "Korean": "韩文",
            "Chinese": "中文",
            "Simple": "简单表达",
            "Polite": "礼貌表达",
            "Friendly": "友好表达",
            "Study": "学习",
            "Daily chat": "日常聊天",
            "Blunt?": "会不会太冲？",
            "Friendly?": "够友好吗？",
            "Too cold?": "会不会太冷淡？",
        },
        "ko": {
            "Casual chat": "일상 대화",
            "Polite request": "정중한 부탁",
            "Friendly reply": "친근한 답장",
            "CN → EN": "중국어 → 영어",
            "EN → ZH": "영어 → 중국어",
            "CN → KO": "중국어 → 한국어",
            "Hidden meaning": "숨은 뜻",
            "Tone check": "말투 확인",
            "Korean chat": "한국어 채팅",
            "Ask naturally": "자연스럽게 묻기",
            "Dating chat": "썸/데이트 대화",
            "Group work": "팀플",
            "Lyric meaning": "가사 뜻",
            "Drama line": "드라마 대사",
            "Internet slang": "인터넷 유행어",
            "English": "영어",
            "Korean": "한국어",
            "Chinese": "중국어",
            "Simple": "간단한 표현",
            "Polite": "정중한 표현",
            "Friendly": "친근한 표현",
            "Study": "공부",
            "Daily chat": "일상 대화",
            "Blunt?": "너무 직설적?",
            "Friendly?": "친근한가요?",
            "Too cold?": "너무 차가운가요?",
        },
        "yue": {
            "Casual chat": "日常傾偈",
            "Polite request": "禮貌請求",
            "Friendly reply": "友善回覆",
            "CN → EN": "中譯英",
            "EN → ZH": "英譯中",
            "CN → KO": "中譯韓",
            "Hidden meaning": "潛台詞",
            "Tone check": "語氣檢查",
            "Korean chat": "韓文聊天",
            "Ask naturally": "自然咁問",
            "Dating chat": "曖昧聊天",
            "Group work": "小組合作",
            "Lyric meaning": "歌詞意思",
            "Drama line": "韓劇對白",
            "Internet slang": "網絡潮語",
            "English": "英文",
            "Korean": "韓文",
            "Chinese": "中文",
            "Simple": "簡單講法",
            "Polite": "禮貌講法",
            "Friendly": "友善講法",
            "Study": "學習",
            "Daily chat": "日常傾偈",
            "Blunt?": "會唔會太直？",
            "Friendly?": "夠唔夠友善？",
            "Too cold?": "會唔會太冷淡？",
        },
    }

    task_items = examples.get(task, {})
    label_map = localized_labels.get(st.session_state.ui_lang, {})
    return {label_map.get(label, label): sample for label, sample in task_items.items()}


def render_workflow_panel():
    st.markdown('<div class="workflow-grid">', unsafe_allow_html=True)
    steps = [
        ("1", ui_text("workflow_1", "Paste a real message or situation")),
        ("2", ui_text("workflow_2", "Choose language, region, tone, and task")),
        ("3", ui_text("workflow_3", "Let AI generate options and explanations")),
        ("4", ui_text("workflow_4", "Save useful results in local history")),
    ]
    for number, label in steps:
        st.markdown(
            f"""
            <div class="workflow-step">
                <div class="workflow-number">{number}</div>
                <div class="workflow-label">{label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)


def render_product_status(username: str):
    display = get_lang_display()
    native_label = display.get(st.session_state.native_lang, st.session_state.native_lang)
    target_label = display.get(st.session_state.target_lang, st.session_state.target_lang)
    provider = st.session_state.ai_provider
    username_label = ui_text("guest_user", "Guest") if username == "guest" else username

    cards = [
        (ui_text("status_workspace", "Workspace"), username_label or ui_text("guest_user", "Guest")),
        (ui_text("status_learning_path", "Learning path"), f"{native_label} → {target_label}"),
        (ui_text("status_ai", "AI status"), f"{provider.upper()} · {provider_health_label(provider)}"),
    ]

    st.markdown('<div class="product-status-grid">', unsafe_allow_html=True)
    for label, value in cards:
        st.markdown(
            f"""
            <div class="product-status-card">
                <div class="product-status-label">{html.escape(str(label))}</div>
                <div class="product-status-value">{html.escape(str(value))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_feature_group(title: str, items):
    st.markdown(
        f'<div class="feature-group-title">{html.escape(str(title))}</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(len(items))
    for index, item in enumerate(items):
        label, sub, icon, page_name, key = item
        with cols[index]:
            if feature_card(label, sub, icon, key=key):
                st.session_state.page = page_name
                st.rerun()


def course_seed_for_target(lang_code: str) -> Dict[str, str]:
    seeds = {
        "ko": {
            "grammar": "저는 학교에 가요 어제.",
            "natural": "I want to say in Korean: Sorry I replied late. I was busy with class.",
            "vocabulary": "assignment, deadline, group project, sorry for replying late",
            "coach": "I want to ask a Korean classmate to send the final files politely.",
        },
        "zh": {
            "grammar": "我昨天去学校了但是我很累的。",
            "natural": "I want to say in Mandarin: Could you send the file when you have time?",
            "vocabulary": "作业、截止日期、小组项目、麻烦你了",
            "coach": "我想礼貌地提醒同学把文件发到群里。",
        },
        "yue": {
            "grammar": "我尋日去學校咗但係我好攰嘅。",
            "natural": "I want to say in Cantonese: Can you send the file when you have time?",
            "vocabulary": "功課、deadline、小組 project、唔該晒",
            "coach": "我想用粵語禮貌咁提醒同學交文件。",
        },
        "ja": {
            "grammar": "昨日学校に行くましたがとても疲れました。",
            "natural": "I want to say in Japanese: Sorry I replied late. I was busy with class.",
            "vocabulary": "宿題、締切、グループプロジェクト、お疲れ様",
            "coach": "I want to politely remind a Japanese classmate to send the files to the group.",
        },
        "en": {
            "grammar": "I am very tired today so I cannot to go school.",
            "natural": "I am sorry for replying late because I was busy.",
            "vocabulary": "awkward, casual, polite, straightforward, deadline",
            "coach": "I want to remind my teammate to upload their part without sounding rude.",
        },
    }
    return seeds.get(lang_code, seeds["en"])


def render_course_card(kicker: str, title: str, body: str):
    st.markdown(
        f"""
        <div class="course-card">
            <div class="course-kicker">{html.escape(str(kicker))}</div>
            <div class="course-title">{html.escape(str(title))}</div>
            <div class="course-body">{html.escape(str(body))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def lesson_button(label: str, target_page: str, text_key: str, sample: str, key: str):
    if st.button(label, key=key, use_container_width=True):
        queue_text_area_update(text_key, sample)
        st.session_state.page = target_page
        st.rerun()


# ═══════════════════════════════════════════════════
# run_ai_task — core AI execution pipeline
# ═══════════════════════════════════════════════════

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
    render_result_actions(result, history_kwargs["mode"], history_kwargs)

    if usage.get("detected_lang"):
        display = get_lang_display()
        detected_lang = usage["detected_lang"]
        st.caption(f"{t('detected_source')}: {display.get(detected_lang, detected_lang)}")

    output_lang_for_pron = (
        pron_lang
        or history_kwargs.get("target_lang")
        or history_kwargs.get("source_lang")
    )

    if (
        st.session_state.get("show_pron")
        and isinstance(result, str)
        and output_lang_for_pron in ("zh", "yue", "ko", "ja", "en")
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
            st.caption(ui_text("tts_too_long", "Text too long for TTS. Use shorter text."))

    show_model_caption(usage, latency_ms)
    st.markdown("</div>", unsafe_allow_html=True)

    if not can_save_user(history_kwargs.get("username")):
        return result, usage

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
            ai_output=result if isinstance(result, str) else json.dumps(result, ensure_ascii=False),
            tokens_input=normalized_usage.get("prompt_tokens"),
            tokens_output=normalized_usage.get("completion_tokens"),
            model=normalized_usage.get("model"),
            latency_ms=latency_ms,
        )
        insert_learning_event(
            username=history_kwargs["username"],
            event_type="ai_task",
            mode=history_kwargs["mode"],
            target_lang=history_kwargs.get("target_lang"),
            points=2,
        )
    except Exception as e:
        st.warning(f"{t('history_save_failed')}: {e}")

    return result, usage


# ═══════════════════════════════════════════════════
# Voice input UI
# ═══════════════════════════════════════════════════

def voice_input_ui(text_area_key: str):
    with st.expander(f"🎙️ {t('voice_input')}", expanded=True):
        lang_option = st.selectbox(
            t("language_of_text"),
            ["auto"] + STUDY_LANG_CODES,
            index=0,
            format_func=lambda code: (
                t("auto_detect") if code == "auto" else get_lang_display().get(code, code)
            ),
            key=f"voice_lang_{text_area_key}",
        )

        st.caption(
            TEXTS.get(st.session_state.ui_lang, {}).get(
                "direct_mic_note",
                "Record directly here. The transcript will be placed into the text box above.",
            )
        )

        if MIC_SUPPORTED:
            mic_data = mic_recorder(
                start_prompt=TEXTS.get(st.session_state.ui_lang, {}).get("start_recording", "Start recording"),
                stop_prompt=TEXTS.get(st.session_state.ui_lang, {}).get("stop_recording", "Stop"),
                just_once=True,
                format="wav",
                key=f"mic_{text_area_key}",
            )
            if mic_data and isinstance(mic_data, dict) and mic_data.get("bytes"):
                st.audio(mic_data["bytes"], format="audio/wav")
                with st.spinner(t("transcribing")):
                    transcript = transcribe_audio(mic_data["bytes"], "mic.wav", lang_for_stt(lang_option))
                if transcript:
                    queue_text_area_update(text_area_key, transcript)
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

        with st.expander(
            TEXTS.get(st.session_state.ui_lang, {}).get("upload_audio_fallback", "Upload audio instead"),
            expanded=False,
        ):
            uploaded_file = st.file_uploader(
                t("upload_audio"),
                type=["wav", "mp3", "m4a", "webm"],
                key=f"upload_{text_area_key}",
            )
            if st.button(t("transcribe"), key=f"transcribe_{text_area_key}"):
                if not uploaded_file:
                    st.warning(
                        TEXTS.get(st.session_state.ui_lang, {}).get(
                            "please_upload_audio_first", "Please upload an audio file first.",
                        )
                    )
                else:
                    with st.spinner(t("transcribing")):
                        audio_data = uploaded_file.read()
                        transcript = transcribe_audio(audio_data, uploaded_file.name, lang_for_stt(lang_option))
                    if transcript:
                        queue_text_area_update(text_area_key, transcript)
                        st.success(t("ok"))
                        st.rerun()
                    else:
                        st.warning(t("stt_unavailable"))


# ═══════════════════════════════════════════════════
# Result actions (download / copy / save / vocab)
# ═══════════════════════════════════════════════════

def render_result_actions(result: Any, mode: str, history_kwargs: Optional[Dict[str, Any]] = None):
    text = result_to_text(result).strip()
    if not text:
        return

    st.divider()
    st.caption(ui_text("result_actions", "Next actions"))
    history_kwargs = history_kwargs or {}
    action_key = stable_key_fragment(mode, history_kwargs.get("user_input"), text)

    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        st.download_button(
            ui_text("download_result", "Download result"),
            data=text.encode("utf-8-sig"),
            file_name=f"trilingua_{mode}_{int(time.time())}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with col2:
        with st.expander(ui_text("copy_ready", "Copy-ready text"), expanded=False):
            st.code(text, language="text")

    if not can_save_user(history_kwargs.get("username")):
        return

    with col3:
        if st.button(ui_text("save_review", "Save to review"), key=f"save_review_{mode}_{action_key}", use_container_width=True):
            try:
                add_saved_item(
                    username=history_kwargs.get("username") or st.session_state.get("username") or "guest",
                    item_type="review",
                    mode=mode,
                    source_lang=history_kwargs.get("source_lang"),
                    target_lang=history_kwargs.get("target_lang"),
                    prompt=history_kwargs.get("user_input", ""),
                    content=text,
                )
                insert_learning_event(
                    username=history_kwargs.get("username") or st.session_state.get("username") or "guest",
                    event_type="save_review",
                    mode=mode,
                    target_lang=history_kwargs.get("target_lang"),
                    points=1,
                )
                st.success(ui_text("saved_review", "Saved to review."))
            except Exception as e:
                st.warning(f"{ui_text('save_failed', 'Save failed')}: {e}")

    with col4:
        if st.button(ui_text("add_vocab", "Add to vocab"), key=f"add_vocab_{mode}_{action_key}", use_container_width=True):
            try:
                prompt = (history_kwargs.get("user_input") or "").strip()
                term = prompt[:120] if prompt else text[:120]
                add_vocab_item(
                    username=history_kwargs.get("username") or st.session_state.get("username") or "guest",
                    term=term,
                    meaning=text,
                    source_lang=history_kwargs.get("source_lang"),
                    target_lang=history_kwargs.get("target_lang"),
                    example=prompt,
                )
                insert_learning_event(
                    username=history_kwargs.get("username") or st.session_state.get("username") or "guest",
                    event_type="add_vocab",
                    mode=mode,
                    target_lang=history_kwargs.get("target_lang"),
                    points=1,
                )
                st.success(ui_text("saved_vocab", "Added to vocab."))
            except Exception as e:
                st.warning(f"{ui_text('save_failed', 'Save failed')}: {e}")


# ═══════════════════════════════════════════════════
# History / summary helpers
# ═══════════════════════════════════════════════════

def format_row_time(timestamp: Any) -> str:
    try:
        timestamp_value = float(timestamp)
        if timestamp_value > 1e12:
            timestamp_value = timestamp_value / 1000
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp_value))
    except Exception:
        return str(timestamp or "")


def history_summary(username: str) -> Dict[str, Any]:
    if not can_save_user(username):
        return {
            "total": 0, "modes": 0, "latest": "-",
            "review": 0, "vocab": 0,
            "today_points": 0, "week_points": 0, "streak": 0, "top_mode": "-",
        }
    try:
        rows = fetch_history(username=username, limit=200)
    except Exception:
        rows = []
    try:
        review_rows = fetch_saved_items(username=username, limit=200)
    except Exception:
        review_rows = []
    try:
        vocab_rows = fetch_vocab_items(username=username, limit=200)
    except Exception:
        vocab_rows = []
    try:
        learning = fetch_learning_summary(username=username)
    except Exception:
        learning = {}

    modes = {row.get("mode") for row in rows if row.get("mode")}
    return {
        "total": len(rows),
        "modes": len(modes),
        "latest": rows[0].get("created_at_text") if rows else "-",
        "review": len(review_rows),
        "vocab": len(vocab_rows),
        "today_points": learning.get("today_points", 0),
        "week_points": learning.get("week_points", 0),
        "streak": learning.get("streak", 0),
        "top_mode": learning.get("top_mode", "-"),
    }


def render_recent_activity(username: str):
    if not can_save_user(username):
        return
    try:
        rows = fetch_history(username=username, limit=3)
    except Exception:
        rows = []
    if not rows:
        return
    with ui_panel():
        st.markdown(f"**{ui_text('recent_activity', 'Recent activity')}**")
        for row in rows:
            mode = mode_display_label(row.get("mode", "-"))
            created = row.get("created_at_text") or ""
            preview = (row.get("user_input") or "").replace("\n", " ")[:90]
            st.caption(f"{created} · {mode}")
            st.write(preview + ("..." if len(preview) >= 90 else ""))


def render_progress_strip(username: str):
    summary = history_summary(username)
    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        (ui_text("metric_today", "Today"), summary["today_points"]),
        (ui_text("metric_week", "This week"), summary["week_points"]),
        (ui_text("metric_streak", "Streak"), summary["streak"]),
        (ui_text("metric_review", "Review"), summary["review"]),
    ]
    for column, (label, value) in zip((c1, c2, c3, c4), metrics):
        with column:
            st.markdown(
                f"""
                <div class="asset-metric">
                    <div class="asset-metric-label">{html.escape(str(label))}</div>
                    <div class="asset-metric-value">{html.escape(str(value))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def rows_to_csv(rows):
    buffer = io.StringIO()
    fieldnames = [
        "created_at_text", "mode", "source_lang", "target_lang", "native_lang",
        "persona", "user_input", "ai_output", "model", "latency_ms",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in fieldnames})
    return buffer.getvalue().encode("utf-8-sig")


def build_region_guidelines(region_code: str, target_lang: str) -> str:
    guidelines = {
        "cn-mainland": (
            "Mainland Chinese mode: Use Mandarin-friendly wording, moderate politeness, "
            "limited emojis, indirect suggestions, concise 1–3 sentences."
        ),
        "hk-cantonese": (
            "Hong Kong Cantonese mode: Use Cantonese expressions with Traditional Chinese, "
            "casual but polite tone, light emojis ok, direct but friendly."
        ),
        "kr": (
            "Korean mode: Adapt honorifics properly, polite endings if not close, "
            "avoid excessive emojis, indirect yet clear."
        ),
        "jp": (
            "Japanese mode: Use appropriate keigo (polite language), "
            "consider formality levels, avoid overly direct wording, concise and courteous."
        ),
        "au-en": (
            "Australian English mode: Friendly, relaxed phrasing, light emoji ok, "
            "direct yet casual tone."
        ),
        "us-en": (
            "American English mode: Friendly, upbeat tone, clear and direct wording."
        ),
    }
    return guidelines.get(region_code, "Adjust wording, politeness, emoji use, directness, length, and tone appropriately.")


def render_workspace_home(username: str):
    section_header(
        TEXTS.get(st.session_state.ui_lang, {}).get("what_can_v2", t("what_can")),
        t("what_can_sub"),
    )

    rail, main, assets = st.columns([1.0, 2.15, 1.05], gap="large")

    with rail:
        st.markdown('<div class="workspace-rail">', unsafe_allow_html=True)
        st.markdown(
            f'<div class="workspace-rail-title">{html.escape(ui_text("workspace_nav", "Workspace"))}</div>',
            unsafe_allow_html=True,
        )
        workspace_nav_button(ui_text("feature_course", "Course Learning"), "Lessons", "nav_lessons")
        workspace_nav_button(ui_text("review_book", "Review Book"), "Review", "nav_review")
        workspace_nav_button(ui_text("vocab_bank", "Vocab Bank"), "Vocab Bank", "nav_vocab_bank")
        workspace_nav_button(ui_text("learning_report", "Learning Report"), "Report", "nav_report")
        workspace_nav_button(t("nav_history"), "History", "nav_history")
        st.markdown("</div>", unsafe_allow_html=True)

    with main:
        render_feature_group(
            ui_text("group_chat", "Chat & replies"),
            [
                (
                    TEXTS.get(st.session_state.ui_lang, {}).get("mode_coach_v2", t("mode_coach")),
                    TEXTS.get(st.session_state.ui_lang, {}).get("mode_coach_sub_v2", t("mode_coach_sub")),
                    "🎯", "Coach", "card_coach_v2",
                ),
                (t("mode_say"), t("mode_say_sub"), "🗣️", "Say", "card_say"),
                (t("feature_tone"), t("feature_tone_sub"), "🧭", "Tone", "card_tone"),
            ],
        )
        render_feature_group(
            ui_text("group_language_tools", "Language tools"),
            [
                (t("feature_translate"), t("tip"), "🌐", "Translate", "card_translate"),
                (t("feature_grammar"), t("feature_grammar_sub"), "✍️", "Grammar", "card_grammar"),
                (t("feature_natural"), t("feature_natural_sub"), "✨", "Natural", "card_natural"),
                (t("feature_vocab"), t("feature_vocab_sub"), "📚", "Vocabulary", "card_vocab"),
            ],
        )
        render_feature_group(
            ui_text("group_understand", "Understand content"),
            [
                (t("mode_mean"), t("mode_mean_sub"), "❓", "Mean", "card_mean"),
                (t("mode_kpop"), t("mode_kpop_sub"), "🎧", "Kpop", "card_kpop"),
            ],
        )

    with assets:
        if not can_save_user(username):
            st.markdown(f"**{ui_text('workspace_assets', 'Your assets')}**")
            product_note(
                ui_text("login_required_title", "Login required"),
                ui_text("guest_no_save_note", "Guest mode is for trying the app only. Log in with an account to save history, review cards, and vocab."),
                "🔒",
            )
            return
        summary = history_summary(username)
        st.markdown(f"**{ui_text('workspace_assets', 'Your assets')}**")
        st.markdown(
            f"""
            <div class="asset-metric">
                <div class="asset-metric-label">{html.escape(ui_text("asset_history", "Saved tasks"))}</div>
                <div class="asset-metric-value">{summary["total"]}</div>
            </div>
            <div class="asset-metric">
                <div class="asset-metric-label">{html.escape(ui_text("asset_modes", "Modes used"))}</div>
                <div class="asset-metric-value">{summary["modes"]}</div>
            </div>
            <div class="asset-metric">
                <div class="asset-metric-label">{html.escape(ui_text("asset_review", "Review cards"))}</div>
                <div class="asset-metric-value">{summary["review"]}</div>
            </div>
            <div class="asset-metric">
                <div class="asset-metric-label">{html.escape(ui_text("asset_vocab", "Vocab items"))}</div>
                <div class="asset-metric-value">{summary["vocab"]}</div>
            </div>
            <div class="asset-metric">
                <div class="asset-metric-label">{html.escape(ui_text("asset_today", "Today points"))}</div>
                <div class="asset-metric-value">{summary["today_points"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(
            f'{ui_text("asset_streak", "Streak")}: {summary["streak"]} · '
            f'{ui_text("asset_top_mode", "Top mode")}: {mode_display_label(summary["top_mode"])}'
        )
        st.caption(f'{ui_text("asset_latest", "Latest")}: {summary["latest"]}')
        render_recent_activity(username)


# ═══════════════════════════════════════════════════
# Lessons / Review / Vocab Bank / Report pages
# ═══════════════════════════════════════════════════

def render_lessons_page():
    go_home_button()
    section_header(
        ui_text("course_title", "Course Learning"),
        ui_text("course_sub", "A guided path that turns the tools into daily practice."),
    )

    target_lang = st.session_state.target_lang
    seeds = course_seed_for_target(target_lang)
    display = get_lang_display()
    target_label = display.get(target_lang, target_lang)

    product_note(
        ui_text("course_note_title", "How this course works"),
        ui_text("course_note_body", "Pick one short lesson, practice with a prepared prompt, then save useful outputs in your local history."),
        "🎓",
    )

    today_path = ui_text("course_today", "Today's path")
    st.markdown(f"**{today_path} · {target_label}**")
    c1, c2, c3 = st.columns(3)

    with c1:
        render_course_card(
            ui_text("course_step_1", "Step 1"),
            ui_text("course_lesson_grammar", "Fix one real sentence"),
            ui_text("course_lesson_grammar_body", "Learn the mistake, the corrected sentence, and one pattern you can reuse."),
        )
        lesson_button(ui_text("course_practice_grammar", "Practice grammar"), "Grammar", "grammar_text", seeds["grammar"], "course_practice_grammar")

    with c2:
        render_course_card(
            ui_text("course_step_2", "Step 2"),
            ui_text("course_lesson_natural", "Make it sound natural"),
            ui_text("course_lesson_natural_body", "Turn a translated-sounding sentence into a version you can actually send."),
        )
        lesson_button(ui_text("course_practice_natural", "Practice natural expression"), "Natural", "natural_text", seeds["natural"], "course_practice_natural")

    with c3:
        render_course_card(
            ui_text("course_step_3", "Step 3"),
            ui_text("course_lesson_reply", "Use it in a real chat"),
            ui_text("course_lesson_reply_body", "Practice a culturally appropriate reply for school, work, friends, or dating."),
        )
        lesson_button(ui_text("course_practice_reply", "Practice chat reply"), "Coach", "coach_text", seeds["coach"], "course_practice_reply")

    section_header(ui_text("course_drills", "Focused drills"), ui_text("course_drills_sub", "Short exercises you can repeat whenever you have five minutes."))
    d1, d2 = st.columns(2)

    with d1:
        render_course_card(
            ui_text("course_drill_vocab", "Vocabulary Builder"),
            ui_text("course_drill_vocab_title", "Build a phrase bank"),
            ui_text("course_drill_vocab_body", "Collect phrases from assignments, chats, lyrics, and daily situations."),
        )
        lesson_button(ui_text("course_practice_vocab", "Practice vocabulary"), "Vocabulary", "vocab_text", seeds["vocabulary"], "course_practice_vocab")

    with d2:
        render_course_card(
            ui_text("course_drill_tone", "Tone Check"),
            ui_text("course_drill_tone_title", "Check before you send"),
            ui_text("course_drill_tone_body", "Learn whether a message sounds cold, polite, direct, formal, or friendly."),
        )
        lesson_button(ui_text("course_practice_tone", "Practice tone"), "Tone", "tone_text", seeds["natural"], "course_practice_tone")


LOGIN_REQUIRED_NOTE = ("login_required_title", "Login required")
GUEST_NO_SAVE_NOTE = ("guest_no_save_note", "Guest mode is for trying the app only. Log in with an account to save history, review cards, and vocab.")


def _guard_guest(username: str) -> bool:
    """Show login-required note if guest; return True if should stop."""
    if not can_save_user(username):
        product_note(ui_text(*LOGIN_REQUIRED_NOTE), ui_text(*GUEST_NO_SAVE_NOTE), "🔒")
        return True
    return False


def render_review_page(username: str):
    go_home_button()
    section_header(
        ui_text("review_title", "Review Book"),
        ui_text("review_sub", "Saved corrections, replies, and explanations for spaced review."),
    )
    if _guard_guest(username):
        return

    render_progress_strip(username)

    search_text = st.text_input(ui_text("review_search", "Search review cards"))
    try:
        rows = fetch_saved_items(username=username, limit=80, search=search_text.strip() or None)
    except Exception as e:
        st.warning(f"{ui_text('history_load_failed', 'Failed to load history')}: {e}")
        rows = []

    if not rows:
        product_note(ui_text("empty_review_title", "No review cards yet"), ui_text("empty_review_body", "Run any AI task, then use Save to review under the result."), "✓")
        return

    for row in rows:
        title = f'{format_row_time(row.get("timestamp"))} · {mode_display_label(row.get("mode", ""))}'
        st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
        st.markdown(f"**{title}**")
        if row.get("prompt"):
            with st.expander(ui_text("input_label", "Input")):
                st.write(row.get("prompt"))
        with st.expander(ui_text("output_label", "Output"), expanded=True):
            st.markdown(row.get("content") or "")
        if st.button(ui_text("review_again", "Practice again"), key=f"review_again_{row.get('id')}", use_container_width=True):
            target_page = {
                "grammar": "Grammar",
                "natural": "Natural",
                "vocabulary": "Vocabulary",
                "tone": "Tone",
                "coach": "Coach",
                "translate": "Translate",
            }.get(row.get("mode"), "Coach")
            key_map = {
                "Grammar": "grammar_text",
                "Natural": "natural_text",
                "Vocabulary": "vocab_text",
                "Tone": "tone_text",
                "Coach": "coach_text",
                "Translate": "translate_text",
            }
            queue_text_area_update(key_map.get(target_page, "coach_text"), row.get("prompt") or row.get("content") or "")
            st.session_state.page = target_page
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def render_vocab_bank_page(username: str):
    go_home_button()
    section_header(
        ui_text("vocab_title", "Vocab Bank"),
        ui_text("vocab_sub", "A personal phrase bank built from your real tasks."),
    )
    if _guard_guest(username):
        return

    render_progress_strip(username)

    with ui_panel():
        term = st.text_input(ui_text("vocab_term", "Term or phrase"))
        meaning = st.text_area(ui_text("vocab_meaning", "Meaning / note"), height=120)
        example = st.text_area(ui_text("vocab_example", "Example sentence"), height=100)
        if st.button(ui_text("vocab_add_manual", "Add phrase"), use_container_width=True):
            if term.strip():
                add_vocab_item(
                    username=username, term=term, meaning=meaning,
                    source_lang=st.session_state.native_lang, target_lang=st.session_state.target_lang,
                    example=example,
                )
                insert_learning_event(username, "add_vocab", "vocabulary", st.session_state.target_lang, 1)
                st.success(ui_text("saved_vocab", "Added to vocab."))
                st.rerun()
            else:
                st.warning(ui_text("vocab_term_required", "Add a term first."))

    search_text = st.text_input(ui_text("vocab_search", "Search vocab"))
    try:
        rows = fetch_vocab_items(username=username, limit=120, search=search_text.strip() or None)
    except Exception as e:
        st.warning(f"{ui_text('history_load_failed', 'Failed to load history')}: {e}")
        rows = []

    if not rows:
        product_note(ui_text("empty_vocab_title", "No vocab yet"), ui_text("empty_vocab_body", "Add phrases manually or save outputs from Vocabulary explanations."), "＋")
        return

    for row in rows:
        with ui_panel():
            st.markdown(f"**{row.get('term', '')}**")
            st.caption(format_row_time(row.get("timestamp")))
            st.write(row.get("meaning") or "")
            if row.get("example"):
                st.caption(row.get("example"))


def render_learning_report_page(username: str):
    go_home_button()
    section_header(
        ui_text("report_title", "Learning Report"),
        ui_text("report_sub", "A quick picture of what you practiced and what to do next."),
    )
    if _guard_guest(username):
        return

    summary = history_summary(username)
    render_progress_strip(username)

    c1, c2 = st.columns(2)
    with c1:
        product_note(ui_text("report_focus_title", "Current focus"), f'{ui_text("asset_top_mode", "Top mode")}: {mode_display_label(summary["top_mode"])}', "◎")
    with c2:
        product_note(ui_text("report_next_title", "Recommended next step"), ui_text("report_next_body", "Review two saved cards, add one phrase to vocab, then finish one course drill."), "→")

    try:
        rows = fetch_history(username=username, limit=20)
    except Exception:
        rows = []

    st.markdown(f"**{ui_text('report_recent', 'Recent learning signals')}**")
    if not rows:
        st.info(ui_text("no_history", "No history yet."))
    else:
        mode_counts: Dict[str, int] = {}
        for row in rows:
            mode_label = mode_display_label(row.get("mode") or "-")
            mode_counts[mode_label] = mode_counts.get(mode_label, 0) + 1
        chart_rows = [{"mode": mode, "count": count} for mode, count in sorted(mode_counts.items())]
        st.bar_chart(chart_rows, x="mode", y="count")


# ═══════════════════════════════════════════════════
# Naturalness evaluator
# ═══════════════════════════════════════════════════

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

    data = {"verdict": "", "score": None, "reason": "", "suggestion": ""}
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            data.update({
                "verdict": parsed.get("verdict", ""),
                "score": parsed.get("score", None),
                "reason": parsed.get("reason", ""),
                "suggestion": parsed.get("suggestion", ""),
            })
    except Exception:
        data["verdict"] = "somewhat_natural"
        data["score"] = 6
        data["reason"] = str(content)[:200]
        data["suggestion"] = ""

    return data


def render_naturalness_panel(title: str, eval_data: Dict[str, Any]):
    verdict = eval_data.get("verdict") or "-"
    verdict_labels = {
        "natural": ui_text("verdict_natural", "Natural"),
        "somewhat_natural": ui_text("verdict_somewhat_natural", "Somewhat natural"),
        "machine_translated": ui_text("verdict_machine_translated", "Translated-sounding"),
    }
    verdict_text = verdict_labels.get(str(verdict), verdict)

    try:
        score = int(eval_data.get("score")) if eval_data.get("score") is not None else "-"
    except Exception:
        score = "-"

    reason = eval_data.get("reason") or "-"
    suggestion = eval_data.get("suggestion") or ""

    st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
    st.markdown(f"**{title}**")
    st.write(
        f"{TEXTS.get(st.session_state.ui_lang, {}).get('naturalness_verdict', 'Verdict')}: {verdict_text}"
    )
    st.write(
        f"{TEXTS.get(st.session_state.ui_lang, {}).get('naturalness_score', 'Score')}: {score}"
    )
    st.write(
        f"{TEXTS.get(st.session_state.ui_lang, {}).get('naturalness_reason', 'Why')}: {reason}"
    )
    if suggestion:
        st.write(
            TEXTS.get(st.session_state.ui_lang, {}).get("naturalness_suggestion", "More natural version")
        )
        st.markdown(suggestion)
    st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
# Home dashboard
# ═══════════════════════════════════════════════════

def is_demo_mode() -> bool:
    flag = os.environ.get("DEPLOY_MODE") or ""
    if not flag:
        try:
            flag = st.secrets.get("DEPLOY_MODE", "") or ""
        except Exception:
            flag = ""
    return flag.lower() == "demo"


def render_home_dashboard():
    ui_lang_key = st.session_state.ui_lang

    hero(
        t("app_title"),
        TEXTS.get(st.session_state.ui_lang, {}).get("subtitle_v2", t("subtitle")),
        t("not_social"),
    )

    if st.session_state.username:
        with ui_panel():
            account_col, logout_col = st.columns([4, 1])
            with account_col:
                st.markdown(f"**{ui_text('workspace_ready', 'Workspace ready')}**")
                auth_label = (
                    ui_text("auth_guest_mode", "Guest mode")
                    if st.session_state.get("auth_mode") == "guest"
                    else ui_text("auth_password_mode", "Password account")
                )
                st.caption(f"{t('account_note')} · {auth_label}")
            with logout_col:
                if st.button(t("logout"), use_container_width=True, key="home_logout_btn"):
                    st.session_state.username = ""
                    st.session_state.auth_mode = ""
                    st.rerun()

            render_product_status(st.session_state.username)
    else:
        with ui_panel():
            st.markdown(f"**{t('account_title')}**")
            st.caption(t("account_note"))

            login_tab, register_tab, guest_tab = st.tabs([
                ui_text("login_tab", "Login"),
                ui_text("register_tab", "Create account"),
                ui_text("guest_tab", "Guest"),
            ])

            with login_tab:
                login_username = st.text_input(t("username"), key="login_username_input")
                login_password = st.text_input(ui_text("password", "Password"), type="password", key="login_password_input")
                if st.button(t("login"), use_container_width=True, key="home_login_btn"):
                    auth = authenticate_user(login_username, login_password)
                    if auth.get("ok"):
                        st.session_state.username = auth["username"]
                        st.session_state.auth_mode = "password"
                        st.rerun()
                    else:
                        st.warning(ui_text("invalid_login", "Invalid username or password."))

            with register_tab:
                register_username = st.text_input(t("username"), key="register_username_input")
                register_password = st.text_input(ui_text("password", "Password"), type="password", key="register_password_input")
                register_confirm = st.text_input(ui_text("confirm_password", "Confirm password"), type="password", key="register_confirm_input")
                if st.button(ui_text("create_account", "Create account"), use_container_width=True, key="home_register_btn"):
                    if register_password != register_confirm:
                        st.warning(ui_text("password_mismatch", "Passwords do not match."))
                    else:
                        created = create_user(register_username, register_password)
                        if created.get("ok"):
                            st.session_state.username = created["username"]
                            st.session_state.auth_mode = "password"
                            st.success(ui_text("account_created", "Account created."))
                            st.rerun()
                        else:
                            st.warning(ui_text(created.get("error", "account_error"), "Could not create account."))

            with guest_tab:
                st.caption(ui_text("guest_note", "Try the app without creating an account. Guest history is shared locally."))
                if st.button(ui_text("continue_guest", "Guest"), use_container_width=True, key="home_guest_btn"):
                    st.session_state.username = "guest"
                    st.session_state.auth_mode = "guest"
                    st.rerun()

    prefs_container = (
        st.expander(t("prefs_title"), expanded=True)
        if st.session_state.username
        else ui_panel()
    )

    with prefs_container:
        if not st.session_state.username:
            st.markdown(f"**{t('prefs_title')}**")

        ui_options = [UI_LANG_DISPLAY[code] for code in UI_LANGS]
        current_ui_index = UI_LANGS.index(st.session_state.ui_lang)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            selected_ui_label = st.selectbox(t("ui_language"), ui_options, index=current_ui_index, key="home_ui_lang_select")
            selected_ui_code = UI_LANGS[ui_options.index(selected_ui_label)]
            if selected_ui_code != st.session_state.ui_lang:
                st.session_state.ui_lang = selected_ui_code
                st.rerun()
        with col2:
            st.session_state.native_lang = st.selectbox(
                t("my_native"), STUDY_LANG_CODES,
                index=STUDY_LANG_CODES.index(st.session_state.native_lang),
                format_func=lang_label, key=f"home_native_lang_select_{ui_lang_key}",
            )
        with col3:
            st.session_state.target_lang = st.selectbox(
                t("i_learn"), STUDY_LANG_CODES,
                index=STUDY_LANG_CODES.index(st.session_state.target_lang),
                format_func=lang_label, key=f"home_target_lang_select_{ui_lang_key}",
            )
        with col4:
            st.session_state.persona_code = st.selectbox(
                t("persona"), PERSONA_CODES,
                index=PERSONA_CODES.index(st.session_state.persona_code),
                format_func=persona_display, key=f"home_persona_code_select_{ui_lang_key}",
            )

        with st.expander(ui_text("advanced_settings", "Advanced settings"), expanded=False):
            col5, col6 = st.columns(2)
            with col5:
                st.session_state.temperature = st.slider(t("creativity"), 0.0, 1.0, st.session_state.temperature, 0.1, key="home_temperature_slider")
            with col6:
                st.session_state.show_pron = st.checkbox(t("show_pron"), value=st.session_state.show_pron, key="home_show_pron_checkbox")

            provider_options = ["auto", "openai", "deepseek", "anthropic"]
            st.session_state.ai_provider = st.selectbox(
                t("ai_provider"), provider_options,
                index=provider_options.index(st.session_state.ai_provider),
                format_func=provider_option_label, key="home_ai_provider_select",
            )
            os.environ["AI_PROVIDER"] = st.session_state.ai_provider
            st.session_state.model_input = st.text_input(t("model"), value=st.session_state.model_input, key="home_model_input_text")

        st.caption(t("tip"))

    if not st.session_state.username:
        product_note(
            ui_text("start_tip_title", "Start in 10 seconds"),
            ui_text("start_tip_body", "Enter a username for separate local history, or use Guest to try the app immediately."),
            "🚀",
        )
        return

    render_workspace_home(st.session_state.username)


# ═══════════════════════════════════════════════════
# Say / Translate page
# ═══════════════════════════════════════════════════

def render_say_translate_page(page: str):
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

    product_note(
        ui_text("page_tip_title", "How to use this page"),
        ui_text("say_translate_tip", "Paste a message, choose source and target language, then run. Use examples if you do not know where to start."),
        "🧭",
    )
    phonetic_input_caption()

    apply_pending_text_area_update(text_key)
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(text_label, height=180, key=text_key)
    st.markdown("</div>", unsafe_allow_html=True)

    example_buttons(text_key, task_examples(mode_name))
    voice_input_ui(text_key)

    col1, col2, col3 = st.columns(3)
    with col1:
        source_choice = st.selectbox(
            t("source_language"), ["auto"] + STUDY_LANG_CODES, index=0,
            format_func=lambda code: t("auto_detect") if code == "auto" else get_lang_display().get(code, code),
            key=f"{mode_name}_source_lang",
        )
    with col2:
        page_target_lang = st.selectbox(
            t("filter_target"), STUDY_LANG_CODES,
            index=STUDY_LANG_CODES.index(st.session_state.target_lang),
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
                    text=text, source_lang=source_choice, target_lang=page_target_lang,
                    native_lang=st.session_state.native_lang, temperature=st.session_state.temperature,
                    model=st.session_state.model_input, persona_profile=persona_profile,
                ),
                history_kwargs=dict(
                    username=st.session_state.username, mode=mode_name,
                    source_lang=source_choice, target_lang=page_target_lang,
                    native_lang=st.session_state.native_lang, persona_code=st.session_state.persona_code,
                    ui_lang=st.session_state.ui_lang, user_input=text,
                ),
                pron_lang=page_target_lang,
            )


# ═══════════════════════════════════════════════════
# Mean / Coach / Kpop page
# ═══════════════════════════════════════════════════

def render_mean_coach_kpop_page(page: str):
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
    mode_map = {"Mean": "mean", "Coach": "coach", "Kpop": "kpop"}

    section_header(title_map[page], sub_map[page])

    # ── Coach state management ───────────────────────────
    if page == "Coach":
        if st.session_state.pop("_pending_swap", False):
            _src = st.session_state.get("coach_source_lang", "auto")
            _tgt = st.session_state.get("coach_target_lang", "en")
            if _src != "auto":
                st.session_state.coach_source_lang = _tgt
                st.session_state.coach_target_lang = _src
                st.session_state.target_lang = _src
            st.rerun()

        if "coach_conversation" not in st.session_state:
            st.session_state.coach_conversation = []

        _src_lang = st.session_state.get("coach_source_lang", "auto")
        _tgt_lang = st.session_state.get("coach_target_lang", "en")
        _region = st.session_state.get("coach_region_mode", "cn-mainland")
        _ctx_key = f"{_src_lang}|{_tgt_lang}|{_region}"
        _prev_ctx = st.session_state.get("_coach_ctx_key", "")
        if _ctx_key != _prev_ctx and st.session_state.coach_conversation:
            st.session_state.coach_conversation = []
            st.info(t("conversation_reset"))
        st.session_state._coach_ctx_key = _ctx_key
    # ── end state management ──────────────────────────────

    text_key = f"{mode_map[page]}_text"
    region_code = st.session_state.get("coach_region_mode", "cn-mainland")

    if page == "Coach":
        # ── Language selector bar (before input) ──
        swap_col1, swap_col2, swap_col3 = st.columns([2, 1, 2])
        with swap_col1:
            source_choice = st.selectbox(
                t("language_of_text"), ["auto"] + STUDY_LANG_CODES, index=0,
                format_func=lambda code: t("auto_detect") if code == "auto" else get_lang_display().get(code, code),
                key="coach_source_lang",
            )
        with swap_col2:
            _swap_disabled = st.session_state.get("coach_source_lang") == "auto"
            if st.button("⇄", key="coach_swap_btn", use_container_width=True, disabled=_swap_disabled):
                st.session_state._pending_swap = True
                st.rerun()
            if _swap_disabled:
                st.caption(t("swap_unavailable_auto"))
        with swap_col3:
            if st.session_state.target_lang not in STUDY_LANG_CODES:
                st.session_state.target_lang = "en"
            if st.session_state.get("coach_target_lang") not in STUDY_LANG_CODES:
                st.session_state.coach_target_lang = st.session_state.target_lang
            target_choice = st.selectbox(
                t("filter_target"), STUDY_LANG_CODES,
                index=STUDY_LANG_CODES.index(st.session_state.target_lang),
                format_func=lambda code: get_lang_display().get(code, code),
                key="coach_target_lang",
            )
            if st.session_state.coach_target_lang != st.session_state.target_lang:
                st.session_state.target_lang = st.session_state.coach_target_lang
        run_button = st.button(t("run"), use_container_width=True)

    phonetic_input_caption()

    apply_pending_text_area_update(text_key)
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("input_text"), height=180, key=text_key)
    st.markdown("</div>", unsafe_allow_html=True)

    example_buttons(text_key, task_examples(mode_map[page]))
    voice_input_ui(text_key)

    if page == "Kpop":
        col1, col2 = st.columns(2)
        with col1:
            source_choice = st.selectbox(
                t("language_of_text"), ["auto"] + STUDY_LANG_CODES, index=0,
                format_func=lambda code: t("auto_detect") if code == "auto" else get_lang_display().get(code, code),
                key="media_source_lang",
            )
        with col2:
            ctx_type = st.selectbox(
                t("context_type"),
                [t("ctx_kpop"), t("ctx_kdrama"), t("ctx_cantodrama"), t("ctx_cdrama"), t("ctx_eng_tv"), t("ctx_inet"), t("ctx_pop")],
                index=0, key="media_ctx_type",
            )
        run_button = st.button(t("run"), use_container_width=True)

    elif page == "Coach":
        # ── Context settings (collapsible, after input) ──
        adv_label = TEXTS.get(st.session_state.ui_lang, {}).get("advanced_settings", "Settings")
        with st.expander("⚙️ " + adv_label, expanded=False):
            reg_col1, reg_col2 = st.columns([2, 2])
            with reg_col1:
                region_code = st.selectbox(
                    TEXTS.get(st.session_state.ui_lang, {}).get("region_mode", "Regional mode"),
                    [code for code, _ in REGION_OPTIONS],
                    index=([code for code, _ in REGION_OPTIONS].index(region_code) if region_code in [code for code, _ in REGION_OPTIONS] else 0),
                    format_func=region_label,
                    key="coach_region_mode",
                )
            with reg_col2:
                styles = [t("style_friend"), t("style_crush"), t("style_work"), t("style_formal"), t("style_cute"), t("style_cold"), t("style_kpop"), t("style_hk")]
                reply_style = st.selectbox(t("relation_mode"), styles, index=0, key="coach_style_select")
            st.caption(ui_text("coach_mean_tip", "Tip: Use a real message or situation for best results."))

        # ── Screenshot analysis (sibling expander, not nested) ──
        with st.expander(f"📷 {t('screenshot_mode')}", expanded=False):
            s_col1, s_col2 = st.columns(2)
            with s_col1:
                ss_lang = st.selectbox(t("language_of_text"), ["auto"] + STUDY_LANG_CODES, index=0,
                    format_func=lambda code: t("auto_detect") if code == "auto" else get_lang_display().get(code, code),
                    key="screenshot_lang")
            with s_col2:
                analyze_btn = st.button(t("analyze_screenshot_btn"), use_container_width=True, key="btn_analyze_screenshot")
            image_file = st.file_uploader(t("upload_screenshot"), type=["png", "jpg", "jpeg", "webm"], key="screenshot_uploader")
            if analyze_btn:
                    if not image_file:
                        st.warning(t("please_upload_image_first"))
                    else:
                        image_data = image_file.read()
                        persona_profile = get_persona_profile(ss_lang, st.session_state.native_lang)
                        persona_profile["region_mode"] = region_code
                        persona_profile["region_guidelines"] = build_region_guidelines(region_code, st.session_state.target_lang)
                        if HAVE_SCREENSHOT_ANALYZE and callable(analyze_screenshot_chat):
                            run_ai_task(task_fn=analyze_screenshot_chat,
                                task_kwargs=dict(image_bytes=image_data, image_name=image_file.name,
                                    assumed_lang=None if ss_lang == "auto" else ss_lang,
                                    native_lang=st.session_state.native_lang, target_lang=st.session_state.target_lang,
                                    region_mode=region_code, temperature=st.session_state.temperature,
                                    model=st.session_state.model_input, persona_profile=persona_profile),
                                history_kwargs=dict(username=st.session_state.username, mode="screenshot",
                                    source_lang=ss_lang, target_lang=st.session_state.native_lang,
                                    native_lang=st.session_state.native_lang,
                                    persona_code=st.session_state.persona_code, ui_lang=st.session_state.ui_lang,
                                    user_input=f"[screenshot] {image_file.name}"),
                                pron_lang=None)
                        else:
                            st.warning(TEXTS.get(st.session_state.ui_lang, {}).get("screenshot_not_available", "截图分析暂不可用。"))

    else:
        col1, col2 = st.columns(2)
        with col1:
            source_choice = st.selectbox(
                t("language_of_text"), ["auto"] + STUDY_LANG_CODES, index=0,
                format_func=lambda code: t("auto_detect") if code == "auto" else get_lang_display().get(code, code),
                key=f"{mode_map[page]}_source_lang",
            )
        with col2:
            run_button = st.button(t("run"), use_container_width=True)

    if run_button:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        elif page == "Coach":
            persona_profile = get_persona_profile(source_choice, target_choice)
            persona_profile["region_mode"] = region_code
            persona_profile["region_guidelines"] = build_region_guidelines(region_code, target_choice)
            style_with_region = f"{reply_style} | region_mode={region_code}"

            # ── Build conversation context from recent messages ──
            conv = st.session_state.get("coach_conversation", [])
            recent_context = conv[-MAX_CONTEXT_MESSAGES:] if len(conv) > 2 else conv
            # ── end context ──

            result_pair = run_ai_task(
                task_fn=chat_reply_coach_advanced,
                task_kwargs=dict(
                    text=text, source_lang=source_choice, target_lang=target_choice,
                    native_lang=st.session_state.native_lang, reply_style=style_with_region,
                    temperature=st.session_state.temperature, model=st.session_state.model_input,
                    persona_profile=persona_profile,
                    conversation_context=recent_context,
                ),
                history_kwargs=dict(
                    username=st.session_state.username, mode="coach",
                    source_lang=source_choice, target_lang=target_choice,
                    native_lang=st.session_state.native_lang,
                    persona_code=st.session_state.persona_code, ui_lang=st.session_state.ui_lang,
                    user_input=text,
                ),
                pron_lang=target_choice,
            )

            # ── Append to Coach conversation memory ──
            if result_pair is not None:
                result_data, _ = result_pair
                # Assistant text: use suggested_best_reply, or first reply option
                assistant_text = ""
                if isinstance(result_data, dict):
                    assistant_text = (
                        result_data.get("suggested_best_reply")
                        or (result_data.get("reply_options") or [{}])[0].get("text", "")
                        or ""
                    )
                if isinstance(result_data, str):
                    assistant_text = result_data

                if assistant_text:
                    st.session_state.coach_conversation.append(
                        {"role": "user", "text": text}
                    )
                    st.session_state.coach_conversation.append(
                        {"role": "assistant", "text": assistant_text}
                    )
                    # Trim to max messages
                    while len(st.session_state.coach_conversation) > MAX_CONVERSATION_MESSAGES:
                        st.session_state.coach_conversation.pop(0)
            # ── end conversation memory append ──

            try:
                detected_code = detect_language_code(text, st.session_state.model_input, st.session_state.temperature, persona_profile) or source_choice
                if detected_code in ("zh", "yue", "ko", "ja", "en"):
                    eval_data = evaluate_naturalness(
                        sentence=text, eval_lang=detected_code, native_lang=st.session_state.native_lang,
                        model=st.session_state.model_input, temperature=st.session_state.temperature,
                        persona_profile=persona_profile,
                    )
                    render_naturalness_panel(
                        TEXTS.get(st.session_state.ui_lang, {}).get("naturalness_score_title", "Naturalness Score"),
                        eval_data,
                    )
            except Exception:
                pass

        elif page == "Mean":
            persona_profile = get_persona_profile(source_choice, st.session_state.native_lang)
            run_ai_task(
                task_fn=explain_message_meaning,
                task_kwargs=dict(
                    text=text, source_lang=source_choice, native_lang=st.session_state.native_lang,
                    temperature=st.session_state.temperature, model=st.session_state.model_input,
                    persona_profile=persona_profile,
                ),
                history_kwargs=dict(
                    username=st.session_state.username, mode="mean",
                    source_lang=source_choice, target_lang=st.session_state.native_lang,
                    native_lang=st.session_state.native_lang,
                    persona_code=st.session_state.persona_code, ui_lang=st.session_state.ui_lang,
                    user_input=text,
                ),
                pron_lang=st.session_state.native_lang,
            )

        else:
            persona_profile = get_persona_profile(source_choice, st.session_state.native_lang)
            run_ai_task(
                task_fn=media_context_explain,
                task_kwargs=dict(
                    text=text, source_lang=source_choice, native_lang=st.session_state.native_lang,
                    context_type=ctx_type, temperature=st.session_state.temperature,
                    model=st.session_state.model_input, persona_profile=persona_profile,
                ),
                history_kwargs=dict(
                    username=st.session_state.username, mode="kpop",
                    source_lang=source_choice, target_lang=st.session_state.native_lang,
                    native_lang=st.session_state.native_lang,
                    persona_code=st.session_state.persona_code, ui_lang=st.session_state.ui_lang,
                    user_input=text,
                ),
                pron_lang=st.session_state.native_lang,
            )

    # ── Conversation history display (Coach, below results) ──
    if page == "Coach":
        conv = st.session_state.get("coach_conversation", [])
        if conv:
            st.markdown("### 💬 Conversation")
            for turn in conv:
                with st.chat_message(turn.get("role", "user")):
                    st.write(turn.get("text", ""))
            if st.button(t("new_conversation"), use_container_width=True, key="coach_new_conv"):
                st.session_state.coach_conversation = []
                st.rerun()


# ═══════════════════════════════════════════════════
# Grammar page
# ═══════════════════════════════════════════════════

def render_grammar_page():
    go_home_button()
    section_header(t("feature_grammar"), t("feature_grammar_sub"))

    product_note(
        ui_text("page_tip_title", "How to use this page"),
        ui_text("grammar_tip", "Paste one sentence or short paragraph. Choose your level so the correction is not too difficult."),
        "✍️",
    )
    phonetic_input_caption()

    apply_pending_text_area_update("grammar_text")
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_correct"), height=150, key="grammar_text")
    st.markdown("</div>", unsafe_allow_html=True)

    example_buttons("grammar_text", task_examples("grammar"))
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
            persona_profile = get_persona_profile(st.session_state.target_lang, st.session_state.target_lang)
            run_ai_task(
                task_fn=correct_grammar,
                task_kwargs=dict(
                    text=text, target_lang=st.session_state.target_lang,
                    native_lang=st.session_state.native_lang, level=level_code,
                    temperature=st.session_state.temperature, model=st.session_state.model_input,
                    persona_profile=persona_profile,
                ),
                history_kwargs=dict(
                    username=st.session_state.username, mode="grammar",
                    source_lang=st.session_state.target_lang, target_lang=st.session_state.target_lang,
                    native_lang=st.session_state.native_lang, persona_code=st.session_state.persona_code,
                    ui_lang=st.session_state.ui_lang, user_input=text,
                ),
                pron_lang=st.session_state.target_lang,
            )


# ═══════════════════════════════════════════════════
# Natural page
# ═══════════════════════════════════════════════════

def render_natural_page():
    go_home_button()
    section_header(t("feature_natural"), t("feature_natural_sub"))

    product_note(
        ui_text("page_tip_title", "How to use this page"),
        ui_text("natural_tip", "Paste a sentence that feels translated or stiff. Choose the tone you want."),
        "✨",
    )
    phonetic_input_caption()

    apply_pending_text_area_update("natural_text")
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_natural"), height=150, key="natural_text")
    st.markdown("</div>", unsafe_allow_html=True)

    example_buttons("natural_text", task_examples("natural"))
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
            persona_profile = get_persona_profile(st.session_state.target_lang, st.session_state.target_lang)
            run_ai_task(
                task_fn=suggest_natural_expression,
                task_kwargs=dict(
                    text=text, target_lang=st.session_state.target_lang,
                    native_lang=st.session_state.native_lang, tone_preference=tone_code,
                    temperature=st.session_state.temperature, model=st.session_state.model_input,
                    persona_profile=persona_profile,
                ),
                history_kwargs=dict(
                    username=st.session_state.username, mode="natural",
                    source_lang=st.session_state.target_lang, target_lang=st.session_state.target_lang,
                    native_lang=st.session_state.native_lang, persona_code=st.session_state.persona_code,
                    ui_lang=st.session_state.ui_lang, user_input=text,
                ),
                pron_lang=st.session_state.target_lang,
            )
            try:
                eval_data = evaluate_naturalness(
                    sentence=text, eval_lang=st.session_state.target_lang,
                    native_lang=st.session_state.native_lang,
                    model=st.session_state.model_input, temperature=st.session_state.temperature,
                    persona_profile=persona_profile,
                )
                render_naturalness_panel(
                    TEXTS.get(st.session_state.ui_lang, {}).get("naturalness_score_title", "Naturalness Score"),
                    eval_data,
                )
            except Exception:
                pass


# ═══════════════════════════════════════════════════
# Vocabulary page
# ═══════════════════════════════════════════════════

def render_vocabulary_page():
    go_home_button()
    section_header(t("feature_vocab"), t("feature_vocab_sub"))

    product_note(
        ui_text("page_tip_title", "How to use this page"),
        ui_text("vocab_tip", "Paste words, lyrics, homework text, or chat messages. The app will explain useful phrases."),
        "📚",
    )
    phonetic_input_caption()

    apply_pending_text_area_update("vocab_text")
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_vocab"), height=150, key="vocab_text")
    st.markdown("</div>", unsafe_allow_html=True)

    example_buttons("vocab_text", task_examples("vocabulary"))
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
            persona_profile = get_persona_profile("auto", st.session_state.target_lang)
            run_ai_task(
                task_fn=explain_vocabulary,
                task_kwargs=dict(
                    text=text, target_lang=st.session_state.target_lang,
                    native_lang=st.session_state.native_lang, max_items=max_items,
                    temperature=st.session_state.temperature, model=st.session_state.model_input,
                    persona_profile=persona_profile,
                ),
                history_kwargs=dict(
                    username=st.session_state.username, mode="vocabulary",
                    source_lang="auto", target_lang=st.session_state.target_lang,
                    native_lang=st.session_state.native_lang, persona_code=st.session_state.persona_code,
                    ui_lang=st.session_state.ui_lang, user_input=text,
                ),
                pron_lang=st.session_state.target_lang,
            )


# ═══════════════════════════════════════════════════
# Tone page
# ═══════════════════════════════════════════════════

def render_tone_page():
    go_home_button()
    section_header(t("feature_tone"), t("feature_tone_sub"))

    product_note(
        ui_text("page_tip_title", "How to use this page"),
        ui_text("tone_tip", "Paste a sentence before sending it. The app checks if it sounds cold, rude, polite, formal, or natural."),
        "🗣️",
    )
    phonetic_input_caption()

    apply_pending_text_area_update("tone_text")
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_tone"), height=150, key="tone_text")
    st.markdown("</div>", unsafe_allow_html=True)

    example_buttons("tone_text", task_examples("tone"))
    voice_input_ui("tone_text")

    col1, col2 = st.columns(2)
    with col1:
        tone_lang = st.selectbox(
            t("language_of_text"), STUDY_LANG_CODES,
            index=STUDY_LANG_CODES.index(st.session_state.target_lang),
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
                    text=text, lang=tone_lang, native_lang=st.session_state.native_lang,
                    temperature=st.session_state.temperature, model=st.session_state.model_input,
                    persona_profile=persona_profile,
                ),
                history_kwargs=dict(
                    username=st.session_state.username, mode="tone",
                    source_lang=tone_lang, target_lang=tone_lang,
                    native_lang=st.session_state.native_lang, persona_code=st.session_state.persona_code,
                    ui_lang=st.session_state.ui_lang, user_input=text,
                ),
                pron_lang=tone_lang,
            )


# ═══════════════════════════════════════════════════
# History page
# ═══════════════════════════════════════════════════

def render_history_page(username: str):
    go_home_button()
    section_header(t("history_title"), t("history_sub"))

    if _guard_guest(username):
        st.stop()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        filter_mode = st.selectbox(
            t("filter_mode"),
            ["All", "say", "mean", "coach", "kpop", "translate", "grammar", "natural", "vocabulary", "tone", "screenshot"],
            index=0,
            format_func=mode_filter_label,
        )
    with col2:
        filter_source = st.selectbox(t("filter_source"), ["All", "auto"] + STUDY_LANG_CODES, index=0, format_func=filter_lang_label)
    with col3:
        filter_target = st.selectbox(t("filter_target"), ["All"] + STUDY_LANG_CODES, index=0, format_func=filter_lang_label)
    with col4:
        filter_persona = st.selectbox(
            t("filter_persona"), ["All"] + PERSONA_CODES, index=0,
            format_func=lambda code: ui_text("all_filter", "All") if code == "All" else persona_display(code),
        )

    search_text = st.text_input(t("search_in"))
    limit = st.slider(t("show_last"), 10, 200, 50, 10)

    try:
        rows = fetch_history(
            username=username, limit=limit,
            mode=None if filter_mode == "All" else filter_mode,
            source_lang=None if filter_source == "All" else filter_source,
            target_lang=None if filter_target == "All" else filter_target,
            persona=None if filter_persona == "All" else filter_persona,
            search=search_text.strip() or None,
        )
    except Exception as e:
        st.warning(f"{t('history_load_failed')}: {e}")
        rows = []

    if rows:
        st.download_button(
            ui_text("export_history", "Export history as CSV"),
            data=rows_to_csv(rows),
            file_name=f"trilingua_history_{username or 'guest'}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    if not rows:
        st.info(t("no_history"))
    else:
        display = get_lang_display()
        for row in rows:
            timestamp = row.get("timestamp")
            try:
                if isinstance(timestamp, (int, float)):
                    ts_val = timestamp / 1000 if timestamp and timestamp > 1e12 else timestamp
                    timestamp_text = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts_val))
                else:
                    timestamp_text = str(timestamp)
            except Exception:
                timestamp_text = str(timestamp)

            mode_value = row.get("mode", "")
            source_label = display.get(row.get("source_lang", ""), row.get("source_lang", ""))
            target_label = display.get(row.get("target_lang", ""), row.get("target_lang", ""))
            persona_value = row.get("persona") or ""
            persona_label = persona_display(persona_value) if persona_value else ""

            title = f"{timestamp_text} • {mode_display_label(mode_value)} • {source_label} → {target_label} • {persona_label}"
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
                f'{t("tokens_label")}: {row.get("tokens_input", "-")}/{row.get("tokens_output", "-")} • '
                f'{t("latency_label")}: {row.get("latency_ms", "-")} ms'
            )
            st.markdown("</div>", unsafe_allow_html=True)


def render_about_page():
    go_home_button()
    section_header(t("about_title"))
    st.write(t("about_desc"))
