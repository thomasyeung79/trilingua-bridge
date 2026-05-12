import json
import time
import inspect
from typing import Dict, Any, Optional, Callable, Tuple

import streamlit as st
from dotenv import load_dotenv

from helpers.db import init_db, insert_history, fetch_history
from helpers.ai_helper import (
    translate_text,
    correct_grammar,
    suggest_natural_expression,
    explain_vocabulary,
    analyze_tone,
    chat_reply_assistant,
)

# ----------------------- Boot -----------------------
load_dotenv()
st.set_page_config(page_title="TriLingua Bridge", layout="centered")

# 初始化数据库（放在 set_page_config 之后，且仅在失败时提示）
try:
    init_db()
except Exception as e:
    st.warning(f"Database init failed: {e}")

# ----------------------- i18n & Personas -----------------------
TEXTS = {
    "en": {
        "app_title": "TriLingua Bridge",
        "subtitle": "AI Language & Cross-Cultural Communication Assistant",
        "not_social": "This is not a social app. It is an AI assistant for real conversations.",
        "ui_language": "Interface Language",
        "account_title": "Account",
        "account_note": "Each user only sees their own data.",
        "username": "Username",
        "login": "Login",
        "logout": "Log out",
        "prefs_title": "Learning Preferences",
        "my_native": "My native language",
        "i_learn": "I want to learn",
        "persona": "Assistant Persona",
        "creativity": "Creativity (temperature)",
        "model": "Model",
        "nav_title": "Navigation",
        "nav_home": "Home",
        "nav_history": "History",
        "nav_about": "About",
        "back_home": "Back Home",
        "run": "Run",
        "enter_text_warn": "Please enter some text.",
        "mode_say": "What I Want to Say",
        "mode_say_sub": "Translate your idea and get useful language notes.",
        "mode_mean": "What Does This Mean?",
        "mode_mean_sub": "Paste a message and understand the meaning, tone, and reply direction.",
        "mode_coach": "AI Chat Coach",
        "mode_coach_sub": "Paste a chat and get reply advice.",
        "mode_kpop": "K-pop / K-drama Real Context",
        "mode_kpop_sub": "Understand Korean lyrics or drama lines.",
        "input_text": "Input text",
        "feature_chat": "Chat Reply Assistant",
        "feature_translate": "Translation",
        "feature_grammar": "Grammar Correction",
        "feature_natural": "Natural Expression",
        "feature_vocab": "Vocabulary",
        "feature_tone": "Tone Analysis",
        "source_language": "Source language",
        "auto_detect": "Auto-detect",
        "translate_btn": "Translate",
        "enter_text_translate": "Enter text to translate",
        "enter_text_correct": "Enter text to correct",
        "learner_level": "Learner level",
        "correct_btn": "Correct Grammar",
        "enter_text_natural": "Enter text for natural expression suggestions",
        "desired_tone": "Desired tone",
        "suggest_btn": "Suggest",
        "enter_text_vocab": "Enter text to extract and explain vocabulary",
        "max_items": "Max items",
        "explain_vocab_btn": "Explain Vocabulary",
        "language_of_text": "Language of the text",
        "enter_text_tone": "Enter text to analyze tone",
        "analyze_tone_btn": "Analyze Tone",
        "msg_language": "Message language",
        "your_message": "Your message",
        "generate_reply": "Generate Reply",
        "model_info_prefix": "Model",
        "history_title": "Learning History",
        "history_sub": "Only your records are shown.",
        "filter_mode": "Mode",
        "filter_source": "Source",
        "filter_target": "Target",
        "filter_persona": "Persona",
        "search_in": "Search in input/output",
        "show_last": "Show last N records",
        "no_history": "No history yet.",
        "about_title": "About TriLingua Bridge",
        "about_desc": "- AI tool for Chinese, Korean, and English learners.\n- Not a social platform.\n- Data is isolated by username.\n- Built with Python, Streamlit, SQLite, and OpenAI API.",
        "what_can": "Core Modes",
        "what_can_sub": "Practice real-life communication with AI.",
        "more_tools": "More Tools",
        "more_tools_sub": "Translation, grammar, natural expression, vocabulary, and tone analysis.",
        "tip": "Explanations use your native language; examples and rewrites use the target language.",
        "detected_source": "Detected source language",
        "input_label": "Input",
        "output_label": "Output",
        "levels": ["Beginner", "Intermediate", "Advanced"],
        "tones": ["Neutral", "Polite", "Casual", "Formal"],
        "personas": {
            "friendly_chat": "Friendly Chat Partner",
            "teacher": "Language Teacher",
            "workplace": "Workplace Assistant",
            "travel": "Travel Buddy",
            "pop_culture": "Pop Culture Friend",
        },
        "swap": "Swap",
    },
    "zh": {
        "app_title": "TriLingua Bridge",
        "subtitle": "AI 语言与跨文化沟通助手",
        "not_social": "这不是社交应用，而是用于真实沟通的 AI 助手。",
        "ui_language": "界面语言",
        "account_title": "账户",
        "account_note": "每位用户只能看到自己的数据。",
        "username": "用户名",
        "login": "登录",
        "logout": "退出",
        "prefs_title": "学习偏好",
        "my_native": "我的母语",
        "i_learn": "我想学习",
        "persona": "助理人格",
        "creativity": "创意度（temperature）",
        "model": "模型",
        "nav_title": "导航",
        "nav_home": "首页",
        "nav_history": "学习记录",
        "nav_about": "关于",
        "back_home": "返回首页",
        "run": "运行",
        "enter_text_warn": "请输入文本。",
        "mode_say": "我想怎么说",
        "mode_say_sub": "输入你想表达的话，获得翻译和语言说明。",
        "mode_mean": "这是什么意思？",
        "mode_mean_sub": "粘贴对方消息，理解含义、语气和回复方向。",
        "mode_coach": "AI 聊天教练",
        "mode_coach_sub": "粘贴聊天内容，获得回复建议。",
        "mode_kpop": "K-pop/K剧 真实语境",
        "mode_kpop_sub": "理解韩语歌词或韩剧台词。",
        "input_text": "输入文本",
        "feature_chat": "聊天回复助手",
        "feature_translate": "翻译",
        "feature_grammar": "语法纠正",
        "feature_natural": "地道表达",
        "feature_vocab": "词汇讲解",
        "feature_tone": "语气分析",
        "source_language": "源语言",
        "auto_detect": "自动检测",
        "translate_btn": "翻译",
        "enter_text_translate": "输入要翻译的文本",
        "enter_text_correct": "输入需要纠正的文本",
        "learner_level": "学习水平",
        "correct_btn": "开始纠正",
        "enter_text_natural": "输入文本获取更地道的表达",
        "desired_tone": "期望语气",
        "suggest_btn": "生成建议",
        "enter_text_vocab": "输入文本以提取并讲解词汇",
        "max_items": "最多条目",
        "explain_vocab_btn": "讲解词汇",
        "language_of_text": "文本语言",
        "enter_text_tone": "输入要分析语气的文本",
        "analyze_tone_btn": "分析语气",
        "msg_language": "消息语言",
        "your_message": "你的消息",
        "generate_reply": "生成回复",
        "model_info_prefix": "模型",
        "history_title": "学习记录",
        "history_sub": "仅显示你的个人记录。",
        "filter_mode": "模式",
        "filter_source": "源语言",
        "filter_target": "目标语言",
        "filter_persona": "人格",
        "search_in": "在输入/输出中搜索",
        "show_last": "显示最近 N 条",
        "no_history": "还没有记录。",
        "about_title": "关于 TriLingua Bridge",
        "about_desc": "- 面向中/韩/英学习者的 AI 工具。\n- 非社交应用。\n- 数据按用户名隔离。\n- 基于 Python、Streamlit、SQLite 与 OpenAI API。",
        "what_can": "核心模式",
        "what_can_sub": "用 AI 练习真实沟通。",
        "more_tools": "更多工具",
        "more_tools_sub": "翻译、语法、地道表达、词汇和语气分析。",
        "tip": "说明使用你的母语；示例与改写使用目标语言。",
        "detected_source": "检测到的源语言",
        "input_label": "输入",
        "output_label": "输出",
        "levels": ["入门", "中级", "高级"],
        "tones": ["中性", "礼貌", "随意", "正式"],
        "personas": {
            "friendly_chat": "友好聊天伙伴",
            "teacher": "语言老师",
            "workplace": "职场助手",
            "travel": "旅行搭子",
            "pop_culture": "流行文化好友",
        },
        "swap": "切换",
    },
    "ko": {
        "app_title": "TriLingua Bridge",
        "subtitle": "AI 언어 · 다문화 커뮤니케이션 도우미",
        "not_social": "이 앱은 소셜 앱이 아니라 실제 대화를 위한 AI 도우미입니다.",
        "ui_language": "인터페이스 언어",
        "account_title": "계정",
        "account_note": "각 사용자는 자신의 데이터만 볼 수 있습니다.",
        "username": "사용자명",
        "login": "로그인",
        "logout": "로그아웃",
        "prefs_title": "학습 설정",
        "my_native": "모국어",
        "i_learn": "학습 언어",
        "persona": "어시스턴트 페르소나",
        "creativity": "창의성(temperature)",
        "model": "모델",
        "nav_title": "내비게이션",
        "nav_home": "홈",
        "nav_history": "학습 기록",
        "nav_about": "소개",
        "back_home": "홈으로",
        "run": "실행",
        "enter_text_warn": "텍스트를 입력하세요.",
        "mode_say": "이렇게 말하고 싶어요",
        "mode_say_sub": "하고 싶은 말을 번역하고 언어 설명을 받습니다.",
        "mode_mean": "무슨 뜻이에요?",
        "mode_mean_sub": "메시지의 의미, 톤, 답장 방향을 이해합니다.",
        "mode_coach": "AI 채팅 코치",
        "mode_coach_sub": "채팅 내용을 붙여넣고 답장 조언을 받습니다.",
        "mode_kpop": "K-pop/K-드라마 실제 맥락",
        "mode_kpop_sub": "한국어 가사나 드라마 대사를 이해합니다.",
        "input_text": "입력 텍스트",
        "feature_chat": "채팅 답장 도우미",
        "feature_translate": "번역",
        "feature_grammar": "문법 교정",
        "feature_natural": "자연스러운 표현",
        "feature_vocab": "어휘 설명",
        "feature_tone": "말투 분석",
        "source_language": "원문 언어",
        "auto_detect": "자동 감지",
        "translate_btn": "번역",
        "enter_text_translate": "번역할 텍스트 입력",
        "enter_text_correct": "교정할 텍스트 입력",
        "learner_level": "학습 단계",
        "correct_btn": "문법 교정",
        "enter_text_natural": "자연스러운 표현을 위한 텍스트",
        "desired_tone": "원하는 톤",
        "suggest_btn": "제안",
        "enter_text_vocab": "어휘 설명을 위한 텍스트",
        "max_items": "최대 항목 수",
        "explain_vocab_btn": "어휘 설명",
        "language_of_text": "텍스트 언어",
        "enter_text_tone": "말투 분석 텍스트",
        "analyze_tone_btn": "분석",
        "msg_language": "메시지 언어",
        "your_message": "메시지",
        "generate_reply": "답장 생성",
        "model_info_prefix": "모델",
        "history_title": "학습 기록",
        "history_sub": "개인 기록만 표시됩니다.",
        "filter_mode": "모드",
        "filter_source": "원문",
        "filter_target": "목표",
        "filter_persona": "페르소나",
        "search_in": "입력/출력 검색",
        "show_last": "최근 N개",
        "no_history": "아직 기록이 없습니다.",
        "about_title": "TriLingua Bridge 소개",
        "about_desc": "- 중/한/영 학습자를 위한 AI 도구.\n- 소셜 앱이 아닙니다.\n- 데이터는 사용자명으로 격리됩니다.\n- Python, Streamlit, SQLite, OpenAI API 기반.",
        "what_can": "핵심 모드",
        "what_can_sub": "AI와 함께 실제 대화를 연습하세요.",
        "more_tools": "추가 도구",
        "more_tools_sub": "번역, 문법, 자연스러운 표현, 어휘, 말투 분석.",
        "tip": "설명은 모국어로, 예문/재작성은 학습 언어로 제공합니다.",
        "detected_source": "감지된 원문 언어",
        "input_label": "입력",
        "output_label": "출력",
        "levels": ["초급", "중급", "고급"],
        "tones": ["중립", "공손", "캐주얼", "격식"],
        "personas": {
            "friendly_chat": "친근한 채팅 파트너",
            "teacher": "언어 선생님",
            "workplace": "직장 도우미",
            "travel": "여행 친구",
            "pop_culture": "팝컬처 친구",
        },
        "swap": "바꾸기",
    },
}

UI_LANGS = ["en", "zh", "ko"]
UI_LANG_DISPLAY = {"en": "English", "zh": "简体中文", "ko": "한국어"}

# 学习语言代码（与内容相关，不随 UI 变化）
STUDY_LANG_CODES = ["zh", "ko", "en"]

# 语言显示（随 UI 语言变化）
LANG_DISPLAY_BY_UI = {
    "en": {"zh": "Chinese (中文)", "ko": "Korean (한국어)", "en": "English"},
    "zh": {"zh": "中文", "ko": "韩语", "en": "英语"},
    "ko": {"zh": "중국어", "ko": "한국어", "en": "영어"},
}

# Personas（语言中立）
PERSONA_CODES = ["friendly_chat", "teacher", "workplace", "travel", "pop_culture"]

# Canonical values for level/tone
LEVEL_VALUES = ["beginner", "intermediate", "advanced"]
TONE_VALUES = ["neutral", "polite", "casual", "formal"]


def t(key: str) -> str:
    code = st.session_state.get("ui_lang", "en")
    return TEXTS.get(code, TEXTS["en"]).get(key, TEXTS["en"].get(key, key))


def get_lang_display() -> Dict[str, str]:
    return LANG_DISPLAY_BY_UI.get(st.session_state.get("ui_lang", "en"), LANG_DISPLAY_BY_UI["en"])


def persona_display(code: str) -> str:
    ui = st.session_state.get("ui_lang", "en")
    return TEXTS.get(ui, TEXTS["en"]).get("personas", {}).get(code, code)


def local_levels():
    ui = st.session_state.get("ui_lang", "en")
    opts = TEXTS[ui]["levels"]
    mapping = dict(zip(opts, LEVEL_VALUES))
    return opts, mapping


def local_tones():
    ui = st.session_state.get("ui_lang", "en")
    opts = TEXTS[ui]["tones"]
    mapping = dict(zip(opts, TONE_VALUES))
    return opts, mapping


def build_persona_profile(
    code: str,
    source_lang: str,
    target_lang: str,
    ui_lang: str,
) -> Dict[str, Any]:
    persona_base = {
        "friendly_chat": "Warm, supportive, concise. Encourage natural conversation.",
        "teacher": "Clear explanations, step-by-step scaffolding, gentle corrections.",
        "workplace": "Professional, succinct, culturally sensitive to business norms.",
        "travel": "Practical, friendly, phrase-focused, situational tips.",
        "pop_culture": "Trendy, upbeat, slang-aware, context from media/internet.",
    }.get(code, "Helpful, concise, culturally aware.")

    if target_lang == "ko":
        style = "Use Korean conversational norms (honorifics vs casual appropriately), short examples, and common set phrases."
    elif target_lang == "zh":
        style = "Use natural Chinese internet/chat style when appropriate, concise examples, and idiomatic expressions."
    else:
        style = "Use international English with an Australian-friendly tone; natural, idiomatic, and inclusive phrasing."

    meta_lang = {
        "en": "Explain meta-notes in English.",
        "zh": "说明和提示请使用中文表达。",
        "ko": "설명과 주석은 한국어로 작성하세요.",
    }.get(ui_lang, "")

    return {
        "code": code,
        "name": TEXTS.get(ui_lang, TEXTS["en"]).get("personas", {}).get(code, code),
        "style_hint": f"{persona_base} {style} {meta_lang}".strip(),
        "lang_context": {"source": source_lang, "target": target_lang, "ui": ui_lang},
    }


def safe_call(func: Callable, kwargs: Dict[str, Any]):
    sig = inspect.signature(func)
    params = sig.parameters
    k = dict((kk, vv) for kk, vv in kwargs.items() if kk in params)
    if "persona_profile" not in params and "persona" in params and "persona_profile" in kwargs:
        prof = kwargs["persona_profile"]
        k["persona"] = f"{prof.get('code','')} | {prof.get('name','')} | {prof.get('style_hint','')}"
    return func(**k)


# ----------------------- Helpers -----------------------
def safe_rerun():
    st.rerun()


def now_ms() -> int:
    return int(time.time() * 1000)


def insert_history_safe(
    username: str,
    mode: str,
    source_lang: str,
    target_lang: str,
    native_lang: str,
    persona_code: str,
    ui_lang: str,
    user_input: str,
    ai_output: str,
    usage: Dict[str, Any],
    latency_ms: int,
):
    try:
        insert_history(
            username=username,
            mode=mode,
            source_lang=source_lang,
            target_lang=target_lang,
            native_lang=native_lang,
            persona=persona_code,
            ui_lang=ui_lang,
            user_input=user_input,
            ai_output=ai_output,
            tokens_input=usage.get("prompt_tokens"),
            tokens_output=usage.get("completion_tokens"),
            model=usage.get("model"),
            latency_ms=latency_ms,
        )
    except TypeError:
        insert_history(
            username=username,
            feature=mode,
            source_lang=source_lang,
            target_lang=target_lang,
            native_lang=native_lang,
            ui_lang=ui_lang,
            user_input=user_input,
            ai_output=ai_output,
            extra={"persona": persona_code},
            tokens_input=usage.get("prompt_tokens"),
            tokens_output=usage.get("completion_tokens"),
            model=usage.get("model"),
            latency_ms=latency_ms,
        )
    except Exception as e:
        st.warning(f"History save failed: {e}")


def show_model_caption(usage: Dict[str, Any], latency_ms: int):
    model = usage.get("model") or "-"
    pt = usage.get("prompt_tokens")
    ct = usage.get("completion_tokens")
    pt = pt if isinstance(pt, int) else "-"
    ct = ct if isinstance(ct, int) else "-"
    st.caption(
        f'{t("model_info_prefix")}: {model} • '
        f'Tokens(in/out): {pt}/{ct} • '
        f'Latency: {latency_ms} ms'
    )


def inject_css():
    st.markdown(
        """
        <style>
        html, body, [data-testid="stAppViewContainer"]{ background:#f6f8fb !important; }
        .block-container{ max-width:980px; padding-top:5rem; padding-bottom:3rem; }
        [data-testid="stSidebar"]{ background:#ffffff; border-right:1px solid #e5e7eb; }
        .hero{ background:linear-gradient(135deg,#e7f3ff 0%,#f9f5ff 100%); border:1px solid #e5e7eb; border-radius:22px; padding:28px 24px; box-shadow:0 6px 24px rgba(16,24,40,0.06); margin-bottom:18px; }
        .hero h1{ margin:0; font-size:2rem; line-height:1.2; }
        .hero p{ color:#6b7280; font-size:1.05rem; margin:6px 0 0; }
        .card{ background:#ffffff; border:1px solid #e5e7eb; border-radius:16px; padding:16px; box-shadow:0 6px 24px rgba(16,24,40,0.06); margin-bottom:12px; }
        .accent-blue{ border-left:6px solid #6b8afd; }
        .accent-green{ border-left:6px solid #10b981; }
        .accent-purple{ border-left:6px solid #a78bfa; }
        .input-wrap{ background:#f9fafb; border:1px dashed #d1d5db; border-radius:16px; padding:10px 12px; }
        .output-wrap{ background:#ffffff; border:1px solid #e5e7eb; border-radius:16px; padding:16px; }
        .sb-title{ font-weight:700; font-size:1.05rem; margin:.25rem 0; }
        .sb-sub{ color:#6b7280; font-size:.88rem; margin-bottom:.5rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, note: Optional[str] = None):
    st.markdown('<div class="hero">', unsafe_allow_html=True)
    st.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p>{subtitle}</p>", unsafe_allow_html=True)
    if note:
        st.caption(note)
    st.markdown("</div>", unsafe_allow_html=True)


def section_header(title: str, subtitle: str = "", accent: str = "purple"):
    cls = {"blue": "accent-blue", "green": "accent-green", "purple": "accent-purple"}.get(accent, "accent-purple")
    st.markdown(f'<div class="card {cls}">', unsafe_allow_html=True)
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)
    st.markdown("</div>", unsafe_allow_html=True)


def feature_button(icon: str, title: str, desc: str, nav_page: str, key: str):
    if st.button(f"{icon}  {title}\n\n{desc}", key=key, use_container_width=True):
        st.session_state.page = nav_page
        safe_rerun()


def back_home_button():
    if st.button(f"🏠 {t('back_home')}", use_container_width=True):
        st.session_state.page = "Home"
        safe_rerun()


def run_ai_task(
    task_fn: Callable[..., Tuple[str, Dict[str, Any]]],
    task_kwargs: Dict[str, Any],
    history_kwargs: Dict[str, Any],
):
    start = now_ms()
    try:
        result = None
        usage = {}
        out = safe_call(task_fn, task_kwargs)
        if isinstance(out, tuple) and len(out) == 3:
            result, usage, detected = out
            if detected:
                usage = usage or {}
                usage["detected_lang"] = detected
            history_kwargs["source_lang"] = detected or history_kwargs.get("source_lang")
        elif isinstance(out, tuple) and len(out) == 2:
            result, usage = out
        else:
            result = str(out)
            usage = {}
        usage = usage or {}
    except Exception as e:
        st.error(f"AI call failed: {e}")
        return
    latency_ms = now_ms() - start

    st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
    try:
        st.json(json.loads(result))
    except Exception:
        st.markdown(result)
    if usage.get("detected_lang"):
        disp = get_lang_display()
        det = usage["detected_lang"]
        st.caption(f"{t('detected_source')}: {disp.get(det, det)}")
    show_model_caption(usage, latency_ms)
    st.markdown("</div>", unsafe_allow_html=True)

    insert_history_safe(
        username=history_kwargs["username"],
        mode=history_kwargs["mode"],
        source_lang=history_kwargs["source_lang"],
        target_lang=history_kwargs["target_lang"],
        native_lang=history_kwargs["native_lang"],
        persona_code=history_kwargs["persona_code"],
        ui_lang=history_kwargs["ui_lang"],
        user_input=history_kwargs["user_input"],
        ai_output=result,
        usage=usage,
        latency_ms=latency_ms,
    )


# ----------------------- State -----------------------
inject_css()

if "ui_lang" not in st.session_state:
    st.session_state.ui_lang = "en"
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "username" not in st.session_state:
    st.session_state.username = ""
if "native_lang" not in st.session_state:
    st.session_state.native_lang = "zh"
if "target_lang" not in st.session_state:
    st.session_state.target_lang = "ko"
if "persona_code" not in st.session_state:
    st.session_state.persona_code = PERSONA_CODES[0]
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.3
if "model_input" not in st.session_state:
    st.session_state.model_input = "gpt-4o-mini"

# ----------------------- Sidebar -----------------------
ui_label = TEXTS[st.session_state.ui_lang]["ui_language"]
ui_options = [UI_LANG_DISPLAY[c] for c in UI_LANGS]
cur_index = UI_LANGS.index(st.session_state.ui_lang)
sel_label = st.sidebar.selectbox(ui_label, ui_options, index=cur_index, key="ui_lang_select")
sel_code = UI_LANGS[ui_options.index(sel_label)]
if sel_code != st.session_state.ui_lang:
    st.session_state.ui_lang = sel_code
    safe_rerun()

st.sidebar.markdown(f'<div class="sb-title">{t("account_title")}</div>', unsafe_allow_html=True)
st.sidebar.markdown(f'<div class="sb-sub">{t("account_note")}</div>', unsafe_allow_html=True)
c1, c2 = st.sidebar.columns([3, 1])
with c1:
    username_input = st.text_input(t("username"), value=st.session_state.username, key="username_input")
with c2:
    if st.button(t("login"), use_container_width=True):
        st.session_state.username = username_input.strip()
        safe_rerun()

if not st.session_state.username:
    hero(t("app_title"), t("subtitle"), t("not_social"))
    st.caption(t("account_note"))
    st.stop()

st.sidebar.success(f"{t('username')}: {st.session_state.username}")
if st.sidebar.button(t("logout"), use_container_width=True):
    st.session_state.username = ""
    safe_rerun()

st.sidebar.markdown(f'<div class="sb-title">{t("prefs_title")}</div>', unsafe_allow_html=True)

ld = get_lang_display()
native_lang = st.sidebar.selectbox(
    t("my_native"),
    STUDY_LANG_CODES,
    index=STUDY_LANG_CODES.index(st.session_state.get("native_lang", "zh")) if st.session_state.get("native_lang", "zh") in STUDY_LANG_CODES else 0,
    format_func=lambda c: ld.get(c, c),
    key="native_lang",
)
target_lang = st.sidebar.selectbox(
    t("i_learn"),
    STUDY_LANG_CODES,
    index=STUDY_LANG_CODES.index(st.session_state.get("target_lang", "ko")) if st.session_state.get("target_lang", "ko") in STUDY_LANG_CODES else 1,
    format_func=lambda c: ld.get(c, c),
    key="target_lang",
)

col_swap_a, col_swap_b = st.sidebar.columns(2)
with col_swap_a:
    if st.button(f"⇄ {t('swap')}", use_container_width=True, key="swap_langs"):
        st.session_state.native_lang, st.session_state.target_lang = (
            st.session_state.target_lang, st.session_state.native_lang
        )
        safe_rerun()
with col_swap_b:
    pass

persona_code = st.sidebar.selectbox(
    t("persona"),
    PERSONA_CODES,
    index=PERSONA_CODES.index(st.session_state.get("persona_code", PERSONA_CODES[0])),
    format_func=persona_display,
    key="persona_code",
)
temperature = st.sidebar.slider(t("creativity"), 0.0, 1.0, st.session_state.get("temperature", 0.3), 0.1, key="temperature")
model = st.sidebar.text_input(t("model"), value=st.session_state.get("model_input", "gpt-4o-mini"), key="model_input")
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
labels = [lbl for _, lbl in NAV_ITEMS]
page_from_label = {lbl: pid for pid, lbl in NAV_ITEMS}
label_from_page = {pid: lbl for pid, lbl in NAV_ITEMS}

selected_label = st.sidebar.radio(
    t("nav_title"),
    labels,
    index=labels.index(label_from_page.get(st.session_state.page, labels[0])),
)
selected_page = page_from_label[selected_label]
if selected_page != st.session_state.page:
    st.session_state.page = selected_page
    safe_rerun()

page = st.session_state.page
username = st.session_state.username

# ----------------------- Pages -----------------------
if page == "Home":
    hero(t("app_title"), t("subtitle"), t("not_social"))
    section_header(t("what_can"), t("what_can_sub"))

    c1, c2 = st.columns(2)
    with c1:
        feature_button("🗣️", t("mode_say"), t("mode_say_sub"), "Say", "home_say")
    with c2:
        feature_button("❓", t("mode_mean"), t("mode_mean_sub"), "Mean", "home_mean")

    c3, c4 = st.columns(2)
    with c3:
        feature_button("🎯", t("mode_coach"), t("mode_coach_sub"), "Coach", "home_coach")
    with c4:
        feature_button("🎵", t("mode_kpop"), t("mode_kpop_sub"), "Kpop", "home_kpop")

    section_header(t("more_tools"), t("more_tools_sub"), accent="green")
    c5, c6 = st.columns(2)
    with c5:
        feature_button("🌐", t("feature_translate"), "", "Translate", "home_translate")
    with c6:
        feature_button("✍️", t("feature_grammar"), "", "Grammar", "home_grammar")
    c7, c8 = st.columns(2)
    with c7:
        feature_button("🎯", t("feature_natural"), "", "Natural", "home_natural")
    with c8:
        feature_button("📚", t("feature_vocab"), "", "Vocabulary", "home_vocab")
    feature_button("🗣️", t("feature_tone"), "", "Tone", "home_tone")

elif page in ["Say", "Translate"]:
    back_home_button()
    if page == "Say":
        section_header(t("mode_say"), t("mode_say_sub"))
        text_key = "say_text"
        mode_name = "say"
        btn_label = t("run")
        text_label = t("input_text")
    else:
        section_header(t("feature_translate"), t("tip"))
        text_key = "translate_text"
        mode_name = "translate"
        btn_label = t("translate_btn")
        text_label = t("enter_text_translate")

    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(text_label, height=150, key=text_key)
    st.markdown("</div>", unsafe_allow_html=True)

    cols = st.columns(2)
    with cols[0]:
        source_choice = st.selectbox(
            t("source_language"),
            ["auto"] + STUDY_LANG_CODES,
            index=0,
            format_func=lambda c: t("auto_detect") if c == "auto" else get_lang_display().get(c, c),
            key=f"{mode_name}_source_lang",
        )
    with cols[1]:
        run_btn = st.button(btn_label, use_container_width=True)

    if run_btn:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            persona_prof = build_persona_profile(
                code=persona_code,
                source_lang=source_choice,
                target_lang=target_lang,
                ui_lang=st.session_state.ui_lang,
            )
            run_ai_task(
                task_fn=translate_text,
                task_kwargs=dict(
                    text=text,
                    source_lang=source_choice,
                    target_lang=target_lang,
                    native_lang=native_lang,
                    temperature=temperature,
                    model=model,
                    persona_profile=persona_prof,
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
            )

elif page in ["Mean", "Coach", "Kpop"]:
    back_home_button()
    title_map = {"Mean": t("mode_mean"), "Coach": t("mode_coach"), "Kpop": t("mode_kpop")}
    sub_map = {"Mean": t("mode_mean_sub"), "Coach": t("mode_coach_sub"), "Kpop": t("mode_kpop_sub")}
    mode_map = {"Mean": "mean", "Coach": "coach", "Kpop": "kpop"}
    section_header(title_map[page], sub_map[page])

    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("input_text"), height=180, key=f"{mode_map[page]}_text")
    st.markdown("</div>", unsafe_allow_html=True)

    if page == "Kpop":
        source_choice = "ko"
        run_btn = st.button(t("run"), use_container_width=True)
    else:
        cols = st.columns(2)
        with cols[0]:
            source_choice = st.selectbox(
                t("language_of_text"),
                ["auto"] + STUDY_LANG_CODES,
                index=0,
                format_func=lambda c: t("auto_detect") if c == "auto" else get_lang_display().get(c, c),
                key=f"{mode_map[page]}_source_lang",
            )
        with cols[1]:
            run_btn = st.button(t("run"), use_container_width=True)

    if run_btn:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            out_lang = native_lang if page in ["Mean", "Coach"] else target_lang
            persona_prof = build_persona_profile(
                code=persona_code,
                source_lang=source_choice,
                target_lang=out_lang,
                ui_lang=st.session_state.ui_lang,
            )
            run_ai_task(
                task_fn=translate_text,
                task_kwargs=dict(
                    text=text,
                    source_lang=source_choice,
                    target_lang=out_lang,
                    native_lang=native_lang,
                    temperature=temperature,
                    model=model,
                    persona_profile=persona_prof,
                ),
                history_kwargs=dict(
                    username=username,
                    mode=mode_map[page],
                    source_lang=source_choice,
                    target_lang=out_lang,
                    native_lang=native_lang,
                    persona_code=persona_code,
                    ui_lang=st.session_state.ui_lang,
                    user_input=text,
                ),
            )

elif page == "Chat":
    back_home_button()
    section_header(t("feature_chat"), t("tip"))
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("your_message"), height=160, key="chat_message")
    st.markdown("</div>", unsafe_allow_html=True)
    cols = st.columns(2)
    with cols[0]:
        source_choice = st.selectbox(
            t("msg_language"),
            ["auto"] + STUDY_LANG_CODES,
            index=0,
            format_func=lambda c: t("auto_detect") if c == "auto" else get_lang_display().get(c, c),
            key="chat_source_lang",
        )
    with cols[1]:
        run_btn = st.button(t("generate_reply"), use_container_width=True)

    if run_btn:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            persona_prof = build_persona_profile(
                code=persona_code,
                source_lang=source_choice,
                target_lang=target_lang,
                ui_lang=st.session_state.ui_lang,
            )
            run_ai_task(
                task_fn=chat_reply_assistant,
                task_kwargs=dict(
                    text=text,
                    source_lang=source_choice,
                    target_lang=target_lang,
                    native_lang=native_lang,
                    temperature=temperature,
                    model=model,
                    persona_profile=persona_prof,
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
            )

elif page == "Grammar":
    back_home_button()
    section_header(t("feature_grammar"), t("tip"))
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_correct"), height=150, key="grammar_text")
    st.markdown("</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        levels, level_map = local_levels()
        level_label = st.selectbox(t("learner_level"), levels, index=1)
        level_code = level_map[level_label]
    with c2:
        run_btn = st.button(t("correct_btn"), use_container_width=True)

    if run_btn:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            persona_prof = build_persona_profile(
                code=persona_code,
                source_lang=target_lang,
                target_lang=target_lang,
                ui_lang=st.session_state.ui_lang,
            )
            run_ai_task(
                task_fn=correct_grammar,
                task_kwargs=dict(
                    text=text,
                    target_lang=target_lang,
                    native_lang=native_lang,
                    level=level_code,
                    temperature=temperature,
                    model=model,
                    persona_profile=persona_prof,
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
            )

elif page == "Natural":
    back_home_button()
    section_header(t("feature_natural"), t("tip"))
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_natural"), height=150, key="natural_text")
    st.markdown("</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        tones, tone_map = local_tones()
        tone_label = st.selectbox(t("desired_tone"), tones, index=0)
        tone_code = tone_map[tone_label]
    with c2:
        run_btn = st.button(t("suggest_btn"), use_container_width=True)

    if run_btn:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            persona_prof = build_persona_profile(
                code=persona_code,
                source_lang=target_lang,
                target_lang=target_lang,
                ui_lang=st.session_state.ui_lang,
            )
            run_ai_task(
                task_fn=suggest_natural_expression,
                task_kwargs=dict(
                    text=text,
                    target_lang=target_lang,
                    native_lang=native_lang,
                    tone_preference=tone_code,
                    temperature=temperature,
                    model=model,
                    persona_profile=persona_prof,
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
            )

elif page == "Vocabulary":
    back_home_button()
    section_header(t("feature_vocab"), t("tip"))
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_vocab"), height=150, key="vocab_text")
    st.markdown("</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        max_items = st.slider(t("max_items"), 3, 12, 6, 1)
    with c2:
        run_btn = st.button(t("explain_vocab_btn"), use_container_width=True)

    if run_btn:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            persona_prof = build_persona_profile(
                code=persona_code,
                source_lang="auto",
                target_lang=target_lang,
                ui_lang=st.session_state.ui_lang,
            )
            run_ai_task(
                task_fn=explain_vocabulary,
                task_kwargs=dict(
                    text=text,
                    target_lang=target_lang,
                    native_lang=native_lang,
                    max_items=max_items,
                    temperature=temperature,
                    model=model,
                    persona_profile=persona_prof,
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
            )

elif page == "Tone":
    back_home_button()
    section_header(t("feature_tone"), t("tip"))
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_tone"), height=150, key="tone_text")
    st.markdown("</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        tone_lang = st.selectbox(
            t("language_of_text"),
            STUDY_LANG_CODES,
            index=STUDY_LANG_CODES.index(target_lang) if target_lang in STUDY_LANG_CODES else 0,
            format_func=lambda c: get_lang_display().get(c, c),
        )
    with c2:
        run_btn = st.button(t("analyze_tone_btn"), use_container_width=True)

    if run_btn:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            persona_prof = build_persona_profile(
                code=persona_code,
                source_lang=tone_lang,
                target_lang=tone_lang,
                ui_lang=st.session_state.ui_lang,
            )
            run_ai_task(
                task_fn=analyze_tone,
                task_kwargs=dict(
                    text=text,
                    lang=tone_lang,
                    native_lang=native_lang,
                    temperature=temperature,
                    model=model,
                    persona_profile=persona_prof,
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
            )

elif page == "History":
    back_home_button()
    section_header(t("history_title"), t("history_sub"))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        f_mode = st.selectbox(t("filter_mode"), ["All", "say", "mean", "coach", "kpop", "chat", "translate", "grammar", "natural", "vocabulary", "tone"], index=0)
    with c2:
        f_source = st.selectbox(t("filter_source"), ["All", "auto", "zh", "ko", "en"], index=0)
    with c3:
        f_target = st.selectbox(t("filter_target"), ["All", "zh", "ko", "en"], index=0)
    with c4:
        f_persona_code = st.selectbox(t("filter_persona"), ["All"] + PERSONA_CODES, index=0, format_func=lambda c: c if c == "All" else persona_display(c))

    search = st.text_input(t("search_in"))
    limit = st.slider(t("show_last"), 10, 200, 50, 10)

    rows = []
    try:
        rows = fetch_history(
            username=username,
            limit=limit,
            mode=None if f_mode == "All" else f_mode,
            source_lang=None if f_source == "All" else f_source,
            target_lang=None if f_target == "All" else f_target,
            persona=None if f_persona_code == "All" else f_persona_code,
            search=(search.strip() or None),
        )
    except TypeError:
        rows = fetch_history(
            username=username,
            limit=limit,
            feature=None if f_mode == "All" else f_mode,
            source_lang=None if f_source == "All" else f_source,
            target_lang=None if f_target == "All" else f_target,
            search=(search.strip() or None),
        )
        if f_persona_code != "All":
            rows = [r for r in rows if (r.get("persona") or r.get("extra", {}).get("persona")) == f_persona_code]
    except Exception as e:
        st.warning(f"History load failed: {e}")

    if not rows:
        st.info(t("no_history"))
    else:
        disp = get_lang_display()
        for r in rows:
            ts = r.get("timestamp")
            if isinstance(ts, (int, float)):
                ts_s = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts / 1000 if ts and ts > 1e12 else (ts or 0)))
            else:
                ts_s = str(ts)

            mode_val = r.get("mode", r.get("feature", ""))
            src = r.get("source_lang", "")
            tgt = r.get("target_lang", "")
            src_lbl = disp.get(src, src)
            tgt_lbl = disp.get(tgt, tgt)
            pcode = r.get("persona") or r.get("extra", {}).get("persona") or ""
            persona_lbl = persona_display(pcode) if pcode else ""
            title = f"{ts_s} • {mode_val} • {src_lbl} → {tgt_lbl} • {persona_lbl}"

            st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
            st.markdown(f"**{title}**")
            with st.expander(t("input_label")):
                st.write(r.get("user_input", ""))
            with st.expander(t("output_label")):
                out = r.get("ai_output") or ""
                try:
                    st.json(json.loads(out))
                except Exception:
                    st.markdown(out)
            st.caption(
                f'{t("model_info_prefix")}: {r.get("model","-")} • '
                f'Tokens(in/out): {r.get("tokens_input","-")}/{r.get("tokens_output","-")} • '
                f'Latency: {r.get("latency_ms","-")} ms'
            )
            st.markdown("</div>", unsafe_allow_html=True)

elif page == "About":
    back_home_button()
    section_header(t("about_title"))
    st.write(t("about_desc"))

st.caption("© 2026 TriLingua Bridge")
