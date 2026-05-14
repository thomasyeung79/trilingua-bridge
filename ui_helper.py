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
        "zh": "중국어",
        "yue": "광둥어",
        "ko": "한국어",
        "en": "영어",
        "auto": "자동 감지",
    },
    "yue": {
        "zh": "普通話",
        "yue": "粵語",
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
        html, body, [data-testid="stAppViewContainer"] {
            background: #f6f8fb !important;
        }

        .block-container {
            max-width: 980px;
            padding-top: 3rem;
            padding-bottom: 3rem;
        }

        .output-wrap {
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 14px 16px;
            margin: 12px 0;
            background: #ffffff;
            box-shadow: 0 4px 16px rgba(16, 24, 40, 0.04);
        }

        .output-card {
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 14px 16px;
            margin: 12px 0;
            background: #ffffff;
            box-shadow: 0 4px 16px rgba(16, 24, 40, 0.04);
        }

        .input-wrap {
            border: 1px dashed #d1d5db;
            border-radius: 14px;
            padding: 10px 12px;
            background: #fafafa;
            margin-bottom: 10px;
        }

        .sb-title {
            font-weight: 700;
            font-size: 1rem;
            margin-top: 8px;
        }

        .sb-sub {
            color: #6b7280;
            font-size: 0.85rem;
            margin-bottom: 8px;
        }

        .hero-title {
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
        }

        .hero-sub {
            color: #6b7280;
            margin-bottom: 0.8rem;
            font-size: 1.05rem;
        }

        .hero-box {
            padding: 20px 18px;
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            background: linear-gradient(135deg, #e7f3ff 0%, #f9f5ff 100%);
            box-shadow: 0 6px 22px rgba(16, 24, 40, 0.06);
            margin-bottom: 18px;
        }

        .feature-card {
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 14px;
            text-align: center;
            background: #ffffff;
            margin-bottom: 8px;
            box-shadow: 0 4px 14px rgba(16, 24, 40, 0.035);
            transition: all 0.15s ease-in-out;
        }

        .feature-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 22px rgba(16, 24, 40, 0.08);
            border-color: #cbd5e1;
        }

        .feature-card-title {
            font-weight: 700;
            margin-top: 4px;
        }

        .feature-card-sub {
            color: #6b7280;
            font-size: 0.86rem;
            margin-top: 4px;
        }

        .section-title {
            font-weight: 750;
            font-size: 1.2rem;
            margin-top: 20px;
            margin-bottom: 4px;
        }

        .section-sub {
            color: #6b7280;
            margin-bottom: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, sub: str = ""):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

    if sub:
        st.markdown(f'<div class="section-sub">{sub}</div>', unsafe_allow_html=True)


def hero(title: str, sub: str = "", note: str = ""):
    st.markdown('<div class="hero-box">', unsafe_allow_html=True)
    st.markdown(f'<div class="hero-title">{title}</div>', unsafe_allow_html=True)

    if sub:
        st.markdown(f'<div class="hero-sub">{sub}</div>', unsafe_allow_html=True)

    if note:
        st.caption(note)

    st.markdown("</div>", unsafe_allow_html=True)


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
        st.markdown("### Reply Options")

        for index, option in enumerate(obj.get("reply_options", []), 1):
            if isinstance(option, dict):
                text = option.get("text", "")
                score = option.get("naturalness_score", "")
                tone = option.get("tone", "")
                st.markdown(f"**{index}. {text}**")

                if score or tone:
                    st.caption(f"Score: {score} • Tone: {tone}")
            else:
                st.markdown(f"**{index}. {option}**")

    section_map = [
        ("tone_notes", "Tone Notes"),
        ("cultural_notes", "Cultural Notes"),
        ("suggested_best_reply", "Suggested Best Reply"),
        ("reason", "Why this works"),
        ("clean_translation", "Clean Translation"),
        ("summary", "Summary"),
        ("recommended_understanding", "Recommended Understanding"),
        ("tone_summary", "Tone Summary"),
        ("intent", "Intent"),
        ("tips", "Tips"),
        ("clean", "Corrected Version"),
        ("notes", "Notes"),
        ("better_version", "Better Version"),
    ]

    for key, title in section_map:
        if obj.get(key):
            st.markdown(f"### {title}")
            st.write(obj[key])

    if obj.get("suggestions"):
        st.markdown("### Suggestions")
        for item in obj["suggestions"]:
            st.markdown(f"- {item}")

    if obj.get("examples"):
        st.markdown("### Examples")
        for item in obj["examples"]:
            st.markdown(f"- {item}")

    if obj.get("items"):
        st.markdown("### Items")
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
        st.markdown("### Key Phrases")
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
        st.markdown("### Slang / Pop Culture")
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
        st.markdown("### Pronunciation")
        pronunciation = obj["pronunciation_guide"]

        if isinstance(pronunciation, dict):
            st.write(
                f"{pronunciation.get('lang', '')}: "
                f"{pronunciation.get('text', '')}"
            )
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

    st.caption(
        f"{t('model_info_prefix')}: {model} • "
        f"{t('tokens_label')}: {prompt_tokens}/{completion_tokens} • "
        f"{t('latency_label')}: {latency_ms} ms"
    )


def normalize_usage(usage: Dict[str, Any]) -> Dict[str, Any]:
    usage = usage or {}

    return {
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "model": usage.get("model"),
    }


def feature_card(title: str, sub: str, icon: str = "✨", key: str = "") -> bool:
    st.markdown(
        f"""
        <div class="feature-card">
            <div style="font-size: 1.5rem;">{icon}</div>
            <div class="feature-card-title">{title}</div>
            <div class="feature-card-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return st.button(f"{icon} {title}", key=key, use_container_width=True)


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
        "show_pron": "Show pronunciation and TTS",
        "tip": "Tip: Keep inputs short and specific for best results.",
        "nav_home": "Home",
        "mode_say": "Say it better",
        "mode_say_sub": "Say something more naturally",
        "mode_mean": "What do they mean?",
        "mode_mean_sub": "Explain hidden meanings and tone",
        "mode_kpop": "Lyrics & Drama Context",
        "mode_kpop_sub": "K-pop lyrics / dramas / internet context",
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
        "filter_persona": "Persona",
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
        "screenshot_mode": "📷 Analyze chat screenshot",
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
        "show_pron": "显示发音与朗读",
        "tip": "提示：输入越具体越好。",
        "nav_home": "首页",
        "mode_say": "更自然地表达",
        "mode_say_sub": "让你的句子听起来更自然",
        "mode_mean": "Ta 在表达什么？",
        "mode_mean_sub": "解释潜台词与语气",
        "mode_kpop": "歌词与影视语境",
        "mode_kpop_sub": "K-pop / 影视 / 网络语境解析",
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
        "filter_persona": "人设",
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
        "screenshot_mode": "📷 聊天截图分析",
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
    },
    "ko": {},
    "yue": {},
}

TEXTS["ko"] = {**TEXTS["en"], **{
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
    "show_pron": "발음과 TTS 표시",
    "tip": "팁: 입력이 짧고 구체적일수록 결과가 좋습니다.",
    "app_title": "TriLingua Bridge",
    "subtitle": "중국어, 광둥어, 한국어, 영어를 위한 다국어 소통 도구.",
    "subtitle_v2": "중국어 / 광둥어 / 한국어 / 영어를 위한 다문화 커뮤니케이션 코치.",
    "mode_coach_v2": "AI 대화 코치",
    "mode_coach_sub_v2": "중국 / 홍콩 / 한국 / 호주 / 미국 문화 스타일에 맞춘 답장",
    "mode_say": "더 자연스럽게 말하기",
    "mode_say_sub": "문장을 더 자연스럽게 표현",
    "mode_mean": "무슨 뜻일까?",
    "mode_mean_sub": "숨은 의미와 말투 설명",
    "mode_kpop": "가사와 드라마 맥락",
    "mode_kpop_sub": "K-pop / 드라마 / 인터넷 맥락 설명",
    "feature_translate": "번역",
    "feature_grammar": "문법",
    "feature_grammar_sub": "수준별 문법 교정",
    "feature_natural": "자연스러운 표현",
    "feature_natural_sub": "원어민처럼 표현하기",
    "feature_vocab": "어휘",
    "feature_vocab_sub": "핵심 단어와 표현 설명",
    "feature_tone": "말투 분석",
    "feature_tone_sub": "공손함 / 격식 / 직접성 분석",
    "nav_history": "기록",
    "nav_about": "소개",
    "what_can_v2": "나만의 다문화 채팅 도우미",
    "not_social": "이 앱은 소셜 플랫폼이 아닙니다.",
    "back_home": "홈으로 돌아가기",
    "input_text": "텍스트 입력",
    "run": "실행",
    "translate_btn": "번역",
    "source_language": "원문 언어",
    "language_of_text": "텍스트 언어",
    "auto_detect": "자동 감지",
    "working": "처리 중...",
    "voice_input": "음성 입력",
    "upload_audio": "오디오 파일 업로드",
    "transcribe": "전사",
    "transcribing": "전사 중...",
    "ok": "완료",
    "relation_mode": "관계 / 스타일",
    "context_type": "맥락 유형",
    "history_title": "기록",
    "history_sub": "최근 작업",
    "about_title": "소개",
    "about_desc": "TriLingua Bridge v2 — 다문화 커뮤니케이션 코치.",
}}

TEXTS["yue"] = {**TEXTS["zh"], **{
    "ui_language": "介面語言",
    "account_title": "帳號",
    "account_note": "只會喺本地資料庫保存歷史記錄。",
    "username": "用戶名",
    "login": "登入",
    "logout": "登出",
    "prefs_title": "偏好設定",
    "my_native": "我嘅母語",
    "i_learn": "我想學",
    "persona": "人設",
    "creativity": "創意度",
    "model": "模型",
    "show_pron": "顯示發音同朗讀",
    "tip": "提示：輸入越具體越好。",
    "subtitle": "面向普通話、粵語、韓文、英文嘅多語言溝通工具。",
    "subtitle_v2": "跨文化溝通教練（支援普通話 / 粵語 / 韓文 / 英文）",
    "mode_say": "講得自然啲",
    "mode_say_sub": "令你句嘢聽落更自然",
    "mode_mean": "佢想表達咩？",
    "mode_mean_sub": "解釋潛台詞同語氣",
    "mode_kpop": "歌詞同影視語境",
    "mode_kpop_sub": "K-pop / 影視 / 網絡語境解析",
    "feature_translate": "翻譯",
    "feature_grammar": "文法",
    "feature_natural": "自然表達",
    "feature_vocab": "詞彙",
    "feature_tone": "語氣分析",
    "nav_history": "歷史",
    "nav_about": "關於",
    "what_can_v2": "你嘅跨文化聊天助手",
    "not_social": "呢個應用唔係社交平台。",
    "back_home": "返首頁",
    "input_text": "請輸入文字",
    "run": "運行",
    "source_language": "源語言",
    "language_of_text": "文本語言",
    "auto_detect": "自動偵測",
    "working": "處理中...",
    "voice_input": "語音輸入",
    "upload_audio": "上載音頻文件",
    "transcribe": "轉寫",
    "transcribing": "轉寫中...",
    "ok": "完成",
    "relation_mode": "關係 / 風格",
    "context_type": "語境類型",
    "history_title": "歷史記錄",
    "history_sub": "最近任務",
    "about_title": "關於",
    "about_desc": "TriLingua Bridge v2 — 跨文化溝通教練。",
    "mode_coach_v2": "AI 聊天教練",
    "mode_coach_sub_v2": "針對大陸 / 香港 / 韓國 / 澳洲 / 美國文化風格調整",
}}
