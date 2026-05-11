import os
import json
import time
from typing import Dict, Any, List, Tuple
from dotenv import load_dotenv
import streamlit as st

from helpers.db import init_db, insert_history, fetch_history
from helpers.ai_helper import (
    translate_text,
    correct_grammar,
    suggest_natural_expression,
    explain_vocabulary,
    analyze_tone,
    chat_reply_assistant,
)

load_dotenv()
init_db()

st.set_page_config(page_title="TriLingua Bridge", layout="centered")

# ---------------- Language + UI Text ----------------
UI_LANGS = ["English", "简体中文", "한국어"]

UI_TEXT: Dict[str, Dict[str, str]] = {
    "English": {
        "app_title": "TriLingua Bridge",
        "subtitle": "Learn Chinese, Korean, and English with AI",
        "ui_language": "Interface Language",
        "account_title": "Account",
        "account_note": "Each user only sees their own data.",
        "username": "Username",
        "login": "Login",
        "logout": "Log out",
        "prefs_title": "Learning Preferences",
        "my_native": "My native language",
        "i_learn": "I want to learn",
        "nav_title": "Navigation",
        "nav_home": "🏠 Home",
        "nav_chat": "💬 Chat Assistant",
        "nav_translate": "🌐 Translation",
        "nav_grammar": "✍️ Grammar",
        "nav_natural": "🎯 Natural Expression",
        "nav_vocab": "📚 Vocabulary",
        "nav_tone": "🗣️ Tone",
        "nav_history": "🕘 History",
        "nav_about": "ℹ️ About",
        "tip": "Explanations use your native language; examples and rewrites use the target language.",
        "what_can": "What can you do here?",
        "what_can_sub": "Practice, translate, refine writing, and track your learning.",
        "feature_chat_title": "Chat Reply Assistant",
        "feature_chat_desc": "Translate, learn key words, and get natural/polite/casual replies.",
        "feature_translation_title": "Translation",
        "feature_translation_desc": "Fast, clear translation between Chinese, Korean, and English.",
        "feature_grammar_title": "Grammar Correction",
        "feature_grammar_desc": "Fix grammar with short explanations and examples.",
        "feature_natural_title": "Natural Expression",
        "feature_natural_desc": "Sound more native with tone-aware rewrites.",
        "feature_history_title": "Learning History",
        "feature_history_desc": "Review your past work by feature and language.",
        "chat_title": "Chat Reply Assistant",
        "chat_sub": "Type a message (in Chinese, Korean, or English). Get translation, vocab, and multiple reply styles.",
        "msg_language": "Message language",
        "auto_detect": "Auto-detect",
        "your_message": "Your message",
        "generate_reply": "Generate Reply",
        "detected_language": "Detected source language",
        "translation_to": "Translation",
        "important_vocabulary": "Important vocabulary",
        "natural_reply": "Natural reply",
        "polite_version": "Polite version",
        "casual_version": "Casual/friend version",
        "translation_title": "Translation",
        "translation_sub": "Translate between Chinese, Korean, and English.",
        "source_language": "Source language",
        "enter_text_translate": "Enter text to translate",
        "translate_btn": "Translate",
        "grammar_title": "Grammar Correction",
        "grammar_sub": "Paste your sentence or paragraph in the target language.",
        "enter_text_correct": "Enter text to correct",
        "learner_level": "Learner level",
        "correct_btn": "Correct Grammar",
        "natural_title": "Natural Expression",
        "natural_sub": "Get more native-like phrasing with tone control.",
        "enter_text_natural": "Enter text for natural expression suggestions",
        "desired_tone": "Desired tone",
        "suggest_btn": "Suggest",
        "vocab_title": "Vocabulary",
        "vocab_sub": "Extract key words/phrases with examples and usage notes.",
        "enter_text_vocab": "Enter text to extract and explain vocabulary",
        "max_items": "Max items",
        "explain_vocab_btn": "Explain Vocabulary",
        "tone_title": "Tone Analysis",
        "tone_sub": "Detect tone (polite, casual, formal) and get rewrites.",
        "language_of_text": "Language of the text",
        "enter_text_tone": "Enter text to analyze tone",
        "analyze_tone_btn": "Analyze Tone",
        "history_title": "Learning History",
        "history_sub": "Only your records are shown (user-isolated).",
        "filter_feature": "Feature",
        "filter_source": "Source",
        "filter_target": "Target",
        "search_in": "Search in input/output",
        "show_last": "Show last N records",
        "no_history": "No history yet.",
        "about_title": "About TriLingua Bridge",
        "about_desc": "- AI tool for Chinese, Korean, and English learners.\n- All data is user-isolated by username.\n- Inspired by modern learning apps with clean, friendly UI.",
        "enter_text_warn": "Please enter some text.",
        "enter_msg_warn": "Please enter a message.",
        "structured_reply_error": "Failed to generate a structured reply. Please try again.",
        "creativity": "Creativity (temperature)",
        "model_info_prefix": "Model",
    },
    "简体中文": {
        "app_title": "TriLingua Bridge",
        "subtitle": "用 AI 学习中文、韩语和英语",
        "ui_language": "界面语言",
        "account_title": "账户",
        "account_note": "每位用户只能看到自己的数据。",
        "username": "用户名",
        "login": "登录",
        "logout": "退出",
        "prefs_title": "学习偏好",
        "my_native": "我的母语",
        "i_learn": "我想学习",
        "nav_title": "导航",
        "nav_home": "🏠 首页",
        "nav_chat": "💬 聊天回复助手",
        "nav_translate": "🌐 翻译",
        "nav_grammar": "✍️ 语法纠正",
        "nav_natural": "🎯 地道表达",
        "nav_vocab": "📚 词汇讲解",
        "nav_tone": "🗣️ 语气分析",
        "nav_history": "🕘 学习记录",
        "nav_about": "ℹ️ 关于",
        "tip": "说明主要使用你的母语；示例与改写使用目标语言。",
        "what_can": "你可以在这里做什么？",
        "what_can_sub": "练习、翻译、优化表达，并追踪你的学习。",
        "feature_chat_title": "聊天回复助手",
        "feature_chat_desc": "翻译、词汇重点、自然/礼貌/朋友式回复。",
        "feature_translation_title": "翻译",
        "feature_translation_desc": "中、韩、英三语快捷清晰互译。",
        "feature_grammar_title": "语法纠正",
        "feature_grammar_desc": "修正语法并提供简短解释与示例。",
        "feature_natural_title": "地道表达",
        "feature_natural_desc": "提供更自然的语气与表达。",
        "feature_history_title": "学习记录",
        "feature_history_desc": "按功能与语言查看历史记录。",
        "chat_title": "聊天回复助手",
        "chat_sub": "输入中文/韩语/英语消息，获得翻译、词汇要点和多种回复风格。",
        "msg_language": "消息语言",
        "auto_detect": "自动检测",
        "your_message": "你的消息",
        "generate_reply": "生成回复",
        "detected_language": "检测到的源语言",
        "translation_to": "翻译",
        "important_vocabulary": "重点词汇",
        "natural_reply": "自然回复",
        "polite_version": "礼貌版本",
        "casual_version": "朋友式版本",
        "translation_title": "翻译",
        "translation_sub": "在中文、韩语和英语之间互译。",
        "source_language": "源语言",
        "enter_text_translate": "输入要翻译的文本",
        "translate_btn": "翻译",
        "grammar_title": "语法纠正",
        "grammar_sub": "请粘贴目标语言的句子或段落。",
        "enter_text_correct": "输入需要纠正的文本",
        "learner_level": "学习水平",
        "correct_btn": "开始纠正",
        "natural_title": "地道表达",
        "natural_sub": "获得更接近母语者的表达，并可调整语气。",
        "enter_text_natural": "输入文本获取更地道的表达",
        "desired_tone": "期望语气",
        "suggest_btn": "生成建议",
        "vocab_title": "词汇讲解",
        "vocab_sub": "提取关键词/短语并给出示例和用法提示。",
        "enter_text_vocab": "输入文本以提取并讲解词汇",
        "max_items": "最多条目",
        "explain_vocab_btn": "讲解词汇",
        "tone_title": "语气分析",
        "tone_sub": "识别礼貌/随意/正式语气并给出改写。",
        "language_of_text": "文本语言",
        "enter_text_tone": "输入要分析语气的文本",
        "analyze_tone_btn": "分析语气",
        "history_title": "学习记录",
        "history_sub": "仅显示你的个人记录（用户隔离）。",
        "filter_feature": "功能",
        "filter_source": "源语言",
        "filter_target": "目标语言",
        "search_in": "在输入/输出中搜索",
        "show_last": "显示最近 N 条",
        "no_history": "还没有记录。",
        "about_title": "关于 TriLingua Bridge",
        "about_desc": "- 面向中文、韩语、英语学习者的 AI 工具。\n- 所有数据以用户名隔离存储。\n- 借鉴现代学习应用的简洁友好风格。",
        "enter_text_warn": "请输入文本。",
        "enter_msg_warn": "请输入消息。",
        "structured_reply_error": "未生成结构化结果，请重试。",
        "creativity": "创意度（temperature）",
        "model_info_prefix": "模型",
    },
    "한국어": {
        "app_title": "TriLingua Bridge",
        "subtitle": "AI로 중국어·한국어·영어를 배우세요",
        "ui_language": "인터페이스 언어",
        "account_title": "계정",
        "account_note": "각 사용자는 자신의 데이터만 볼 수 있습니다.",
        "username": "사용자명",
        "login": "로그인",
        "logout": "로그아웃",
        "prefs_title": "학습 환경설정",
        "my_native": "나의 모국어",
        "i_learn": "학습 언어",
        "nav_title": "내비게이션",
        "nav_home": "🏠 홈",
        "nav_chat": "💬 채팅 답장 도우미",
        "nav_translate": "🌐 번역",
        "nav_grammar": "✍️ 문법 교정",
        "nav_natural": "🎯 자연스러운 표현",
        "nav_vocab": "📚 어휘 설명",
        "nav_tone": "🗣️ 말투 분석",
        "nav_history": "🕘 학습 기록",
        "nav_about": "ℹ️ 소개",
        "tip": "설명은 모국어로, 예시와 재작성은 학습 언어로 제공합니다.",
        "what_can": "여기서 무엇을 할 수 있나요?",
        "what_can_sub": "연습, 번역, 글 다듬기, 학습 기록 확인.",
        "feature_chat_title": "채팅 답장 도우미",
        "feature_chat_desc": "번역, 핵심 어휘, 자연/공손/친구말 답장.",
        "feature_translation_title": "번역",
        "feature_translation_desc": "중·한·영 간 빠르고 명확한 번역.",
        "feature_grammar_title": "문법 교정",
        "feature_grammar_desc": "문법을 고치고 짧은 설명과 예시 제공.",
        "feature_natural_title": "자연스러운 표현",
        "feature_natural_desc": "톤을 고려한 자연스러운 표현 제안.",
        "feature_history_title": "학습 기록",
        "feature_history_desc": "기능·언어별 과거 기록 보기.",
        "chat_title": "채팅 답장 도우미",
        "chat_sub": "중국어/한국어/영어 메시지를 입력하세요. 번역, 어휘, 다양한 답장을 제공합니다.",
        "msg_language": "메시지 언어",
        "auto_detect": "자동 감지",
        "your_message": "메시지",
        "generate_reply": "답장 생성",
        "detected_language": "감지된 원문 언어",
        "translation_to": "번역",
        "important_vocabulary": "중요 어휘",
        "natural_reply": "자연스러운 답장",
        "polite_version": "공손한 버전",
        "casual_version": "친구말 버전",
        "translation_title": "번역",
        "translation_sub": "중국어·한국어·영어 간 번역.",
        "source_language": "원문 언어",
        "enter_text_translate": "번역할 텍스트 입력",
        "translate_btn": "번역",
        "grammar_title": "문법 교정",
        "grammar_sub": "학습 언어 문장 또는 문단을 붙여넣으세요.",
        "enter_text_correct": "교정할 텍스트 입력",
        "learner_level": "학습 단계",
        "correct_btn": "문법 교정",
        "natural_title": "자연스러운 표현",
        "natural_sub": "톤을 조절하며 더 자연스러운 표현을 얻으세요.",
        "enter_text_natural": "자연스러운 표현 제안을 위한 텍스트 입력",
        "desired_tone": "원하는 톤",
        "suggest_btn": "제안",
        "vocab_title": "어휘 설명",
        "vocab_sub": "핵심 어휘/구를 추출해 예문과 사용 팁 제공.",
        "enter_text_vocab": "어휘 설명을 위한 텍스트 입력",
        "max_items": "최대 항목 수",
        "explain_vocab_btn": "어휘 설명",
        "tone_title": "말투 분석",
        "tone_sub": "공손/친근/격식 톤을 판별하고 재작성합니다.",
        "language_of_text": "텍스트 언어",
        "enter_text_tone": "말투를 분석할 텍스트 입력",
        "analyze_tone_btn": "말투 분석",
        "history_title": "학습 기록",
        "history_sub": "개인 기록만 표시됩니다(사용자 격리).",
        "filter_feature": "기능",
        "filter_source": "원문",
        "filter_target": "목표",
        "search_in": "입력/출력 검색",
        "show_last": "최근 N개 표시",
        "no_history": "아직 기록이 없습니다.",
        "about_title": "TriLingua Bridge 소개",
        "about_desc": "- 중국어/한국어/영어 학습자를 위한 AI 도구.\n- 모든 데이터는 사용자명으로 격리 저장됩니다.\n- 현대적이고 친화적인 UI에서 영감을 받았습니다.",
        "enter_text_warn": "텍스트를 입력하세요.",
        "enter_msg_warn": "메시지를 입력하세요.",
        "structured_reply_error": "구조화된 결과 생성에 실패했습니다. 다시 시도하세요.",
        "creativity": "창의성(temperature)",
        "model_info_prefix": "모델",
    },
}

# Study language codes
LANG_CODES = {"zh": "zh", "ko": "ko", "en": "en"}

# Localized display for study languages
LANG_DISPLAY = {
    "English": {"zh": "Chinese (中文)", "ko": "Korean (한국어)", "en": "English"},
    "简体中文": {"zh": "中文", "ko": "韩语", "en": "英语"},
    "한국어": {"zh": "중국어", "ko": "한국어", "en": "영어"},
}

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
        .block-container{ max-width: 980px; padding-top: 6rem; padding-bottom: 3rem; }
        [data-testid="stSidebar"]{ background:#ffffff; border-right:1px solid var(--border); }
        .sb-title{ font-weight:700; font-size:1.05rem; color:var(--text); margin:.25rem 0; }
        .sb-sub{ color:var(--muted); font-size:.88rem; margin-bottom:.5rem; }
        .hero{ background:var(--bg-hero); border:1px solid var(--border); border-radius:22px; padding:28px 24px; box-shadow:var(--shadow); margin-bottom:18px; }
        .hero h1{ margin:0; font-size:2.0rem; line-height:1.2; letter-spacing:-.005em; }
        .hero p.sub{ color:var(--muted); font-size:1.05rem; margin:6px 0 0 0; }
        .badge{ display:inline-block; padding:2px 8px; font-size:.78rem; color:#0f172a; background:#eef2ff; border:1px solid #dbeafe; border-radius:999px; margin-right:6px; }
        .grid{ display:grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap:14px; }
        @media (max-width: 950px){ .grid{ grid-template-columns: repeat(2, minmax(0, 1fr)); } .hero h1{ font-size:1.7rem; } }
        @media (max-width: 640px){ .grid{ grid-template-columns: 1fr; } .block-container{ padding-left:.5rem; padding-right:.5rem; } .hero{ padding:22px 16px; } }
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
        </style>
        """,
        unsafe_allow_html=True,
    )

def t(key: str) -> str:
    lang = st.session_state.get("ui_lang", "English")
    return UI_TEXT.get(lang, UI_TEXT["English"]).get(key, UI_TEXT["English"].get(key, key))

def hero(title: str, subtitle: str):
    st.markdown('<div class="hero">', unsafe_allow_html=True)
    st.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)
    st.markdown(f'<p class="sub">{subtitle}</p>', unsafe_allow_html=True)
    st.markdown(
        '<div style="margin-top:10px;">'
        '<span class="badge">🇨🇳 Chinese</span>'
        '<span class="badge">🇰🇷 Korean</span>'
        '<span class="badge">🇬🇧 English</span>'
        " • Learn together with AI"
        "</div>",
        unsafe_allow_html=True,
    )
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

def section_header(title: str, subtitle: str = ""):
    st.markdown('<div class="card accent-purple">', unsafe_allow_html=True)
    st.markdown(f'<div class="card-header"><span class="card-title">{title}</span></div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="card-sub">{subtitle}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def feature_button(icon: str, title: str, desc: str, target_label: str, key: str):
    clicked = st.button(
        f"{icon}  {title}\n\n{desc}",
        key=key,
        use_container_width=True,
        type="secondary",
    )
    if clicked:
        st.session_state["page"] = target_label
        st.rerun()

def back_home_button():
    if st.button("🏠 Back Home", use_container_width=True):
        st.session_state["page"] = "Home"
        st.rerun()

def now_ms() -> int:
    return int(time.time() * 1000)

inject_css()

# ---------------- Sidebar: UI language first ----------------
if "ui_lang" not in st.session_state:
    st.session_state.ui_lang = "English"

ui_lang_selected = st.sidebar.selectbox(
    UI_TEXT["English"]["ui_language"],
    UI_LANGS,
    index=UI_LANGS.index(st.session_state.ui_lang),
    key="ui_lang_select",
)
if ui_lang_selected != st.session_state.ui_lang:
    st.session_state.ui_lang = ui_lang_selected
    st.rerun()

# ---------------- Auth (username) ----------------
def require_login() -> str:
    if "username" not in st.session_state:
        st.session_state.username = ""
    st.sidebar.markdown(f'<div class="sb-title">{t("account_title")}</div>', unsafe_allow_html=True)
    st.sidebar.markdown(f'<div class="sb-sub">{t("account_note")}</div>', unsafe_allow_html=True)
    ucol1, ucol2 = st.sidebar.columns([3, 1])
    with ucol1:
        username_input = st.text_input(t("username"), value=st.session_state.username, key="username_input")
    with ucol2:
        login_clicked = st.button(t("login"), use_container_width=True)
    if login_clicked:
        st.session_state.username = username_input.strip()
    if st.session_state.username:
        st.sidebar.success(f"{t('username')}: {st.session_state.username}")
        if st.sidebar.button(t("logout"), use_container_width=True):
            st.session_state.username = ""
            st.rerun()
        return st.session_state.username
    else:
        hero(t("app_title"), t("subtitle"))
        st.caption(t("account_note"))
        st.stop()

username = require_login()

# ---------------- Sidebar: Learning preferences ----------------
st.sidebar.markdown(f'<div class="sb-title">{t("prefs_title")}</div>', unsafe_allow_html=True)

# Allow all three languages as native and target
study_lang_display = LANG_DISPLAY[st.session_state.ui_lang]
study_lang_codes = ["zh", "ko", "en"]

def lang_label_to_code(label: str) -> str:
    # Reverse map for the current UI language display
    for code, lbl in study_lang_display.items():
        if lbl == label:
            return code
    return "en"

native_label = st.sidebar.selectbox(
    t("my_native"),
    [study_lang_display[c] for c in study_lang_codes],
    index=0,
    key="native_choice",
)
native_lang = lang_label_to_code(native_label)

target_label = st.sidebar.selectbox(
    t("i_learn"),
    [study_lang_display[c] for c in study_lang_codes],
    index=1 if native_lang != "ko" else 0,
    key="target_choice",
)
target_lang = lang_label_to_code(target_label)

st.sidebar.markdown("---")
st.sidebar.markdown(f'<div class="sb-title">{t("nav_title")}</div>', unsafe_allow_html=True)

# Navigation with localized labels
# Navigation with localized labels
PAGE_DEFS = [
    ("Home", "🏠", t("nav_home")),
    ("Chat", "💬", t("nav_chat")),
    ("Translate", "🌐", t("nav_translate")),
    ("Grammar", "✍️", t("nav_grammar")),
    ("Natural", "🎯", t("nav_natural")),
    ("Vocabulary", "📚", t("nav_vocab")),
    ("Tone", "🗣️", t("nav_tone")),
    ("History", "🕘", t("nav_history")),
    ("About", "ℹ️", t("nav_about")),
]

labels = [lbl for _, _, lbl in PAGE_DEFS]

label_to_page = {
    lbl: pid for pid, _, lbl in PAGE_DEFS
}

page_to_label = {
    pid: lbl for pid, _, lbl in PAGE_DEFS
}

# 初始化页面
if "page" not in st.session_state:
    st.session_state["page"] = "Home"

# sidebar radio
selected_label = st.sidebar.radio(
    "Go to",
    labels,
    index=labels.index(
        page_to_label[st.session_state["page"]]
    )
)

# label -> page
selected_page = label_to_page[selected_label]

# 同步
if selected_page != st.session_state["page"]:
    st.session_state["page"] = selected_page
    st.rerun()

# 当前页面
current_page = st.session_state["page"]

# 同步 sidebar 和 page
st.session_state["page"] = current_page

st.sidebar.info(t("tip"))

# ---------------- Home ----------------
if current_page == "Home":
    hero(t("app_title"), t("subtitle"))
    section_header(t("what_can"), t("what_can_sub"))

    st.markdown('<div class="grid">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        feature_button("💬", t("feature_chat_title"), t("feature_chat_desc"), "Chat", "fc_chat")
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        feature_button("🌐", t("feature_translation_title"), t("feature_translation_desc"), "Translate", "fc_translation")
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        feature_button("✍️", t("feature_grammar_title"), t("feature_grammar_desc"), "Grammar", "fc_grammar")
        st.markdown('</div>', unsafe_allow_html=True)

    c4, c5, _ = st.columns(3)
    with c4:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        feature_button("🎯", t("feature_natural_title"), t("feature_natural_desc"), "Natural", "fc_natural")
        st.markdown('</div>', unsafe_allow_html=True)
    with c5:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        feature_button("🕘", t("feature_history_title"), t("feature_history_desc"), "History", "fc_history")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Chat Assistant ----------------
elif current_page == "Chat":
    back_home_button()
    section_header(f'{t("chat_title")} 💬', t("chat_sub"))
    lang_choices = [t("auto_detect")] + [study_lang_display[c] for c in study_lang_codes]
    sel = st.selectbox(t("msg_language"), lang_choices, index=0)
    if sel == t("auto_detect"):
        source_lang = "auto"
    else:
        source_lang = lang_label_to_code(sel)

    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("your_message"), height=140, key="chat_message")
    st.markdown('</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        temperature = st.slider(t("creativity"), 0.0, 1.0, 0.3, 0.1, key="chat_temp")
    with c2:
        run_btn = st.button(t("generate_reply"), use_container_width=True)

    if run_btn:
        if not text.strip():
            st.warning(t("enter_msg_warn"))
        else:
            start = now_ms()
            result_dict, usage = chat_reply_assistant(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                native_lang=native_lang,
                temperature=temperature,
            )
            latency_ms = now_ms() - start

            st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
            if isinstance(result_dict, dict) and result_dict:
                det = result_dict.get("detected_source_lang")
                trans = result_dict.get("translation")
                vocab = result_dict.get("vocabulary", [])
                r_nat = result_dict.get("reply_natural")
                r_pol = result_dict.get("reply_polite")
                r_cas = result_dict.get("reply_casual")

                if det:
                    card(t("detected_language"), study_lang_display.get(det, det), accent="yellow")
                if trans:
                    card(f'{t("translation_to")} → {study_lang_display.get(target_lang, target_lang)}', trans, accent="blue")

                if vocab:
                    st.markdown('<div class="card accent-green">', unsafe_allow_html=True)
                    st.markdown(f'<div class="card-header"><span class="card-title">{t("important_vocabulary")}</span></div>', unsafe_allow_html=True)
                    for item in vocab:
                        it = item.get("item")
                        meaning = item.get("meaning_native")
                        ex = item.get("example_target")
                        note = item.get("note")
                        st.write(f"- {it}: {meaning}")
                        if ex:
                            st.write(f"  • Example: {ex}")
                        if note:
                            st.write(f"  • Note: {note}")
                    st.markdown("</div>", unsafe_allow_html=True)

                if r_nat:
                    card(t("natural_reply"), r_nat, accent="purple")
                if r_pol:
                    card(t("polite_version"), r_pol, accent="green")
                if r_cas:
                    card(t("casual_version"), r_cas, accent="pink")

                insert_history(
                    username=username,
                    feature="chat",
                    source_lang=det or source_lang,
                    target_lang=target_lang,
                    native_lang=native_lang,
                    ui_lang=st.session_state.ui_lang,
                    user_input=text,
                    ai_output=json.dumps(result_dict, ensure_ascii=False, indent=2),
                    extra={"note": "chat_assistant"},
                    tokens_input=usage.get("prompt_tokens"),
                    tokens_output=usage.get("completion_tokens"),
                    model=usage.get("model"),
                    latency_ms=latency_ms,
                )
                st.caption(f'{t("model_info_prefix")}: {usage.get("model")}, Tokens (in/out): {usage.get("prompt_tokens")}/{usage.get("completion_tokens")}, Latency: {latency_ms} ms')
            else:
                st.error(t("structured_reply_error"))
            st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Translation ----------------
elif current_page == "Translate":
    back_home_button()
    section_header(f'{t("translation_title")} 🌐', t("translation_sub"))
    source_choice = st.selectbox(
        t("source_language"),
        [t("auto_detect")] + [study_lang_display[c] for c in study_lang_codes],
        index=0
    )
    source_lang = "auto" if source_choice == t("auto_detect") else lang_label_to_code(source_choice)

    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_translate"), height=150, key="translate_text")
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        temperature = st.slider(t("creativity"), 0.0, 1.0, 0.2, 0.1, key="translate_temp")
    with col2:
        run_btn = st.button(t("translate_btn"), use_container_width=True)

    if run_btn:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            start = now_ms()
            result, usage = translate_text(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                native_lang=native_lang,
                temperature=temperature
            )
            latency_ms = now_ms() - start
            st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
            card(t("translation_title"), result, accent="blue")
            st.caption(f'{t("model_info_prefix")}: {usage.get("model")}, Tokens (in/out): {usage.get("prompt_tokens")}/{usage.get("completion_tokens")}, Latency: {latency_ms} ms')
            st.markdown('</div>', unsafe_allow_html=True)

            insert_history(
                username=username,
                feature="translate",
                source_lang=source_lang,
                target_lang=target_lang,
                native_lang=native_lang,
                ui_lang=st.session_state.ui_lang,
                user_input=text,
                ai_output=result,
                extra={"note": "translation"},
                tokens_input=usage.get("prompt_tokens"),
                tokens_output=usage.get("completion_tokens"),
                model=usage.get("model"),
                latency_ms=latency_ms
            )

# ---------------- Grammar ----------------
elif current_page == "Grammar":
    back_home_button()
    section_header(f'{t("grammar_title")} ✍️', t("grammar_sub"))
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_correct"), height=150, key="grammar_text")
    st.markdown('</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        level = st.selectbox(t("learner_level"), ["Beginner", "Intermediate", "Advanced"], index=1)
    with col2:
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
                level=level.lower()
            )
            latency_ms = now_ms() - start
            st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
            card(t("grammar_title"), result, accent="green")
            st.caption(f'{t("model_info_prefix")}: {usage.get("model")}, Tokens (in/out): {usage.get("prompt_tokens")}/{usage.get("completion_tokens")}, Latency: {latency_ms} ms')
            st.markdown('</div>', unsafe_allow_html=True)
            insert_history(
                username=username,
                feature="grammar",
                source_lang=target_lang,
                target_lang=target_lang,
                native_lang=native_lang,
                ui_lang=st.session_state.ui_lang,
                user_input=text,
                ai_output=result,
                extra={"level": level},
                tokens_input=usage.get("prompt_tokens"),
                tokens_output=usage.get("completion_tokens"),
                model=usage.get("model"),
                latency_ms=latency_ms
            )

# ---------------- Natural Expression ----------------
elif current_page == "Natural":
    back_home_button()
    section_header(f'{t("natural_title")} 🎯', t("natural_sub"))
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_natural"), height=150, key="natural_text")
    st.markdown('</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        tone_pref = st.selectbox(t("desired_tone"), ["Neutral", "Polite", "Casual", "Formal"], index=0)
    with col2:
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
                tone_preference=tone_pref.lower()
            )
            latency_ms = now_ms() - start
            st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
            card(t("natural_title"), result, accent="purple")
            st.caption(f'{t("model_info_prefix")}: {usage.get("model")}, Tokens (in/out): {usage.get("prompt_tokens")}/{usage.get("completion_tokens")}, Latency: {latency_ms} ms')
            st.markdown('</div>', unsafe_allow_html=True)
            insert_history(
                username=username,
                feature="natural",
                source_lang=target_lang,
                target_lang=target_lang,
                native_lang=native_lang,
                ui_lang=st.session_state.ui_lang,
                user_input=text,
                ai_output=result,
                extra={"tone_preference": tone_pref},
                tokens_input=usage.get("prompt_tokens"),
                tokens_output=usage.get("completion_tokens"),
                model=usage.get("model"),
                latency_ms=latency_ms
            )

# ---------------- Vocabulary ----------------
elif current_page == "Vocabulary":
    back_home_button()
    section_header(f'{t("vocab_title")} 📚', t("vocab_sub"))
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_vocab"), height=150, key="vocab_text")
    st.markdown('</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        max_items = st.slider(t("max_items"), 3, 10, 5, 1, key="vocab_max")
    with col2:
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
                max_items=max_items
            )
            latency_ms = now_ms() - start
            st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
            card(t("vocab_title"), result, accent="yellow")
            st.caption(f'{t("model_info_prefix")}: {usage.get("model")}, Tokens (in/out): {usage.get("prompt_tokens")}/{usage.get("completion_tokens")}, Latency: {latency_ms} ms')
            st.markdown('</div>', unsafe_allow_html=True)
            insert_history(
                username=username,
                feature="vocabulary",
                source_lang="auto",
                target_lang=target_lang,
                native_lang=native_lang,
                ui_lang=st.session_state.ui_lang,
                user_input=text,
                ai_output=result,
                extra={"max_items": max_items},
                tokens_input=usage.get("prompt_tokens"),
                tokens_output=usage.get("completion_tokens"),
                model=usage.get("model"),
                latency_ms=latency_ms
            )

# ---------------- Tone ----------------
elif current_page == "Tone":
    back_home_button()
    section_header(f'{t("tone_title")} 🗣️', t("tone_sub"))
    tone_lang_choice = st.selectbox(
        t("language_of_text"),
        [study_lang_display[c] for c in study_lang_codes],
        index=study_lang_codes.index(target_lang) if target_lang in study_lang_codes else 0
    )
    tone_lang_code = lang_label_to_code(tone_lang_choice)

    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    text = st.text_area(t("enter_text_tone"), height=150, key="tone_text")
    st.markdown('</div>', unsafe_allow_html=True)
    run_btn = st.button(t("analyze_tone_btn"), use_container_width=True)

    if run_btn:
        if not text.strip():
            st.warning(t("enter_text_warn"))
        else:
            start = now_ms()
            result, usage = analyze_tone(text=text, lang=tone_lang_code, native_lang=native_lang)
            latency_ms = now_ms() - start
            st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
            card(t("tone_title"), result, accent="pink")
            st.caption(f'{t("model_info_prefix")}: {usage.get("model")}, Tokens (in/out): {usage.get("prompt_tokens")}/{usage.get("completion_tokens")}, Latency: {latency_ms} ms')
            st.markdown('</div>', unsafe_allow_html=True)
            insert_history(
                username=username,
                feature="tone",
                source_lang=tone_lang_code,
                target_lang=tone_lang_code,
                native_lang=native_lang,
                ui_lang=st.session_state.ui_lang,
                user_input=text,
                ai_output=result,
                extra={"analysis": "tone"},
                tokens_input=usage.get("prompt_tokens"),
                tokens_output=usage.get("completion_tokens"),
                model=usage.get("model"),
                latency_ms=latency_ms
            )

# ---------------- History ----------------
elif current_page == "History":
    back_home_button()
    section_header(f'{t("history_title")} 🕘', t("history_sub"))
    colf1, colf2, colf3 = st.columns(3)
    with colf1:
        f_feature = st.selectbox(t("filter_feature"), ["All", "chat", "translate", "grammar", "natural", "vocabulary", "tone"], index=0)
    with colf2:
        f_source = st.selectbox(t("filter_source"), ["All", "auto", "zh", "ko", "en"], index=0)
    with colf3:
        f_target = st.selectbox(t("filter_target"), ["All", "zh", "ko", "en"], index=0)
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    search = st.text_input(t("search_in"))
    st.markdown('</div>', unsafe_allow_html=True)
    limit = st.slider(t("show_last"), 10, 200, 50, 10)

    feature_filter = None if f_feature == "All" else f_feature
    src_filter = None if f_source == "All" else f_source
    tgt_filter = None if f_target == "All" else f_target

    rows = fetch_history(
        username=username,
        limit=limit,
        feature=feature_filter,
        source_lang=src_filter,
        target_lang=tgt_filter,
        search=search.strip() or None
    )

    if not rows:
        st.info(t("no_history"))
    else:
        for r in rows:
            src_lbl = study_lang_display.get(r["source_lang"], r["source_lang"])
            tgt_lbl = study_lang_display.get(r["target_lang"], r["target_lang"])
            title = f"{r['timestamp']} • {r['feature']} • {src_lbl} → {tgt_lbl}"
            st.markdown('<div class="output-wrap">', unsafe_allow_html=True)
            st.markdown(f'<div class="card accent-blue"><div class="card-header"><span class="card-title">{title}</span></div>', unsafe_allow_html=True)
            with st.expander("Input"):
                st.write(r["user_input"])
            with st.expander("Output"):
                out = r["ai_output"] or ""
                shown = False
                if r["feature"] == "chat":
                    try:
                        data = json.loads(out)
                        st.json(data)
                        shown = True
                    except Exception:
                        shown = False
                if not shown:
                    st.write(out)
            st.caption(f'{t("model_info_prefix")}: {r.get("model")}, Tokens (in/out): {r.get("tokens_input")}/{r.get("tokens_output")}, Latency: {r.get("latency_ms")} ms')
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ---------------- About ----------------
elif current_page == "About":
    back_home_button()
    section_header(f'{t("about_title")} ℹ️')
    st.write(t("about_desc"))

st.caption("© 2026 TriLingua Bridge")
