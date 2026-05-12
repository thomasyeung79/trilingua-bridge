import json
from typing import Dict, Any, Optional

import streamlit as st


# =========================
# Basic Config
# =========================

UI_LANGS = ["en", "zh", "ko"]

UI_LANG_DISPLAY = {
    "en": "English",
    "zh": "简体中文",
    "ko": "한국어",
}

STUDY_LANG_CODES = ["zh", "ko", "en"]

LANG_DISPLAY_BY_UI = {
    "en": {
        "zh": "Chinese (中文)",
        "ko": "Korean (한국어)",
        "en": "English",
    },
    "zh": {
        "zh": "中文",
        "ko": "韩语",
        "en": "英语",
    },
    "ko": {
        "zh": "중국어",
        "ko": "한국어",
        "en": "영어",
    },
}

PERSONA_CODES = [
    "friendly_chat",
    "teacher",
    "workplace",
    "travel",
    "pop_culture",
]

LEVEL_VALUES = ["beginner", "intermediate", "advanced"]
TONE_VALUES = ["neutral", "polite", "casual", "formal"]


# =========================
# i18n Texts
# =========================

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
        "creativity": "Creativity",
        "model": "Model",

        "nav_title": "Navigation",
        "nav_home": "Home",
        "nav_history": "History",
        "nav_about": "About",
        "back_home": "Back Home",

        "what_can": "Core Modes",
        "what_can_sub": "Practice real-life communication with AI.",
        "more_tools": "More Tools",
        "more_tools_sub": "Translation, grammar, natural expression, vocabulary, and tone analysis.",
        "tip": "Explanations use your native language; examples and rewrites use the target language.",

        "mode_say": "What I Want to Say",
        "mode_say_sub": "Translate your idea and get useful language notes.",
        "mode_mean": "What Does This Mean?",
        "mode_mean_sub": "Paste a message and understand the meaning, tone, and reply direction.",
        "mode_coach": "AI Chat Coach",
        "mode_coach_sub": "Paste a chat and get reply advice.",
        "mode_kpop": "K-pop / K-drama Context",
        "mode_kpop_sub": "Understand Korean lyrics or drama lines.",

        "feature_chat": "Chat Reply Assistant",
        "feature_translate": "Translation",
        "feature_grammar": "Grammar Correction",
        "feature_natural": "Natural Expression",
        "feature_vocab": "Vocabulary",
        "feature_tone": "Tone Analysis",

        "run": "Run",
        "input_text": "Input text",
        "enter_text_warn": "Please enter some text.",
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
        "show_pron": "Show pronunciation",
        "play_pron": "Play pronunciation",
        "voice_input": "Voice Input",
        "upload_audio": "Upload audio file",
        "transcribe": "Transcribe",
        "transcribing": "Transcribing...",
        "playing_audio": "Generating audio...",
        "tts_not_supported": "TTS not supported for this language.",
        "stt_unavailable": "Speech-to-text unavailable without OpenAI API key.",
        "pronunciation_label": "Pronunciation",

        "working": "Working...",
        "ok": "OK",
        "db_init_failed": "Database init failed",
        "ai_call_failed": "AI call failed",
        "history_load_failed": "History load failed",
        "history_save_failed": "History save failed",

        "model_info_prefix": "Model",
        "tokens_label": "Tokens(in/out)",
        "latency_label": "Latency",
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
        "creativity": "创意度",
        "model": "模型",

        "nav_title": "导航",
        "nav_home": "首页",
        "nav_history": "学习记录",
        "nav_about": "关于",
        "back_home": "返回首页",

        "what_can": "核心模式",
        "what_can_sub": "使用 AI 练习真实沟通。",
        "more_tools": "更多工具",
        "more_tools_sub": "翻译、语法、地道表达、词汇与语气分析。",
        "tip": "说明使用你的母语；示例和改写使用目标语言。",

        "mode_say": "我想怎么说",
        "mode_say_sub": "翻译你的表达并获得语言说明。",
        "mode_mean": "这是什么意思？",
        "mode_mean_sub": "理解对方消息的含义、语气和回复方向。",
        "mode_coach": "AI 聊天教练",
        "mode_coach_sub": "粘贴聊天内容，获得回复建议。",
        "mode_kpop": "K-pop / 韩剧语境",
        "mode_kpop_sub": "理解韩语歌词或韩剧台词。",

        "feature_chat": "聊天回复助手",
        "feature_translate": "翻译",
        "feature_grammar": "语法纠正",
        "feature_natural": "地道表达",
        "feature_vocab": "词汇讲解",
        "feature_tone": "语气分析",

        "run": "运行",
        "input_text": "输入文本",
        "enter_text_warn": "请输入文本。",
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
        "show_pron": "显示发音",
        "play_pron": "播放发音",
        "voice_input": "语音输入",
        "upload_audio": "上传音频文件",
        "transcribe": "转写",
        "transcribing": "正在转写...",
        "playing_audio": "正在生成音频...",
        "tts_not_supported": "该语言暂不支持语音合成。",
        "stt_unavailable": "未设置 OpenAI API 密钥，无法使用语音转写。",
        "pronunciation_label": "发音",

        "working": "正在处理...",
        "ok": "完成",
        "db_init_failed": "数据库初始化失败",
        "ai_call_failed": "AI 调用失败",
        "history_load_failed": "历史记录加载失败",
        "history_save_failed": "保存历史记录失败",

        "model_info_prefix": "模型",
        "tokens_label": "Tokens(入/出)",
        "latency_label": "延迟",
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
        "creativity": "창의성",
        "model": "모델",

        "nav_title": "내비게이션",
        "nav_home": "홈",
        "nav_history": "학습 기록",
        "nav_about": "소개",
        "back_home": "홈으로",

        "what_can": "핵심 모드",
        "what_can_sub": "AI와 함께 실제 대화를 연습하세요.",
        "more_tools": "추가 도구",
        "more_tools_sub": "번역, 문법, 자연스러운 표현, 어휘, 말투 분석.",
        "tip": "설명은 모국어로, 예문과 재작성은 학습 언어로 제공합니다.",

        "mode_say": "이렇게 말하고 싶어요",
        "mode_say_sub": "하고 싶은 말을 번역하고 설명을 받습니다.",
        "mode_mean": "무슨 뜻이에요?",
        "mode_mean_sub": "메시지의 의미, 톤, 답장 방향을 이해합니다.",
        "mode_coach": "AI 채팅 코치",
        "mode_coach_sub": "채팅 내용을 붙여넣고 답장 조언을 받습니다.",
        "mode_kpop": "K-pop / 드라마 맥락",
        "mode_kpop_sub": "한국어 가사나 드라마 대사를 이해합니다.",

        "feature_chat": "채팅 답장 도우미",
        "feature_translate": "번역",
        "feature_grammar": "문법 교정",
        "feature_natural": "자연스러운 표현",
        "feature_vocab": "어휘 설명",
        "feature_tone": "말투 분석",

        "run": "실행",
        "input_text": "입력 텍스트",
        "enter_text_warn": "텍스트를 입력하세요.",
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
        "show_pron": "발음 표시",
        "play_pron": "발음 재생",
        "voice_input": "음성 입력",
        "upload_audio": "오디오 파일 업로드",
        "transcribe": "전사",
        "transcribing": "전사 중...",
        "playing_audio": "오디오 생성 중...",
        "tts_not_supported": "해당 언어의 음성 합성을 지원하지 않습니다.",
        "stt_unavailable": "OpenAI API 키가 없으면 음성 전사를 사용할 수 없습니다.",
        "pronunciation_label": "발음",

        "working": "작업 중...",
        "ok": "완료",
        "db_init_failed": "데이터베이스 초기화 실패",
        "ai_call_failed": "AI 호출 실패",
        "history_load_failed": "기록 불러오기 실패",
        "history_save_failed": "기록 저장 실패",

        "model_info_prefix": "모델",
        "tokens_label": "토큰(입력/출력)",
        "latency_label": "지연",
    },
}


# =========================
# i18n Helpers
# =========================

def t(key: str) -> str:
    ui_lang = st.session_state.get("ui_lang", "en")
    return TEXTS.get(ui_lang, TEXTS["en"]).get(
        key,
        TEXTS["en"].get(key, key)
    )


def get_lang_display() -> Dict[str, str]:
    ui_lang = st.session_state.get("ui_lang", "en")
    return LANG_DISPLAY_BY_UI.get(ui_lang, LANG_DISPLAY_BY_UI["en"])


def persona_display(code: str) -> str:
    ui_lang = st.session_state.get("ui_lang", "en")
    return TEXTS.get(ui_lang, TEXTS["en"]).get("personas", {}).get(code, code)


def local_levels():
    ui_lang = st.session_state.get("ui_lang", "en")
    options = TEXTS[ui_lang]["levels"]
    mapping = dict(zip(options, LEVEL_VALUES))
    return options, mapping


def local_tones():
    ui_lang = st.session_state.get("ui_lang", "en")
    options = TEXTS[ui_lang]["tones"]
    mapping = dict(zip(options, TONE_VALUES))
    return options, mapping


# =========================
# Persona Profile
# =========================

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
        "pop_culture": "Trendy, upbeat, slang-aware, context from media or internet.",
    }.get(code, "Helpful, concise, culturally aware.")

    if target_lang == "ko":
        style = (
            "Use Korean conversational norms, appropriate honorifics or casual speech, "
            "short examples, and common set phrases."
        )
    elif target_lang == "zh":
        style = (
            "Use natural Chinese chat style when appropriate, "
            "with concise examples and idiomatic expressions."
        )
    else:
        style = (
            "Use international English with an Australian-friendly tone; "
            "natural, idiomatic, and inclusive phrasing."
        )

    meta_lang = {
        "en": "Explain meta-notes in English.",
        "zh": "说明和提示请使用中文表达。",
        "ko": "설명과 주석은 한국어로 작성하세요.",
    }.get(ui_lang, "")

    return {
        "code": code,
        "name": TEXTS.get(ui_lang, TEXTS["en"])
        .get("personas", {})
        .get(code, code),
        "style_hint": f"{persona_base} {style} {meta_lang}".strip(),
        "lang_context": {
            "source": source_lang,
            "target": target_lang,
            "ui": ui_lang,
        },
    }


# =========================
# CSS / UI Components
# =========================

def inject_css():
    st.markdown(
        """
        <style>
        html, body, [data-testid="stAppViewContainer"] {
            background: #f6f8fb !important;
        }

        .block-container {
            max-width: 980px;
            padding-top: 4rem;
            padding-bottom: 3rem;
        }

        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid #e5e7eb;
        }

        .hero {
            background: linear-gradient(135deg, #e7f3ff 0%, #f9f5ff 100%);
            border: 1px solid #e5e7eb;
            border-radius: 22px;
            padding: 28px 24px;
            box-shadow: 0 6px 24px rgba(16, 24, 40, 0.06);
            margin-bottom: 18px;
        }

        .hero h1 {
            margin: 0;
            font-size: 2rem;
            line-height: 1.2;
        }

        .hero p {
            color: #6b7280;
            font-size: 1.05rem;
            margin: 6px 0 0;
        }

        .card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 16px;
            box-shadow: 0 6px 24px rgba(16, 24, 40, 0.06);
            margin-bottom: 12px;
        }

        .accent-blue {
            border-left: 6px solid #6b8afd;
        }

        .accent-green {
            border-left: 6px solid #10b981;
        }

        .accent-purple {
            border-left: 6px solid #a78bfa;
        }

        .input-wrap {
            background: #f9fafb;
            border: 1px dashed #d1d5db;
            border-radius: 16px;
            padding: 10px 12px;
        }

        .output-wrap {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 16px;
            margin-bottom: 14px;
        }

        .sb-title {
            font-weight: 700;
            font-size: 1.05rem;
            margin: .25rem 0;
        }

        .sb-sub {
            color: #6b7280;
            font-size: .88rem;
            margin-bottom: .5rem;
        }
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
    css_class = {
        "blue": "accent-blue",
        "green": "accent-green",
        "purple": "accent-purple",
    }.get(accent, "accent-purple")

    st.markdown(f'<div class="card {css_class}">', unsafe_allow_html=True)
    st.markdown(f"### {title}")

    if subtitle:
        st.caption(subtitle)

    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Render Helpers
# =========================

def looks_like_json(value: str) -> bool:
    if not isinstance(value, str):
        return False

    value = value.strip()

    return (
        value.startswith("{") and value.endswith("}")
    ) or (
        value.startswith("[") and value.endswith("]")
    )


def render_result(result):
    if isinstance(result, (dict, list)):
        st.json(result)
        return

    if isinstance(result, str) and looks_like_json(result):
        try:
            st.json(json.loads(result))
            return
        except Exception:
            pass

    st.markdown(result if isinstance(result, str) else str(result))


def normalize_usage(usage: Dict[str, Any]) -> Dict[str, Any]:
    if not usage:
        return {}

    model = usage.get("model") or usage.get("model_name") or "-"

    prompt_tokens = usage.get("prompt_tokens", usage.get("input_tokens"))
    completion_tokens = usage.get(
        "completion_tokens",
        usage.get("output_tokens")
    )

    normalized = dict(usage)
    normalized["model"] = model
    normalized["prompt_tokens"] = (
        prompt_tokens if isinstance(prompt_tokens, int) else None
    )
    normalized["completion_tokens"] = (
        completion_tokens if isinstance(completion_tokens, int) else None
    )

    return normalized


def show_model_caption(usage: Dict[str, Any], latency_ms: int):
    usage_data = normalize_usage(usage)

    model = usage_data.get("model") or "-"
    prompt_tokens = usage_data.get("prompt_tokens")
    completion_tokens = usage_data.get("completion_tokens")

    prompt_tokens = prompt_tokens if isinstance(prompt_tokens, int) else "-"
    completion_tokens = completion_tokens if isinstance(completion_tokens, int) else "-"

    st.caption(
        f'{t("model_info_prefix")}: {model} • '
        f'{t("tokens_label")}: {prompt_tokens}/{completion_tokens} • '
        f'{t("latency_label")}: {latency_ms} ms'
    )
