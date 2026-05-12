import os
import json
import time
from typing import Dict, Any, List, Optional, Tuple

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
init_db()

st.set_page_config(page_title="TriLingua Bridge", layout="centered")

# ----------------------- UI Constants -----------------------
# Supported UI languages for labels (fall back to English for missing keys)
UI_LANGS = ["English", "简体中文", "한국어"]

UI_TEXT: Dict[str, Dict[str, str]] = {
    "English": {
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
        "nav_modes": "Core Modes",
        "nav_tools": "More Tools",
        "nav_history": "History",
        "nav_about": "About",
        "back_home": "Back Home",
        "run": "Run",
        "enter_text_warn": "Please enter some text.",

        # Modes
        "mode_say": "What I Want to Say",
        "mode_say_sub": "Type what you want to say. Get direct translation, natural, young/casual, polite, close-friend versions, plus a short tone explanation.",
        "mode_mean": "What Does This Mean?",
        "mode_mean_sub": "Paste a message received from someone. Get literal meaning, natural meaning, hidden emotion/tone, social vibe, and how to interpret it.",
        "mode_coach": "AI Chat Coach",
        "mode_coach_sub": "Paste a chat snippet. Get the atmosphere, other person’s attitude, suitable replies, what’s too formal or MT-sounding, and a recommended reply.",
        "mode_kpop": "K-pop / K-drama Real Context",
        "mode_kpop_sub": "Enter a Korean lyric or drama line. Get Chinese/English meaning, word breakdown, grammar, natural usage, casual example, and cultural note.",
        "input_text": "Input text",

        # Tools
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

        # History
        "history_title": "Learning History",
        "history_sub": "Only your records are shown (user-isolated).",
        "filter_mode": "Mode",
        "filter_source": "Source",
        "filter_target": "Target",
        "filter_persona": "Persona",
        "search_in": "Search in input/output",
        "show_last": "Show last N records",
        "no_history": "No history yet.",

        # About
        "about_title": "About TriLingua Bridge",
        "about_desc": "- AI tool for Chinese, Korean, and English learners.\n- Not a social platform; it is an AI for real, cross-cultural conversations.\n- All data is isolated by username.\n- Built with Python, Streamlit, SQLite, and OpenAI API.",

        # Cards/sections
        "what_can": "Core Modes",
        "what_can_sub": "Practice real-life communication with AI in multiple tones and contexts.",
        "more_tools": "More Tools",
        "more_tools_sub": "Keep using translation, grammar check, natural expression, vocabulary, and tone analysis.",
        "tip": "Explanations use your native language; examples and rewrites use the target language.",

        # Sections titles used in outputs
        "detected_language": "Detected source language",
        "translation_to": "Translation",
        "important_vocabulary": "Important vocabulary",
        "natural_reply": "Natural reply",
        "polite_version": "Polite version",
        "casual_version": "Casual/friend version",
    },
    "简体中文": {
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
        "nav_modes": "核心模式",
        "nav_tools": "更多工具",
        "nav_history": "学习记录",
        "nav_about": "关于",
        "back_home": "返回首页",
        "run": "运行",
        "enter_text_warn": "请输入文本。",

        "mode_say": "我想怎么说",
        "mode_say_sub": "输入你想说的话，获得直译、自然表达、年轻/随意、礼貌、亲密朋友版本，附短语气说明。",
        "mode_mean": "这是什么意思？",
        "mode_mean_sub": "粘贴对方消息，获得字面/自然含义、潜在情绪/社交语气、如何理解与回应建议。",
        "mode_coach": "AI 聊天教练",
        "mode_coach_sub": "粘贴聊天片段，获得氛围、对方态度、合适回复、哪些过于正式/机翻感、推荐自然回复。",
        "mode_kpop": "K-pop/K剧 真实语境",
        "mode_kpop_sub": "输入韩语歌词或台词，获得中文/英文含义、词汇拆解、语法说明、地道用法、随例与文化注记。",
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
        "history_sub": "仅显示你的个人记录（用户隔离）。",
        "filter_mode": "模式",
        "filter_source": "源语言",
        "filter_target": "目标语言",
        "filter_persona": "人格",
        "search_in": "在输入/输出中搜索",
        "show_last": "显示最近 N 条",
        "no_history": "还没有记录。",

        "about_title": "关于 TriLingua Bridge",
        "about_desc": "- 面向中/韩/英学习者的 AI 工具。\n- 非社交应用，专注真实跨文化对话。\n- 数据按用户名隔离存储。\n- 基于 Python、Streamlit、SQLite 与 OpenAI API。",

        "what_can": "核心模式",
        "what_can_sub": "用 AI 练习真实沟通语境与多种语气。",
        "more_tools": "更多工具",
        "more_tools_sub": "继续使用翻译、语法、地道表达、词汇与语气分析等功能。",
        "tip": "说明使用你的母语；示例与改写使用目标语言。",

        "detected_language": "检测到的源语言",
        "translation_to": "翻译",
        "important_vocabulary": "重点词汇",
        "natural_reply": "自然回复",
        "polite_version": "礼貌版本",
        "casual_version": "朋友式版本",
    },
    "한국어": {
        "app_title": "TriLingua Bridge",
        "subtitle": "AI 언어 · 다문화 커뮤니케이션 도우미",
        "not_social": "이 앱은 소셜이 아닙니다. 실제 대화를 위한 AI 도우미입니다.",
        "ui_language": "인터페이스 언어",
        "account_title": "계정",
        "account_note": "각 사용자는 자신의 데이터만 볼 수 있습니다.",
        "username": "사용자명",
        "login": "로그인",
        "logout": "로그아웃",
        "prefs_title": "학습 환경설정",
        "my_native": "모국어",
        "i_learn": "학습 언어",
        "persona": "어시스턴트 페르소나",
        "creativity": "창의성(temperature)",
        "model": "모델",
        "nav_title": "내비게이션",
        "nav_home": "홈",
        "nav_modes": "핵심 모드",
        "nav_tools": "추가 도구",
        "nav_history": "학습 기록",
        "nav_about": "소개",
        "back_home": "홈으로",
        "run": "실행",
        "enter_text_warn": "텍스트를 입력하세요.",

        "mode_say": "이렇게 말하고 싶어요",
        "mode_say_sub": "하고 싶은 말을 입력하면 직역, 자연스러운 표현, 젊은/캐주얼, 공손, 친한 친구 버전과 간단한 톤 설명을 제공합니다.",
        "mode_mean": "무슨 뜻이에요?",
        "mode_mean_sub": "상대 메시지를 붙여넣으면 문자/자연 의미, 숨은 감정/말투, 사회적 뉘앙스, 이해 포인트를 설명합니다.",
        "mode_coach": "AI 채팅 코치",
        "mode_coach_sub": "채팅 일부를 붙여넣으면 분위기, 상대 태도, 적절한 답장, 과도하게 격식/번역투, 추천 답장을 제시합니다.",
        "mode_kpop": "K-pop/K-드라마 실제 맥락",
        "mode_kpop_sub": "한국어 가사나 대사를 입력하면 중/영 의미, 어휘 분해, 문법, 자연스러운 사용, 캐주얼 예문, 문화 노트를 제공합니다.",
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
        "enter_text_natural": "자연스러운 표현 제안을 위한 텍스트",
        "desired_tone": "원하는 톤",
        "suggest_btn": "제안",
        "enter_text_vocab": "어휘 설명을 위한 텍스트",
        "max_items": "최대 항목 수",
        "explain_vocab_btn": "어휘 설명",
        "language_of_text": "텍스트 언어",
        "enter_text_tone": "말투를 분석할 텍스트",
        "analyze_tone_btn": "분석",
        "msg_language": "메시지 언어",
        "your_message": "메시지",
        "generate_reply": "답장 생성",
        "model_info_prefix": "모델",

        "history_title": "학습 기록",
        "history_sub": "개인 기록만 표시됩니다(사용자 격리).",
        "filter_mode": "모드",
        "filter_source": "원문",
        "filter_target": "목표",
        "filter_persona": "페르소나",
        "search_in": "입력/출력 검색",
        "show_last": "최근 N개",
        "no_history": "아직 기록이 없습니다.",

        "about_title": "TriLingua Bridge 소개",
        "about_desc": "- 중/한/영 학습자를 위한 AI 도구\n- 소셜 앱이 아닌 실제 대화 보조 AI\n- 사용자명 단위로 데이터 격리\n- Python, Streamlit, SQLite, OpenAI API 기반",

        "what_can": "핵심 모드",
        "what_can_sub": "AI와 함께 실제 대화 맥락과 다양한 톤을 연습하세요.",
        "more_tools": "추가 도구",
        "more_tools_sub": "번역, 문법, 자연스러운 표현, 어휘, 말투 분석을 계속 사용하세요.",
        "tip": "설명은 모국어로, 예문/재작성은 학습 언어로 제공합니다.",

        "detected_language": "감지된 원문 언어",
        "translation_to": "번역",
        "important_vocabulary": "중요 어휘",
        "natural_reply": "자연스러운 답장",
        "polite_version": "공손한 버전",
        "casual_version": "친구말 버전",
    },
}

# Study language codes and display
STUDY_LANG_CODES = ["zh", "ko", "en"]
LANG_DISPLAY = {
    "English": {"zh": "Chinese (中文)", "ko": "Korean (한국어)", "en": "English"},
    "简体中文": {"zh": "中文", "ko": "韩语", "en": "英语"},
    "韩国어": {"zh": "중국어", "ko": "한국어", "en": "영어"},
}
# Note: For Korean UI we use key "한국어", but display mapping uses "韩国어" typo-safe fallback.
def get_lang_display():
    ui = st.session_state.get("ui_lang", "English")
    if ui in LANG_DISPLAY:
        return LANG_DISPLAY[ui]
    # Fallback for Korean key
    if ui == "한국어":
        return {"zh": "중국어", "ko": "한국어", "en": "영어"}
    return LANG_DISPLAY["English"]

PERSONAS = [
    "Korean Friend",
    "Korean Teacher",
    "Workplace Assistant",
    "Travel Assistant",
    "K-pop Fan Friend",
]

# ----------------------- CSS -----------------------
def inject_css():
    st.markdown(
        """
        <style>
        :root{
            --bg-soft:#f6f8fb;
            --bg-hero: linear-gradient(135deg, #e7f3ff 0%, #f9f5ff 100%);
            --card:#ffffff;
            --primary:#6b8afd;
            --accent:#00c2a8;
            --text:#1f2937;
            --muted:#6b7280;
            --border:#e5e7eb;
            --shadow:0 6px 24px rgba(16,24,40,0.06), 0 2px 4px rgba(16,24,40,0.04);
            --radius:16px;
            --radius-sm:12px;
            --input-bg:#f9fafb;
            --output-bg:#ffffff;
        }
        html, body, [data-testid="stAppViewContainer"]{
            background: var(--bg-soft) !important;
        }
        .block-container{ max-width: 980px; padding-top: 5rem; padding-bottom: 3rem; }
        [data-testid="stSidebar"]{ background:#ffffff; border-right:1px solid var(--border); }
        .sb-title{ font-weight:700; font-size:1.05rem; color:var(--text); margin:.25rem 0; }
        .sb-sub{ color:var(--muted); font-size:.88rem; margin-bottom:.5rem; }
        .hero{ background:var(--bg-hero); border:1px solid var(--border); border-radius:22px; padding:28px 24px; box-shadow:var(--shadow); margin-bottom:18px; }
        .hero h1{ margin:0; font-size:2.0rem; line-height:1.2; letter-spacing:-.005em; }
        .hero p.sub{ color:var(--muted); font-size:1.05rem; margin:6px 0 0 0; }
        .badge{ display:inline-block; padding:2px 8px; font-size:.78rem; color:#0f172a; background:#eef2ff; border:1px solid #dbeafe; border-radius:999px; margin-right:6px; }
        .grid{ display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:14px; }
        @media (max-width: 950px){ .grid{ grid-template-columns: 1fr; } .hero h1{ font-size:1.7rem; } }
        .card{ background:var(--card); border:1px solid var(--border); border-radius:var(--radius); padding:16px; box-shadow:var(--shadow); }
        .card-header{ display:flex; align-items:center; gap:10px; margin-bottom:6px; }
        .card-title{ font-weight:700; color:var(--text); }
        .card-sub{ color:var(--muted); font-size:.92rem; margin-top:2px; }
        .accent-blue{ border-left:6px solid #6b8afd; }
        .accent-green{ border-left:6px solid #10b981; }
        .accent-purple{ border-left:6px solid #a78bfa; }
        .accent-yellow{ border-left:6px solid #f59e0b; }
        .accent-pink{ border-left:6px solid #ec4899; }
        .input-wrap{ background:var(--input-bg); border:1px dashed #d1d5db; border-radius:var(--radius); padding:10px 12px; }
        .output-wrap{ background:var(--output-bg); border:1px solid var(--border); border-radius:var(--radius); padding:12px 14px; }
        div[data-testid="stTextArea"] textarea{ background:var(--input-bg); border:1px solid var(--border); border-radius:var(--radius-sm); }
        [data-testid="stExpander"]{ background:#ffffff; border-radius:var(--radius-sm); border:1px solid var(--border); }
        .home-grid { display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:16px; margin-top:8px; }
        .feature-btn {
            display:block; width:100%; text-align:left; padding:14px 16px; border:1px solid var(--border);
            border-radius:14px; background:white; box-shadow:var(--shadow);
        }
        .footer-note { color: var(--muted); font-size:.9rem; margin-top: 8px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def t(key: str) -> str:
    lang = st.session_state.get("ui_lang", "English")
    return UI_TEXT.get(lang, UI_TEXT["English"]).get(key, UI_TEXT["English"].get(key, key))

def hero(title: str, subtitle: str, note: Optional[str] = None):
    st.markdown('<div class="hero">', unsafe_allow_html=True)
    st.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)
    st.markdown(f'<p class="sub">{subtitle}</p>', unsafe_allow_html=True)
    if note:
        st.caption(note)
    st.markdown(
        '<div style="margin-top:10px;">'
        '<span class="badge">🇨🇳 Chinese</span>'
        '<span class="badge">🇰🇷 Korean</span>'
        '<span class="badge">🇬🇧 English</span>'
        " • Real conversations with AI"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

def section_header(title: str, subtitle: str = "", accent: str = "purple"):
    color_class = {
        "blue":"accent-blue","green":"accent-green","purple":"accent-purple",
        "yellow":"accent-yellow","pink":"accent-pink",
    }.get(accent, "accent-purple")
    st.markdown(f'<div class="card {color_class}">', unsafe_allow_html=True)
    st.markdown(f'<div class="card-header"><span class="card-title">{title}</span></div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="card-sub">{subtitle}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def card(title: str, content=None, accent: str = "blue"):
    color_class = {
        "blue":"accent-blue","green":"accent-green","purple":"accent-purple",
        "yellow":"accent-yellow","pink":"accent-pink",
    }.get(accent, "accent-blue")
    st.markdown(f'<div class="card {color_class}">', unsafe_allow_html=True)
    st.markdown(f'<div class="card-header"><span class="card-title">{title}</span></div>', unsafe_allow_html=True)
    if content is not None:
        st.write(content)
    st.markdown('</div>', unsafe_allow_html=True)

def feature_button(icon: str, title: str, desc: str, nav_page: str, key: str):
    if st.button(f"{icon}  {title}\n\n{desc}", key=key, use_container_width=True, type="secondary"):
        st.session_state["page"] = nav_page
        st.experimental_rerun()

def now_ms() -> int:
    return int(time.time() * 1000)

# ----------------------- App State -----------------------
inject_css()

if "ui_lang" not in st.session_state:
    st.session_state.ui_lang = "English"
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ----------------------- Sidebar: UI Language -----------------------
ui_lang_selected = st.sidebar.selectbox(
    t("ui_language"),
    UI_LANGS,
    index=UI_LANGS.index(st.session_state.ui_lang),
    key="ui_lang_select",
)
if ui_lang_selected != st.session_state.ui_lang:
    st.session_state.ui_lang = ui_lang_selected
    st.rerun()

# ----------------------- Sidebar: Account -----------------------
def require_login() -> str:
    if "username" not in st.session_state:
        st.session_state.username = ""
    st.sidebar.markdown(f'<div class="sb-title">{t("account_title")}</div>', unsafe_allow_html=True)
    st.sidebar.markdown(f'<div class="sb-sub">{t("account_note")}</div>', unsafe_allow_html=True)
    c1, c2 = st.sidebar.columns([3,1])
    with c1:
        username_input = st.text_input(t("username"), value=st.session_state.username, key="username_input")
    with c2:
        login_clicked = st.button(t("login"), use_container_width=True)
    if login_clicked:
        st.session_state.username = username_input.strip()
    if st.session_state.username:
        st.sidebar.success(f"{t('username')}: {st.session_state.username}")
        if st.sidebar.button(t("logout"), use_container_width=True):
            st.session_state.username = ""
            st.experimental_rerun()
        return st.session_state.username
    else:
        hero(t("app_title"), t("subtitle"), t("not_social"))
        st.caption(t("account_note"))
        st.stop()

username = require_login()

# ----------------------- Sidebar: Learning prefs + persona -----------------------
st.sidebar.markdown(f'<div class="sb-title">{t("prefs_title")}</div>', unsafe_allow_html=True)

ld = get_lang_display()

def select_lang(label_key: str, session_key: str, default_code: str):
    codes = STUDY_LANG_CODES
    current = st.session_state.get(session_key, default_code)
    try:
        default_idx = codes.index(current)
    except Exception:
        default_idx = 0
    return st.sidebar.selectbox(
        t(label_key),
        options=codes,
        index=default_idx,
        format_func=lambda c: ld.get(c, c),
        key=session_key
    )

native_lang = select_lang("my_native", "native_lang", "en")
target_lang = select_lang("i_learn", "target_lang", "ko")

persona = st.sidebar.selectbox(t("persona"), PERSONAS, index=0, key="persona")
temperature = st.sidebar.slider(t("creativity"), 0.0, 1.0, 0.3, 0.1, key="temperature")

# Optional: model override
default_model = "gpt-4o-mini"
model = st.sidebar.text_input(t("model"), value=default_model, key="model_input")

st.sidebar.info(t("tip"))

# ----------------------- Navigation -----------------------
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

selected_label = st.sidebar.radio(t("nav_title"), labels, index=labels.index(label_from_page[st.session_state.page]))
selected_page = page_from_label[selected_label]
if selected_page != st.session_state.page:
    st.session_state.page = selected_page
    st.rerun()

page = st.session_state.page

def back_home_button():
    if st.button(f"🏠 {t('back_home')}", use_container_width=True):
        st.session_state.page = "Home"
        st.rerun()

# ----------------------- Pages -----------------------
if page == "Home":
    hero(t("app_title"), t("subtitle"), t("not_social"))
    section_header(t("what_can"), t("what_can_sub"))

    st.markdown('<div class="home-grid">', unsafe_allow_html=True)
    # Core modes
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
    st.markdown('</div>', unsafe_allow_html=True)

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
    st.button("🗣️ " + t("feature_tone"), key="home_tone", use_container_width=True, on_click=lambda: (st.session_state.update({"page":"Tone"}), st.experimental_rerun()))

# ---------------- Mode: What I Want to Say ----------------
elif page == "Say":
    back_home_button()
    section_header(t("mode_say"), t("mode_say_sub"))
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("input_text"), height=150, key="say_text")
    st.markdown('</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    with cols[0]:
        source_choice = st.selectbox(
            t("source_language"),
            options=["auto"] + STUDY_LANG_CODES,
            index=0,
            format_func=lambda c: t("auto_detect") if c == "auto" else get_lang_display().get(c, c),
            key="say_source_lang"
        )
    with cols[1]:
        run_btn = st.button(t("run"), use_container_width=True)

    if run_btn:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            source_lang = "auto" if source_choice == t("auto_detect") else lang_label_to_code(source_choice)
            
            start = now_ms()

            result, usage = translate_text(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                native_lang=native_lang,
                temperature=temperature,
            )

            detected = source_lang
            latency_ms = now_ms() - start
            usage = usage or {}

            st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
            st.markdown(result)
            st.caption(
                f'{t("model_info_prefix")}: {usage.get("model")} • '
                f'Tokens(in/out): {usage.get("prompt_tokens")}/{usage.get("completion_tokens")} • '
                f'Latency: {latency_ms} ms'
            )
            st.markdown('</div>', unsafe_allow_html=True)

            insert_history(
                username=username,
                mode="say",
                source_lang=detected or source_choice,
                target_lang=target_lang,
                native_lang=native_lang,
                persona=persona,
                ui_lang=st.session_state.ui_lang,
                user_input=text,
                ai_output=result,
                tokens_input=usage.get("prompt_tokens"),
                tokens_output=usage.get("completion_tokens"),
                model=usage.get("model"),
                latency_ms=latency_ms,
            )

# ---------------- Mode: What Does This Mean? ----------------
elif page == "Mean":
    back_home_button()
    section_header(t("mode_mean"), t("mode_mean_sub"))
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("input_text"), height=150, key="mean_text")
    st.markdown('</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    with cols[0]:
        lang_choice = st.selectbox(
            t("language_of_text"),
            options=STUDY_LANG_CODES,
            index=STUDY_LANG_CODES.index(target_lang) if target_lang in STUDY_LANG_CODES else 0,
            format_func=lambda c: get_lang_display().get(c, c),
            key="mean_lang"
        )
    with cols[1]:
        run_btn = st.button(t("run"), use_container_width=True)

    if run_btn:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            start = now_ms()
            result, usage = mode_what_does_this_mean(
                text=text,
                lang=lang_choice,
                native_lang=native_lang,
                persona=persona,
                temperature=temperature,
                model=model,
            )
            latency_ms = now_ms() - start
            usage = usage or {}
            st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
            st.markdown(result)
            st.caption(f'{t("model_info_prefix")}: {usage.get("model")} • Tokens(in/out): {usage.get("prompt_tokens")}/{usage.get("completion_tokens")} • Latency: {latency_ms} ms')
            st.markdown('</div>', unsafe_allow_html=True)
            insert_history(
                username=username, mode="mean",
                source_lang=lang_choice, target_lang=lang_choice,
                native_lang=native_lang, persona=persona, ui_lang=st.session_state.ui_lang,
                user_input=text, ai_output=result,
                tokens_input=usage.get("prompt_tokens"), tokens_output=usage.get("completion_tokens"),
                model=usage.get("model"), latency_ms=latency_ms
            )

# ---------------- Mode: AI Chat Coach ----------------
elif page == "Coach":
    back_home_button()
    section_header(t("mode_coach"), t("mode_coach_sub"))
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("input_text"), height=200, key="coach_text")
    st.markdown('</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    with cols[0]:
        lang_choice = st.selectbox(
            t("language_of_text"),
            options=STUDY_LANG_CODES,
            index=STUDY_LANG_CODES.index(target_lang) if target_lang in STUDY_LANG_CODES else 0,
            format_func=lambda c: get_lang_display().get(c, c),
            key="coach_lang"
        )
    with cols[1]:
        run_btn = st.button(t("run"), use_container_width=True)

    if run_btn:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            start = now_ms()
            result, usage = mode_ai_chat_coach(
                text=text,
                lang=lang_choice,
                native_lang=native_lang,
                target_lang=target_lang,
                persona=persona,
                temperature=temperature,
                model=model,
            )
            latency_ms = now_ms() - start
            usage = usage or {}
            st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
            st.markdown(result)
            st.caption(f'{t("model_info_prefix")}: {usage.get("model")} • Tokens(in/out): {usage.get("prompt_tokens")}/{usage.get("completion_tokens")} • Latency: {latency_ms} ms')
            st.markdown('</div>', unsafe_allow_html=True)
            insert_history(
                username=username, mode="coach",
                source_lang=lang_choice, target_lang=target_lang,
                native_lang=native_lang, persona=persona, ui_lang=st.session_state.ui_lang,
                user_input=text, ai_output=result,
                tokens_input=usage.get("prompt_tokens"), tokens_output=usage.get("completion_tokens"),
                model=usage.get("model"), latency_ms=latency_ms
            )

# ---------------- Mode: K-pop / K-drama Context ----------------
elif page == "Kpop":
    back_home_button()
    section_header(t("mode_kpop"), t("mode_kpop_sub"))
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("input_text"), height=160, key="kpop_text")
    st.markdown('</div>', unsafe_allow_html=True)
    run_btn = st.button(t("run"), use_container_width=True)

    if run_btn:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            start = now_ms()
            result, usage = mode_kpop_kdrama_context(
                text=text,
                native_lang=native_lang,
                persona=persona,
                temperature=temperature,
                model=model,
            )
            latency_ms = now_ms() - start
            usage = usage or {}
            st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
            st.markdown(result)
            st.caption(f'{t("model_info_prefix")}: {usage.get("model")} • Tokens(in/out): {usage.get("prompt_tokens")}/{usage.get("completion_tokens")} • Latency: {latency_ms} ms')
            st.markdown('</div>', unsafe_allow_html=True)
            insert_history(
                username=username, mode="kpop",
                source_lang="ko", target_lang="ko",
                native_lang=native_lang, persona=persona, ui_lang=st.session_state.ui_lang,
                user_input=text, ai_output=result,
                tokens_input=usage.get("prompt_tokens"), tokens_output=usage.get("completion_tokens"),
                model=usage.get("model"), latency_ms=latency_ms
            )

# ---------------- Tool: Chat Reply Assistant (kept) ----------------
elif page == "Chat":
    back_home_button()
    section_header(t("feature_chat"), t("tip"))
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("your_message"), height=160, key="chat_message")
    st.markdown('</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    with cols[0]:
        lang_choice = st.selectbox(
            t("msg_language"),
            options=["auto"] + STUDY_LANG_CODES,
            index=0,
            format_func=lambda c: t("auto_detect") if c == "auto" else get_lang_display().get(c, c),
            key="chat_lang_choice"
        )
    with cols[1]:
        run_btn = st.button(t("generate_reply"), use_container_width=True)

    if run_btn:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            start = now_ms()
            result, usage, detected = chat_reply_assistant(
                text=text,
                source_lang=lang_choice,
                target_lang=target_lang,
                native_lang=native_lang,
                persona=persona,
                temperature=temperature,
                model=model,
            )
            latency_ms = now_ms() - start
            usage = usage or {}
            st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
            st.markdown(result)
            st.caption(f'{t("model_info_prefix")}: {usage.get("model")} • Tokens(in/out): {usage.get("prompt_tokens")}/{usage.get("completion_tokens")} • Latency: {latency_ms} ms')
            st.markdown('</div>', unsafe_allow_html=True)
            insert_history(
                username=username, mode="chat",
                source_lang=detected or lang_choice, target_lang=target_lang,
                native_lang=native_lang, persona=persona, ui_lang=st.session_state.ui_lang,
                user_input=text, ai_output=result,
                tokens_input=usage.get("prompt_tokens"), tokens_output=usage.get("completion_tokens"),
                model=usage.get("model"), latency_ms=latency_ms
            )

# ---------------- Tool: Translation ----------------
elif page == "Translate":
    back_home_button()
    section_header(t("feature_translate"), t("tip"))
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_translate"), height=150, key="translate_text")
    st.markdown('</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    with cols[0]:
        source_choice = st.selectbox(
            t("source_language"),
            options=["auto"] + STUDY_LANG_CODES,
            index=0,
            format_func=lambda c: t("auto_detect") if c == "auto" else get_lang_display().get(c, c)
        )
    with cols[1]:
        run_btn = st.button(t("translate_btn"), use_container_width=True)

    if run_btn:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            start = now_ms()
            result, usage, detected = translate_text(
                text=text,
                source_lang=source_choice,
                target_lang=target_lang,
                native_lang=native_lang,
                temperature=temperature,
                model=model,
            )
            latency_ms = now_ms() - start
            usage = usage or {}
            st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
            st.markdown(result)
            st.caption(f'{t("model_info_prefix")}: {usage.get("model")} • Tokens(in/out): {usage.get("prompt_tokens")}/{usage.get("completion_tokens")} • Latency: {latency_ms} ms')
            st.markdown('</div>', unsafe_allow_html=True)
            insert_history(
                username=username, mode="translate",
                source_lang=detected or source_choice, target_lang=target_lang,
                native_lang=native_lang, persona=persona, ui_lang=st.session_state.ui_lang,
                user_input=text, ai_output=result,
                tokens_input=usage.get("prompt_tokens"), tokens_output=usage.get("completion_tokens"),
                model=usage.get("model"), latency_ms=latency_ms
            )

# ---------------- Tool: Grammar ----------------
elif page == "Grammar":
    back_home_button()
    section_header(t("feature_grammar"), t("tip"))
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_correct"), height=150, key="grammar_text")
    st.markdown('</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    with cols[0]:
        level = st.selectbox(t("learner_level"), ["Beginner", "Intermediate", "Advanced"], index=1)
    with cols[1]:
        run_btn = st.button(t("correct_btn"), use_container_width=True)

    if run_btn:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            start = now_ms()
            result, usage = correct_grammar(
                text=text,
                target_lang=target_lang,
                native_lang=native_lang,
                level=level.lower(),
                persona=persona,
                temperature=temperature,
                model=model
            )
            latency_ms = now_ms() - start
            usage = usage or {}
            st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
            st.markdown(result)
            st.caption(f'{t("model_info_prefix")}: {usage.get("model")} • Tokens(in/out): {usage.get("prompt_tokens")}/{usage.get("completion_tokens")} • Latency: {latency_ms} ms')
            st.markdown('</div>', unsafe_allow_html=True)
            insert_history(
                username=username, mode="grammar",
                source_lang=target_lang, target_lang=target_lang,
                native_lang=native_lang, persona=persona, ui_lang=st.session_state.ui_lang,
                user_input=text, ai_output=result,
                tokens_input=usage.get("prompt_tokens"), tokens_output=usage.get("completion_tokens"),
                model=usage.get("model"), latency_ms=latency_ms
            )

# ---------------- Tool: Natural Expression ----------------
elif page == "Natural":
    back_home_button()
    section_header(t("feature_natural"), t("tip"))
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_natural"), height=150, key="natural_text")
    st.markdown('</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    with cols[0]:
        tone_pref = st.selectbox(t("desired_tone"), ["Neutral", "Polite", "Casual", "Formal"], index=0)
    with cols[1]:
        run_btn = st.button(t("suggest_btn"), use_container_width=True)

    if run_btn:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            start = now_ms()
            result, usage = suggest_natural_expression(
                text=text,
                target_lang=target_lang,
                native_lang=native_lang,
                tone_preference=tone_pref.lower(),
                persona=persona,
                temperature=temperature,
                model=model,
            )
            latency_ms = now_ms() - start
            usage = usage or {}
            st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
            st.markdown(result)
            st.caption(f'{t("model_info_prefix")}: {usage.get("model")} • Tokens(in/out): {usage.get("prompt_tokens")}/{usage.get("completion_tokens")} • Latency: {latency_ms} ms')
            st.markdown('</div>', unsafe_allow_html=True)
            insert_history(
                username=username, mode="natural",
                source_lang=target_lang, target_lang=target_lang,
                native_lang=native_lang, persona=persona, ui_lang=st.session_state.ui_lang,
                user_input=text, ai_output=result,
                tokens_input=usage.get("prompt_tokens"), tokens_output=usage.get("completion_tokens"),
                model=usage.get("model"), latency_ms=latency_ms
            )

# ---------------- Tool: Vocabulary ----------------
elif page == "Vocabulary":
    back_home_button()
    section_header(t("feature_vocab"), t("tip"))
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_vocab"), height=150, key="vocab_text")
    st.markdown('</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    with cols[0]:
        max_items = st.slider(t("max_items"), 3, 12, 6, 1)
    with cols[1]:
        run_btn = st.button(t("explain_vocab_btn"), use_container_width=True)

    if run_btn:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            start = now_ms()
            result, usage = explain_vocabulary(
                text=text,
                target_lang=target_lang,
                native_lang=native_lang,
                max_items=max_items,
                persona=persona,
                temperature=temperature,
                model=model
            )
            latency_ms = now_ms() - start
            usage = usage or {}
            st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
            st.markdown(result)
            st.caption(f'{t("model_info_prefix")}: {usage.get("model")} • Tokens(in/out): {usage.get("prompt_tokens")}/{usage.get("completion_tokens")} • Latency: {latency_ms} ms')
            st.markdown('</div>', unsafe_allow_html=True)
            insert_history(
                username=username, mode="vocabulary",
                source_lang="auto", target_lang=target_lang,
                native_lang=native_lang, persona=persona, ui_lang=st.session_state.ui_lang,
                user_input=text, ai_output=result,
                tokens_input=usage.get("prompt_tokens"), tokens_output=usage.get("completion_tokens"),
                model=usage.get("model"), latency_ms=latency_ms
            )

# ---------------- Tool: Tone ----------------
elif page == "Tone":
    back_home_button()
    section_header(t("feature_tone"), t("tip"))
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_tone"), height=150, key="tone_text")
    st.markdown('</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    with cols[0]:
        tone_lang = st.selectbox(
            t("language_of_text"),
            options=STUDY_LANG_CODES,
            index=STUDY_LANG_CODES.index(target_lang) if target_lang in STUDY_LANG_CODES else 0,
            format_func=lambda c: get_lang_display().get(c, c)
        )
    with cols[1]:
        run_btn = st.button(t("analyze_tone_btn"), use_container_width=True)

    if run_btn:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            start = now_ms()
            result, usage = analyze_tone(
                text=text,
                lang=tone_lang,
                native_lang=native_lang,
                persona=persona,
                temperature=temperature,
                model=model
            )
            latency_ms = now_ms() - start
            usage = usage or {}
            st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
            st.markdown(result)
            st.caption(f'{t("model_info_prefix")}: {usage.get("model")} • Tokens(in/out): {usage.get("prompt_tokens")}/{usage.get("completion_tokens")} • Latency: {latency_ms} ms')
            st.markdown('</div>', unsafe_allow_html=True)
            insert_history(
                username=username, mode="tone",
                source_lang=tone_lang, target_lang=tone_lang,
                native_lang=native_lang, persona=persona, ui_lang=st.session_state.ui_lang,
                user_input=text, ai_output=result,
                tokens_input=usage.get("prompt_tokens"), tokens_output=usage.get("completion_tokens"),
                model=usage.get("model"), latency_ms=latency_ms
            )

# ---------------- History ----------------
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
        f_persona = st.selectbox(t("filter_persona"), ["All"] + PERSONAS, index=0)

    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    search = st.text_input(t("search_in"))
    st.markdown('</div>', unsafe_allow_html=True)
    limit = st.slider(t("show_last"), 10, 200, 50, 10)

    rows = fetch_history(
        username=username,
        limit=limit,
        mode=None if f_mode == "All" else f_mode,
        source_lang=None if f_source == "All" else f_source,
        target_lang=None if f_target == "All" else f_target,
        persona=None if f_persona == "All" else f_persona,
        search=(search.strip() or None),
    )

    if not rows:
        st.info(t("no_history"))
    else:
        disp = get_lang_display()
        for r in rows:
            # Timestamp formatting
            ts = r.get("timestamp")
            if isinstance(ts, (int, float)):
                ts_s = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts/1000 if ts > 1e12 else ts))
            else:
                ts_s = str(ts)

            src_lbl = disp.get(r["source_lang"], r["source_lang"])
            tgt_lbl = disp.get(r["target_lang"], r["target_lang"])
            title = f"{ts_s} • {r['mode']} • {src_lbl} → {tgt_lbl} • {r.get('persona','')}"
            st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
            st.markdown(f'<div class="card accent-blue"><div class="card-header"><span class="card-title">{title}</span></div>', unsafe_allow_html=True)
            with st.expander("Input"):
                st.write(r["user_input"])
            with st.expander("Output"):
                out = r.get("ai_output") or ""
                # Display raw or JSON-decoded if it looks like JSON
                try:
                    data = json.loads(out)
                    st.json(data)
                except Exception:
                    st.markdown(out)
            st.caption(f'{t("model_info_prefix")}: {r.get("model")} • Tokens(in/out): {r.get("tokens_input")}/{r.get("tokens_output")} • Latency: {r.get("latency_ms")} ms')
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ---------------- About ----------------
elif page == "About":
    back_home_button()
    section_header(t("about_title"))
    st.write(t("about_desc"))

st.caption("© 2026 TriLingua Bridge")  # v2.0
