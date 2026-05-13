import json
from typing import Dict, Any, List, Tuple

import streamlit as st


# =========================
# Basic i18n scaffolding
# =========================

UI_LANGS = ["en", "zh", "ko", "yue"]

UI_LANG_DISPLAY = {
    "en": "English",
    "zh": "简体中文",
    "ko": "한국어",
    "yue": "繁體中文 / 粵語",
}

STUDY_LANG_CODES = ["zh", "yue", "ko", "en"]

LANG_DISPLAY_BY_UI = {
    "en": {
        "zh": "Mandarin Chinese",
        "yue": "Cantonese (粵語)",
        "ko": "Korean",
        "en": "English",
        "auto": "Auto-detect",
    },
    "zh": {
        "zh": "普通话",
        "yue": "粤语",
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


def get_lang_display() -> Dict[str, str]:
    ui_lang = st.session_state.get("ui_lang", "en")
    return LANG_DISPLAY_BY_UI.get(ui_lang, LANG_DISPLAY_BY_UI["en"])


def lang_label(code: str) -> str:
    return get_lang_display().get(code, code)


# =========================
# Text dictionary
# =========================

TEXTS = {
    "en": {
        "ui_language": "UI Language",
        "account_title": "Account",
        "account_note": "Your data is isolated by username.",
        "username": "Username",
        "login": "Login",
        "logout": "Logout",
        "prefs_title": "Preferences",
        "my_native": "My native language",
        "i_learn": "I am learning",
        "persona": "Persona",
        "creativity": "Creativity",
        "model": "Model",
        "show_pron": "Show pronunciation",
        "tip": "Tip: Keep inputs short and explicit for best results.",
        "nav_title": "Navigation",
        "nav_home": "Home",
        "mode_say": "Say",
        "mode_say_sub": "Express your idea naturally in the target language",
        "mode_mean": "Mean",
        "mode_mean_sub": "Understand what it really means in your native language",
        "mode_coach": "AI Chat Coach",
        "mode_coach_sub": "3 natural replies + tone & cultural notes",
        "mode_kpop": "Lyrics & Drama Context",
        "mode_kpop_sub": "Lyrics, drama dialogue, slang, and pop culture",
        "feature_translate": "Translate",
        "feature_grammar": "Grammar",
        "feature_natural": "Natural Expression",
        "feature_vocab": "Vocabulary",
        "feature_tone": "Tone Analysis",
        "feature_chat": "Chat",
        "feature_chat_sub": "Get a helpful reply in your target language",
        "nav_history": "History",
        "nav_about": "About",
        "app_title": "TriLingua Bridge v2",
        "subtitle": "AI Cross-cultural Communication Assistant",
        "not_social": "We never post to social networks.",
        "what_can": "Core features",
        "what_can_sub": "Communicate across cultures with confidence",
        "more_tools": "More tools",
        "more_tools_sub": "Extra help for expression and understanding",
        "back_home": "Back to Home",
        "working": "Working...",
        "ai_call_failed": "AI request failed",
        "history_save_failed": "Failed to save history",
        "db_init_failed": "Database init failed",
        "voice_input": "Voice Input",
        "language_of_text": "Language of the text",
        "upload_audio": "Upload audio (wav/mp3/m4a/webm)",
        "transcribe": "Transcribe",
        "transcribing": "Transcribing...",
        "ok": "OK",
        "stt_unavailable": "Speech-to-text unavailable",
        "input_text": "Enter text",
        "run": "Run",
        "source_language": "Source language",
        "auto_detect": "Auto-detect",
        "enter_text_warn": "Please enter some text.",
        "pronunciation_label": "Pronunciation",
        "playing_audio": "Generating audio...",
        "tts_not_supported": "TTS not supported for this language",
        "detected_source": "Detected source",
        "model_info_prefix": "Model",
        "tokens_label": "Tokens",
        "latency_label": "Latency",
        "your_message": "Your message",
        "msg_language": "Message language",
        "generate_reply": "Generate reply",
        "feature_grammar_sub": "Fix mistakes and learn quickly",
        "enter_text_correct": "Enter text to correct",
        "learner_level": "Learner level",
        "correct_btn": "Correct grammar",
        "feature_natural_sub": "Sound more natural",
        "enter_text_natural": "Enter text to improve",
        "desired_tone": "Desired tone",
        "suggest_btn": "Suggest",
        "feature_vocab_sub": "Understand key words and phrases",
        "enter_text_vocab": "Enter text",
        "max_items": "Max items",
        "explain_vocab_btn": "Explain vocabulary",
        "feature_tone_sub": "Analyze tone and intent",
        "enter_text_tone": "Enter text for tone analysis",
        "analyze_tone_btn": "Analyze tone",
        "history_title": "History",
        "history_sub": "Your recent AI interactions",
        "filter_mode": "Mode filter",
        "filter_source": "Source language filter",
        "filter_target": "Target language filter",
        "filter_persona": "Persona filter",
        "search_in": "Search in content",
        "show_last": "Show last N items",
        "history_load_failed": "Failed to load history",
        "no_history": "No history yet.",
        "input_label": "Input",
        "output_label": "AI Output",
        "about_title": "About",
        "about_desc": "TriLingua Bridge v2 — AI Cross-cultural Communication Assistant.",
        "translate_btn": "Translate",
        "enter_text_translate": "Enter text to translate",
        "pron_play": "Play pronunciation",
        "relation_mode": "Reply Style / Relationship Mode",
        "style_friend": "Friend",
        "style_crush": "Crush",
        "style_work": "Workplace",
        "style_formal": "Formal",
        "style_cute": "Cute",
        "style_cold": "Cold",
        "style_kpop": "K-pop Fan Style",
        "style_hk": "Hong Kong Style",
        "context_type": "Context type",
        "ctx_kpop": "K-pop lyrics",
        "ctx_kdrama": "Korean drama dialogue",
        "ctx_cdrama": "Chinese drama dialogue",
        "ctx_cantodrama": "Cantonese drama dialogue",
        "ctx_eng_tv": "English TV/movie dialogue",
        "ctx_inet": "Internet slang",
        "ctx_pop": "Pop culture expressions",
    },

    "zh": {
        "ui_language": "界面语言",
        "account_title": "账号",
        "account_note": "不同用户名数据相互隔离。",
        "username": "用户名",
        "login": "登录",
        "logout": "登出",
        "prefs_title": "偏好设置",
        "my_native": "母语",
        "i_learn": "学习语言",
        "persona": "人设",
        "creativity": "创造性",
        "model": "模型",
        "show_pron": "显示发音",
        "tip": "提示：输入简洁明确，效果更好。",
        "nav_title": "导航",
        "nav_home": "首页",
        "mode_say": "表达",
        "mode_say_sub": "用目标语言自然表达想法",
        "mode_mean": "理解",
        "mode_mean_sub": "用母语更好理解对方含义",
        "mode_coach": "AI 对话教练",
        "mode_coach_sub": "3 个自然回复 + 语气 & 文化说明",
        "mode_kpop": "歌词与影视语境",
        "mode_kpop_sub": "歌词、影视台词、网络语和流行文化表达",
        "feature_translate": "翻译",
        "feature_grammar": "语法",
        "feature_natural": "自然表达",
        "feature_vocab": "词汇",
        "feature_tone": "语气分析",
        "feature_chat": "聊天",
        "feature_chat_sub": "用目标语言获得友好回复",
        "nav_history": "历史",
        "nav_about": "关于",
        "app_title": "TriLingua Bridge v2",
        "subtitle": "AI 跨文化沟通助理",
        "not_social": "我们不会在社交网络发布任何内容。",
        "what_can": "核心功能",
        "what_can_sub": "跨文化表达更自信",
        "more_tools": "更多工具",
        "more_tools_sub": "表达与理解的加速器",
        "back_home": "返回首页",
        "working": "处理中...",
        "ai_call_failed": "AI 调用失败",
        "history_save_failed": "历史保存失败",
        "db_init_failed": "数据库初始化失败",
        "voice_input": "语音输入",
        "language_of_text": "文本语言",
        "upload_audio": "上传音频（wav/mp3/m4a/webm）",
        "transcribe": "转写",
        "transcribing": "转写中...",
        "ok": "完成",
        "stt_unavailable": "语音识别暂不可用",
        "input_text": "输入文本",
        "run": "运行",
        "source_language": "源语言",
        "auto_detect": "自动检测",
        "enter_text_warn": "请输入一些文本。",
        "pronunciation_label": "发音",
        "playing_audio": "生成音频中...",
        "tts_not_supported": "暂不支持该语言的 TTS",
        "detected_source": "检测语言",
        "model_info_prefix": "模型",
        "tokens_label": "Tokens",
        "latency_label": "延迟",
        "your_message": "你的消息",
        "msg_language": "消息语言",
        "generate_reply": "生成回复",
        "feature_grammar_sub": "修正错误并快速学习",
        "enter_text_correct": "输入需要纠正的文本",
        "learner_level": "学习者等级",
        "correct_btn": "纠正语法",
        "feature_natural_sub": "表达更自然",
        "enter_text_natural": "输入需要润色的文本",
        "desired_tone": "期望语气",
        "suggest_btn": "给出建议",
        "feature_vocab_sub": "理解关键词语",
        "enter_text_vocab": "输入文本",
        "max_items": "最多条目",
        "explain_vocab_btn": "解释词汇",
        "feature_tone_sub": "分析语气与意图",
        "enter_text_tone": "输入要分析的文本",
        "analyze_tone_btn": "分析语气",
        "history_title": "历史记录",
        "history_sub": "最近的 AI 交互",
        "filter_mode": "按模式筛选",
        "filter_source": "按源语言筛选",
        "filter_target": "按目标语言筛选",
        "filter_persona": "按人设筛选",
        "search_in": "搜索内容",
        "show_last": "显示最近 N 条",
        "history_load_failed": "历史加载失败",
        "no_history": "暂无历史记录。",
        "input_label": "输入",
        "output_label": "AI 输出",
        "about_title": "关于",
        "about_desc": "TriLingua Bridge v2 — AI 跨文化沟通助理。",
        "translate_btn": "翻译",
        "enter_text_translate": "输入待翻译内容",
        "pron_play": "播放发音",
        "relation_mode": "关系/风格",
        "style_friend": "朋友",
        "style_crush": "心动对象",
        "style_work": "职场",
        "style_formal": "正式",
        "style_cute": "可爱",
        "style_cold": "冷淡",
        "style_kpop": "K-pop 饭圈风",
        "style_hk": "港风",
        "context_type": "语境类型",
        "ctx_kpop": "K-pop 歌词",
        "ctx_kdrama": "韩剧台词",
        "ctx_cdrama": "国剧台词",
        "ctx_cantodrama": "港剧台词",
        "ctx_eng_tv": "英文影视台词",
        "ctx_inet": "网络流行语",
        "ctx_pop": "流行文化表达",
    },

    "ko": {
        "ui_language": "인터페이스 언어",
        "account_title": "계정",
        "account_note": "사용자명별로 데이터가 분리됩니다.",
        "username": "사용자명",
        "login": "로그인",
        "logout": "로그아웃",
        "prefs_title": "설정",
        "my_native": "모국어",
        "i_learn": "학습 언어",
        "persona": "페르소나",
        "creativity": "창의성",
        "model": "모델",
        "show_pron": "발음 표시",
        "tip": "팁: 짧고 명확하게 입력하면 더 좋은 결과를 얻을 수 있습니다.",
        "nav_title": "내비게이션",
        "nav_home": "홈",
        "mode_say": "표현하기",
        "mode_say_sub": "하고 싶은 말을 목표 언어로 자연스럽게 표현",
        "mode_mean": "의미 이해",
        "mode_mean_sub": "상대의 메시지를 모국어로 더 잘 이해",
        "mode_coach": "AI 대화 코치",
        "mode_coach_sub": "자연스러운 답장 3개 + 말투 & 문화 설명",
        "mode_kpop": "가사와 드라마 맥락",
        "mode_kpop_sub": "가사, 드라마 대사, 인터넷 표현, 대중문화 표현",
        "feature_translate": "번역",
        "feature_grammar": "문법",
        "feature_natural": "자연스러운 표현",
        "feature_vocab": "어휘",
        "feature_tone": "말투 분석",
        "feature_chat": "채팅",
        "feature_chat_sub": "목표 언어로 적절한 답장 받기",
        "nav_history": "기록",
        "nav_about": "소개",
        "app_title": "TriLingua Bridge v2",
        "subtitle": "AI 다문화 커뮤니케이션 도우미",
        "not_social": "이 앱은 소셜 네트워크에 어떤 내용도 게시하지 않습니다.",
        "what_can": "핵심 기능",
        "what_can_sub": "문화 간 소통을 더 자신 있게",
        "more_tools": "추가 도구",
        "more_tools_sub": "표현과 이해를 돕는 보조 기능",
        "back_home": "홈으로 돌아가기",
        "working": "처리 중...",
        "ai_call_failed": "AI 호출 실패",
        "history_save_failed": "기록 저장 실패",
        "db_init_failed": "데이터베이스 초기화 실패",
        "voice_input": "음성 입력",
        "language_of_text": "텍스트 언어",
        "upload_audio": "오디오 업로드（wav/mp3/m4a/webm）",
        "transcribe": "전사",
        "transcribing": "전사 중...",
        "ok": "완료",
        "stt_unavailable": "음성 인식을 사용할 수 없습니다",
        "input_text": "텍스트 입력",
        "run": "실행",
        "source_language": "원문 언어",
        "auto_detect": "자동 감지",
        "enter_text_warn": "텍스트를 입력하세요.",
        "pronunciation_label": "발음",
        "playing_audio": "오디오 생성 중...",
        "tts_not_supported": "이 언어는 TTS를 지원하지 않습니다",
        "detected_source": "감지된 언어",
        "model_info_prefix": "모델",
        "tokens_label": "토큰",
        "latency_label": "지연",
        "your_message": "메시지",
        "msg_language": "메시지 언어",
        "generate_reply": "답장 생성",
        "feature_grammar_sub": "오류를 고치고 빠르게 학습",
        "enter_text_correct": "교정할 텍스트 입력",
        "learner_level": "학습자 수준",
        "correct_btn": "문법 교정",
        "feature_natural_sub": "더 자연스럽게 표현하기",
        "enter_text_natural": "다듬을 텍스트 입력",
        "desired_tone": "원하는 말투",
        "suggest_btn": "제안 받기",
        "feature_vocab_sub": "핵심 단어와 표현 이해",
        "enter_text_vocab": "텍스트 입력",
        "max_items": "최대 항목 수",
        "explain_vocab_btn": "어휘 설명",
        "feature_tone_sub": "말투와 의도 분석",
        "enter_text_tone": "분석할 텍스트 입력",
        "analyze_tone_btn": "말투 분석",
        "history_title": "기록",
        "history_sub": "최근 AI 상호작용",
        "filter_mode": "모드 필터",
        "filter_source": "원문 언어 필터",
        "filter_target": "목표 언어 필터",
        "filter_persona": "페르소나 필터",
        "search_in": "내용 검색",
        "show_last": "최근 N개 표시",
        "history_load_failed": "기록 불러오기 실패",
        "no_history": "아직 기록이 없습니다.",
        "input_label": "입력",
        "output_label": "AI 출력",
        "about_title": "소개",
        "about_desc": "TriLingua Bridge v2 — AI 다문화 커뮤니케이션 도우미.",
        "translate_btn": "번역",
        "enter_text_translate": "번역할 내용 입력",
        "pron_play": "발음 재생",
        "relation_mode": "관계 / 답장 스타일",
        "style_friend": "친구",
        "style_crush": "호감 있는 사람",
        "style_work": "직장",
        "style_formal": "격식",
        "style_cute": "귀여운 말투",
        "style_cold": "차가운 말투",
        "style_kpop": "K-pop 팬 스타일",
        "style_hk": "홍콩 스타일",
        "context_type": "맥락 유형",
        "ctx_kpop": "K-pop 가사",
        "ctx_kdrama": "한국 드라마 대사",
        "ctx_cdrama": "중국 드라마 대사",
        "ctx_cantodrama": "광둥어 드라마 대사",
        "ctx_eng_tv": "영어 영화/드라마 대사",
        "ctx_inet": "인터넷 유행어",
        "ctx_pop": "대중문화 표현",
    },

    "yue": {
        "ui_language": "介面語言",
        "account_title": "帳號",
        "account_note": "唔同用戶名嘅資料會分開儲存。",
        "username": "用戶名",
        "login": "登入",
        "logout": "登出",
        "prefs_title": "偏好設定",
        "my_native": "我嘅母語",
        "i_learn": "我想學",
        "persona": "人設",
        "creativity": "創意度",
        "model": "模型",
        "show_pron": "顯示發音",
        "tip": "提示：輸入簡短清楚，效果會更好。",
        "nav_title": "導航",
        "nav_home": "首頁",
        "mode_say": "點樣講",
        "mode_say_sub": "用目標語言自然表達你想講嘅嘢",
        "mode_mean": "咩意思",
        "mode_mean_sub": "用母語理解對方真正意思",
        "mode_coach": "AI 對話教練",
        "mode_coach_sub": "3 個自然回覆 + 語氣同文化提示",
        "mode_kpop": "歌詞同影視語境",
        "mode_kpop_sub": "歌詞、影視對白、網絡用語同流行文化表達",
        "feature_translate": "翻譯",
        "feature_grammar": "文法",
        "feature_natural": "自然表達",
        "feature_vocab": "詞彙",
        "feature_tone": "語氣分析",
        "feature_chat": "聊天",
        "feature_chat_sub": "用目標語言生成合適回覆",
        "nav_history": "歷史",
        "nav_about": "關於",
        "app_title": "TriLingua Bridge v2",
        "subtitle": "AI 跨文化溝通助手",
        "not_social": "我哋唔會喺社交平台發佈任何內容。",
        "what_can": "核心功能",
        "what_can_sub": "跨文化溝通更加有信心",
        "more_tools": "更多工具",
        "more_tools_sub": "幫你更好表達同理解",
        "back_home": "返首頁",
        "working": "處理中...",
        "ai_call_failed": "AI 調用失敗",
        "history_save_failed": "歷史保存失敗",
        "db_init_failed": "資料庫初始化失敗",
        "voice_input": "語音輸入",
        "language_of_text": "文本語言",
        "upload_audio": "上載音頻（wav/mp3/m4a/webm）",
        "transcribe": "轉寫",
        "transcribing": "轉寫中...",
        "ok": "完成",
        "stt_unavailable": "語音識別暫時不可用",
        "input_text": "輸入文本",
        "run": "運行",
        "source_language": "源語言",
        "auto_detect": "自動偵測",
        "enter_text_warn": "請輸入文字。",
        "pronunciation_label": "發音",
        "playing_audio": "生成音頻中...",
        "tts_not_supported": "暫時唔支援呢種語言嘅 TTS",
        "detected_source": "偵測到嘅語言",
        "model_info_prefix": "模型",
        "tokens_label": "Tokens",
        "latency_label": "延遲",
        "your_message": "你嘅訊息",
        "msg_language": "訊息語言",
        "generate_reply": "生成回覆",
        "feature_grammar_sub": "修正文法錯誤並快速學習",
        "enter_text_correct": "輸入需要修正嘅文本",
        "learner_level": "學習程度",
        "correct_btn": "修正文法",
        "feature_natural_sub": "表達更加自然",
        "enter_text_natural": "輸入需要潤色嘅文本",
        "desired_tone": "想要嘅語氣",
        "suggest_btn": "生成建議",
        "feature_vocab_sub": "理解關鍵詞同短語",
        "enter_text_vocab": "輸入文本",
        "max_items": "最多項目",
        "explain_vocab_btn": "解釋詞彙",
        "feature_tone_sub": "分析語氣同意圖",
        "enter_text_tone": "輸入要分析嘅文本",
        "analyze_tone_btn": "分析語氣",
        "history_title": "歷史記錄",
        "history_sub": "最近嘅 AI 互動",
        "filter_mode": "按模式篩選",
        "filter_source": "按源語言篩選",
        "filter_target": "按目標語言篩選",
        "filter_persona": "按人設篩選",
        "search_in": "搜尋內容",
        "show_last": "顯示最近 N 條",
        "history_load_failed": "歷史載入失敗",
        "no_history": "暫時未有歷史記錄。",
        "input_label": "輸入",
        "output_label": "AI 輸出",
        "about_title": "關於",
        "about_desc": "TriLingua Bridge v2 — AI 跨文化溝通助手。",
        "translate_btn": "翻譯",
        "enter_text_translate": "輸入要翻譯嘅內容",
        "pron_play": "播放發音",
        "relation_mode": "關係 / 回覆風格",
        "style_friend": "朋友",
        "style_crush": "心動對象",
        "style_work": "職場",
        "style_formal": "正式",
        "style_cute": "可愛",
        "style_cold": "冷淡",
        "style_kpop": "K-pop 飯圈風",
        "style_hk": "港風",
        "context_type": "語境類型",
        "ctx_kpop": "K-pop 歌詞",
        "ctx_kdrama": "韓劇對白",
        "ctx_cdrama": "國劇對白",
        "ctx_cantodrama": "港劇對白",
        "ctx_eng_tv": "英文影視對白",
        "ctx_inet": "網絡流行語",
        "ctx_pop": "流行文化表達",
    },
}


def t(key: str, default: str = None) -> str:
    ui = st.session_state.get("ui_lang", "en")
    return TEXTS.get(ui, {}).get(key, default or key)


# =========================
# Personas and levels / tones
# =========================

PERSONA_CODES = ["friendly", "direct", "teacher", "cheerful", "professional"]


def persona_display(code: str) -> str:
    ui_lang = st.session_state.get("ui_lang", "en")

    display = {
        "en": {
            "friendly": "Friendly",
            "direct": "Direct",
            "teacher": "Teacher",
            "cheerful": "Cheerful",
            "professional": "Professional",
        },
        "zh": {
            "friendly": "友好",
            "direct": "直接",
            "teacher": "老师",
            "cheerful": "开朗",
            "professional": "专业",
        },
        "ko": {
            "friendly": "친근함",
            "direct": "직설적",
            "teacher": "선생님",
            "cheerful": "밝은 스타일",
            "professional": "전문적",
        },
        "yue": {
            "friendly": "友善",
            "direct": "直接",
            "teacher": "老師",
            "cheerful": "開朗",
            "professional": "專業",
        },
    }

    return display.get(ui_lang, display["en"]).get(code, code)


def local_levels() -> Tuple[List[str], Dict[str, str]]:
    ui_lang = st.session_state.get("ui_lang", "en")

    options = {
        "en": ["Beginner", "Intermediate", "Advanced"],
        "zh": ["入门", "中级", "高级"],
        "ko": ["초급", "중급", "고급"],
        "yue": ["初學", "中級", "高級"],
    }.get(ui_lang, ["Beginner", "Intermediate", "Advanced"])

    values = ["A1-A2", "B1-B2", "C1-C2"]

    return options, dict(zip(options, values))


def local_tones() -> Tuple[List[str], Dict[str, str]]:
    ui_lang = st.session_state.get("ui_lang", "en")

    options = {
        "en": ["Neutral", "Polite", "Casual", "Warm", "Serious"],
        "zh": ["中性", "礼貌", "随意", "温暖", "认真"],
        "ko": ["중립", "공손", "캐주얼", "따뜻함", "진지함"],
        "yue": ["中性", "禮貌", "隨意", "溫暖", "認真"],
    }.get(ui_lang, ["Neutral", "Polite", "Casual", "Warm", "Serious"])

    values = ["neutral", "polite", "casual", "warm", "serious"]

    return options, dict(zip(options, values))


def build_persona_profile(
    code: str,
    source_lang: str,
    target_lang: str,
    ui_lang: str,
) -> Dict[str, Any]:
    profiles = {
        "friendly": "Be kind, supportive, and encouraging.",
        "direct": "Be concise, clear, and straightforward.",
        "teacher": "Be explanatory, step-by-step, with examples.",
        "cheerful": "Be upbeat and positive.",
        "professional": "Be formal and precise.",
    }

    return {
        "code": code,
        "style": profiles.get(code, ""),
        "style_hint": profiles.get(code, ""),
        "source_lang": source_lang,
        "target_lang": target_lang,
        "ui_lang": ui_lang,
    }


# =========================
# CSS and UI components
# =========================

def inject_css():
    st.markdown(
        """
        <style>
        :root {
            --card-bg: #ffffff;
            --soft: #f6f7f9;
            --border: #e6e8eb;
            --accent: #3b82f6;
            --muted: #6b7280;
        }

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
            padding: 20px 18px 22px;
            border: 1px solid var(--border);
            border-radius: 18px;
            background: linear-gradient(135deg, #e7f3ff 0%, #f9f5ff 100%);
            box-shadow: 0 6px 22px rgba(16, 24, 40, 0.06);
            margin-bottom: 18px;
        }

        .hero h1 {
            margin: 0;
            font-size: 2.0rem;
        }

        .hero p {
            color: var(--muted);
            margin-top: .25rem;
            font-size: 1.05rem;
        }

        .section-title {
            font-weight: 700;
            margin: 24px 0 4px;
            font-size: 1.1rem;
        }

        .section-subtle {
            color: var(--muted);
            margin-bottom: 12px;
        }

        .input-wrap {
            background: #f9fafb;
            border: 1px dashed #d1d5db;
            border-radius: 16px;
            padding: 10px 12px;
            margin-bottom: 10px;
        }

        .input-wrap textarea {
            font-size: 0.98rem !important;
        }

        .output-wrap {
            margin: 10px 0 18px;
        }

        .output-card {
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 14px;
            background: var(--card-bg);
            box-shadow: 0 4px 18px rgba(16, 24, 40, 0.04);
            margin-bottom: 14px;
        }

        .sb-title {
            font-weight: 700;
            margin-top: 10px;
        }

        .sb-sub {
            color: var(--muted);
            font-size: .85rem;
            margin-bottom: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, note: str = ""):
    st.markdown('<div class="hero">', unsafe_allow_html=True)
    st.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p>{subtitle}</p>", unsafe_allow_html=True)

    if note:
        st.caption(note)

    st.markdown("</div>", unsafe_allow_html=True)


def section_header(title: str, subtitle: str = "", accent: str = "blue"):
    st.markdown(
        f'<div class="section-title">{title}</div>',
        unsafe_allow_html=True,
    )

    if subtitle:
        st.markdown(
            f'<div class="section-subtle">{subtitle}</div>',
            unsafe_allow_html=True,
        )


def feature_card(title: str, subtitle: str, icon: str, key: str) -> bool:
    return st.button(
        f"{icon} {title}\n\n{subtitle}",
        use_container_width=True,
        key=key,
    )


# =========================
# Render helpers
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


def render_structured_response(obj: Dict[str, Any]):
    st.markdown('<div class="output-card">', unsafe_allow_html=True)

    if "reply_options" in obj:
        st.markdown("### Reply Options")
        for i, option in enumerate(obj.get("reply_options", []), 1):
            if isinstance(option, dict):
                text = option.get("text", "")
                score = option.get("naturalness_score", "")
                tone = option.get("tone", "")
                st.markdown(f"**{i}. {text}**")
                st.caption(f"Score: {score} • Style: {tone}")
            else:
                st.markdown(f"**{i}. {option}**")

    sections = [
        ("tone_notes", "Tone Notes"),
        ("cultural_notes", "Cultural Notes"),
        ("suggested_best_reply", "Suggested Best Reply"),
        ("reason", "Why this works"),
        ("clean_translation", "Clean Translation"),
        ("summary", "Summary"),
        ("recommended_understanding", "What it really means"),
    ]

    for key, title in sections:
        if obj.get(key):
            st.markdown(f"### {title}")
            st.write(obj[key])

    if obj.get("key_phrases"):
        st.markdown("### Key Phrases")
        for item in obj["key_phrases"]:
            if isinstance(item, dict):
                st.markdown(
                    f"- **{item.get('phrase', '')}**: {item.get('meaning', '')}"
                )
                if item.get("note"):
                    st.caption(item["note"])
            else:
                st.markdown(f"- {item}")

    if obj.get("slang_pop_culture"):
        st.markdown("### Slang / Pop Culture")
        for item in obj["slang_pop_culture"]:
            if isinstance(item, dict):
                st.markdown(f"- **{item.get('term', '')}** ({item.get('origin', '')})")
                if item.get("note"):
                    st.caption(item["note"])
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
        }

        if set(result.keys()) & structured_keys:
            render_structured_response(result)
            return

        st.markdown('<div class="output-card">', unsafe_allow_html=True)
        st.json(result)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if isinstance(result, list):
        st.markdown('<div class="output-card">', unsafe_allow_html=True)
        st.json(result)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.markdown('<div class="output-card">', unsafe_allow_html=True)
    st.markdown(str(result))
    st.markdown("</div>", unsafe_allow_html=True)


def normalize_usage(usage: Dict[str, Any]) -> Dict[str, Any]:
    if not usage:
        return {}

    return {
        "model": usage.get("model"),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }


def show_model_caption(usage: Dict[str, Any], latency_ms: int):
    usage_data = normalize_usage(usage)

    model = usage_data.get("model") or "-"
    prompt_tokens = usage_data.get("prompt_tokens")
    completion_tokens = usage_data.get("completion_tokens")

    prompt_tokens = prompt_tokens if prompt_tokens is not None else "-"
    completion_tokens = completion_tokens if completion_tokens is not None else "-"

    st.caption(
        f"{t('model_info_prefix')}: {model} • "
        f"{t('tokens_label')}: {prompt_tokens}/{completion_tokens} • "
        f"{t('latency_label')}: {latency_ms} ms"
    )
