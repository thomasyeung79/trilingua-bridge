import html
import json
from typing import Dict, Any, List, Tuple

import streamlit as st


UI_LANGS = ["en", "zh", "ko", "yue", "ja"]

UI_LANG_DISPLAY = {
    "en": "English",
    "zh": "简体中文",
    "ko": "한국어",
    "yue": "繁體中文 / 粵語",
    "ja": "日本語",
}

STUDY_LANG_CODES = ["zh", "yue", "ko", "en", "ja"]

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
        "ja": "Japanese",
        "en": "English",
        "auto": "Auto-detect",
    },
    "zh": {
        "zh": "简体中文（普通话）",
        "yue": "繁體中文（粵語）",
        "ko": "韩语",
        "ja": "日语",
        "en": "英语",
        "auto": "自动检测",
    },
    "ko": {
        "zh": "중국어 간체 / 보통화",
        "yue": "광둥어 / 번체 중국어",
        "ko": "한국어",
        "ja": "일본어",
        "en": "영어",
        "auto": "자동 감지",
    },
    "yue": {
        "zh": "普通話 / 簡體中文",
        "yue": "粵語 / 繁體中文",
        "ko": "韓文",
        "ja": "日文",
        "en": "英文",
        "auto": "自動偵測",
    },
    "ja": {
        "zh": "簡体字中国語（標準中国語）",
        "yue": "繁体字中国語（広東語）",
        "ko": "韓国語",
        "ja": "日本語",
        "en": "英語",
        "auto": "自動検出",
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
            "ja": "ニュートラル",
        },
        "friendly": {
            "en": "Friendly",
            "zh": "友好",
            "ko": "친근함",
            "yue": "友善",
            "ja": "フレンドリー",
        },
        "teacher": {
            "en": "Teacher",
            "zh": "老师风格",
            "ko": "선생님 스타일",
            "yue": "老師風格",
            "ja": "先生スタイル",
        },
        "strict": {
            "en": "Strict",
            "zh": "严格",
            "ko": "엄격함",
            "yue": "嚴格",
            "ja": "厳格",
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
    elif lang == "ja":
        labels = ["A1 初級", "A2 初中級", "B1 中級", "B2 中上級", "C1 上級", "C2 母語レベル"]
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
        "ja": [
            ("neutral", "ニュートラル"),
            ("friendly", "フレンドリー"),
            ("polite", "丁寧"),
            ("cute", "可愛い"),
            ("formal", "フォーマル"),
            ("casual", "カジュアル"),
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
            --bg: #f5f7fb;
            --panel: #ffffff;
            --panel-soft: #f9fbfd;
            --text: #111827;
            --muted: #6b7280;
            --line: #e5e7eb;
            --line-strong: #d1d5db;
            --accent: #2563eb;
            --accent-2: #0f766e;
            --accent-3: #b45309;
            --accent-soft: #eef5ff;
            --mint-soft: #ecfdf5;
            --amber-soft: #fffbeb;
            --shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
            --shadow-soft: 0 8px 22px rgba(15, 23, 42, 0.05);
            --brand: #2563eb;
            --brand-dark: #1d4ed8;
        }

        html, body, [data-testid="stAppViewContainer"] {
            background: var(--bg) !important;
            color: var(--text);
        }

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 12% 0%, rgba(37, 99, 235, 0.08), transparent 28rem),
                radial-gradient(circle at 88% 8%, rgba(15, 118, 110, 0.07), transparent 26rem),
                linear-gradient(180deg, #f8fafc 0%, #f3f6fb 100%) !important;
        }

        [data-testid="stHeader"],
        #MainMenu,
        footer {
            display: none !important;
        }

        .block-container {
            max-width: 1360px;
            padding-top: 1.75rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3, p {
            letter-spacing: 0;
        }

        /* ── Brand header bar ── */
        .brand-topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.6rem 1.25rem;
            margin-bottom: 1.5rem;
            background: rgba(255, 255, 255, 0.85);
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 8px;
            backdrop-filter: blur(8px);
        }
        .brand-topbar-left {
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 800;
            color: #0f172a;
            font-size: 1.05rem;
        }
        .brand-topbar-logo {
            width: 32px;
            height: 32px;
            border-radius: 6px;
            background: linear-gradient(135deg, #0f172a, #2563eb);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
            font-size: 0.85rem;
        }
        .brand-topbar-right {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .badge-pill {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 10px;
            border-radius: 999px;
            background: rgba(37, 99, 235, 0.1);
            color: var(--brand);
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            border: 1px solid rgba(37, 99, 235, 0.18);
        }

        /* ── Primary CTA button ── */
        div[data-testid="stButton"] > button[kind="primary"],
        .btn-primary {
            background: var(--brand) !important;
            color: #ffffff !important;
            border: 1px solid var(--brand) !important;
            font-weight: 700;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background: var(--brand-dark) !important;
            border-color: var(--brand-dark) !important;
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.25);
        }

        /* ── Secondary CTA button ── */
        .btn-secondary {
            background: #ffffff !important;
            color: var(--brand) !important;
            border: 1px solid var(--brand) !important;
            font-weight: 700;
        }
        .btn-secondary:hover {
            background: var(--accent-soft) !important;
        }

        /* ── Default buttons ── */
        div[data-testid="stButton"] > button {
            border-radius: 8px;
            border: 1px solid var(--line-strong);
            background: #ffffff;
            color: var(--text);
            font-weight: 650;
            min-height: 44px;
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
            border-color: #e2e8f0 !important;
            background: #f8fafc !important;
        }

        div[data-testid="stSelectbox"] > div,
        div[data-testid="stSlider"],
        [data-testid="stExpander"] {
            border-radius: 8px !important;
        }

        .hero-box {
            position: relative;
            overflow: hidden;
            padding: 28px 30px;
            border: 1px solid rgba(148, 163, 184, 0.28);
            border-radius: 8px;
            background:
                linear-gradient(135deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.92));
            box-shadow: var(--shadow);
            margin-bottom: 20px;
        }

        .hero-box::after {
            content: "";
            position: absolute;
            right: 0;
            top: 0;
            width: 34%;
            height: 100%;
            background:
                linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(15, 118, 110, 0.07));
            border-left: 1px solid rgba(148, 163, 184, 0.16);
            pointer-events: none;
        }
        
        .hero-kicker {
            position: relative;
            z-index: 1;
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
        }

        .hero-logo {
            width: 44px;
            height: 44px;
            flex: 0 0 44px;
            border-radius: 8px;
            background: linear-gradient(135deg, #0f172a, #1e3a8a);
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
            position: relative;
            z-index: 1;
            font-size: 2.45rem;
            line-height: 1.12;
            font-weight: 850;
            margin-bottom: 0.35rem;
            color: var(--text);
        }

        .hero-sub {
            position: relative;
            z-index: 1;
            color: var(--muted);
            margin-bottom: 0.35rem;
            font-size: 1.02rem;
            line-height: 1.55;
            max-width: 680px;
        }

        .hero-pills {
            position: relative;
            z-index: 1;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 18px;
        }

        .hero-pill {
            border: 1px solid rgba(148, 163, 184, 0.35);
            background: rgba(255, 255, 255, 0.74);
            color: #334155;
            border-radius: 999px;
            padding: 6px 10px;
            font-size: 0.78rem;
            font-weight: 720;
        }

        .settings-card,
        .output-wrap,
        .output-card {
            border: 1px solid rgba(148, 163, 184, 0.28);
            border-radius: 8px;
            padding: 16px;
            margin: 12px 0;
            background: rgba(255, 255, 255, 0.9);
            box-shadow: var(--shadow-soft);
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
            margin-top: 26px;
            margin-bottom: 4px;
            color: var(--text);
        }

        .section-sub {
            margin-bottom: 14px;
            line-height: 1.5;
        }

        .feature-card {
            border: 1px solid rgba(148, 163, 184, 0.28);
            border-radius: 8px;
            padding: 18px 15px;
            min-height: 128px;
            text-align: left;
            background: rgba(255, 255, 255, 0.92);
            margin-bottom: 8px;
            box-shadow: var(--shadow-soft);
            transition: border-color 0.12s ease, box-shadow 0.12s ease, transform 0.12s ease;
        }

        .feature-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 18px 36px rgba(15, 23, 42, 0.1);
            border-color: var(--accent);
        }

        .feature-card-icon {
            width: 34px;
            height: 34px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            background: linear-gradient(135deg, var(--accent-soft), var(--mint-soft));
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
            border-color: rgba(148, 163, 184, 0.28);
            background: rgba(255, 255, 255, 0.9);
        }

        .stAlert {
            border-radius: 8px;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: rgba(148, 163, 184, 0.28) !important;
            background: rgba(255, 255, 255, 0.82) !important;
            box-shadow: var(--shadow-soft);
        }

        /* ══════════════════════════════════════════════
           Landing page — feature preview cards
           ══════════════════════════════════════════════ */
        .landing-section-label {
            color: var(--brand);
            font-size: 0.72rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 4px;
        }
        .landing-section-title {
            font-size: 1.55rem;
            font-weight: 850;
            color: var(--text);
            margin-bottom: 6px;
            line-height: 1.2;
        }
        .landing-section-sub {
            color: var(--muted);
            font-size: 0.95rem;
            margin-bottom: 20px;
            line-height: 1.5;
            max-width: 600px;
        }

        .landing-feature-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
            margin: 16px 0 10px;
        }
        .landing-feature-card {
            border: 1px solid rgba(148, 163, 184, 0.28);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.92);
            padding: 18px 16px;
            min-height: 140px;
            box-shadow: 0 7px 18px rgba(15, 23, 42, 0.045);
            transition: transform 0.12s ease, box-shadow 0.12s ease, border-color 0.12s ease;
        }
        .landing-feature-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
            border-color: rgba(37, 99, 235, 0.35);
        }
        .landing-feature-icon {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 12px;
            font-size: 1.2rem;
        }
        .landing-feature-card h3 {
            font-size: 0.95rem;
            font-weight: 800;
            margin: 0 0 6px;
            color: var(--text);
        }
        .landing-feature-card p {
            font-size: 0.84rem;
            color: var(--muted);
            line-height: 1.45;
            margin: 0;
        }
        .icon-gradient-blue {
            background: linear-gradient(135deg, #eef5ff, #dbeafe);
        }
        .icon-gradient-teal {
            background: linear-gradient(135deg, #ecfdf5, #d1fae5);
        }
        .icon-gradient-amber {
            background: linear-gradient(135deg, #fffbeb, #fef3c7);
        }
        .icon-gradient-rose {
            background: linear-gradient(135deg, #fef2f2, #fce7f3);
        }

        /* ══════════════════════════════════════════════
           Landing page — value proposition + CTA
           ══════════════════════════════════════════════ */
        .landing-value {
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 8px;
            background: linear-gradient(135deg, rgba(255,255,255,0.96), rgba(248,250,252,0.9));
            padding: 22px 24px;
            margin: 12px 0 16px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
        }
        .landing-value p {
            font-size: 1rem;
            line-height: 1.6;
            color: #334155;
            margin: 0 0 4px;
        }
        .landing-cta-row {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 18px 0 4px;
        }

        /* ══════════════════════════════════════════════
           Landing page — workspace preview (static)
           ══════════════════════════════════════════════ */
        .preview-section {
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.88);
            padding: 20px;
            margin: 16px 0;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
        }
        .preview-label {
            color: var(--muted);
            font-size: 0.76rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 12px;
        }
        .preview-bubble {
            border-radius: 12px;
            padding: 12px 16px;
            margin-bottom: 10px;
            max-width: 80%;
            font-size: 0.92rem;
            line-height: 1.5;
        }
        .preview-bubble-user {
            background: var(--accent-soft);
            border: 1px solid rgba(37, 99, 235, 0.15);
            color: var(--text);
            margin-left: auto;
        }
        .preview-bubble-ai {
            background: #ffffff;
            border: 1px solid rgba(148, 163, 184, 0.25);
            color: var(--text);
            margin-right: auto;
        }
        .preview-output-item {
            padding: 8px 0;
            border-bottom: 1px solid rgba(148, 163, 184, 0.15);
        }
        .preview-output-item:last-child {
            border-bottom: none;
        }
        .preview-output-label {
            color: var(--muted);
            font-size: 0.76rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 4px;
        }
        .preview-output-value {
            font-size: 0.92rem;
            color: var(--text);
            line-height: 1.5;
        }
        .preview-output-value em {
            color: var(--muted);
            font-size: 0.86rem;
        }

        /* ══════════════════════════════════════════════
           Responsive breakpoints
           ══════════════════════════════════════════════ */

        /* Tablet: max-width 1024px */
        @media (max-width: 1024px) {
            .landing-feature-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .hero-title {
                font-size: 2rem;
            }
            .brand-topbar {
                flex-wrap: wrap;
                gap: 6px;
            }
        }

        /* Mobile: max-width 768px */
        @media (max-width: 768px) {
            .block-container {
                padding-top: 1rem;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
            .hero-box {
                padding: 20px 16px;
            }
            .hero-title {
                font-size: 1.6rem;
            }
            .hero-sub {
                font-size: 0.92rem;
            }
            .landing-feature-grid {
                grid-template-columns: 1fr;
            }
            .landing-section-title {
                font-size: 1.25rem;
            }
            .landing-cta-row {
                flex-direction: column;
            }
            .landing-cta-row div[data-testid="stButton"] > button {
                width: 100%;
            }
            .preview-bubble {
                max-width: 100%;
            }
            .brand-topbar {
                flex-direction: column;
                align-items: flex-start;
                gap: 8px;
            }
            .brand-topbar-right {
                width: 100%;
                justify-content: flex-start;
            }
            .landing-value {
                padding: 16px;
            }
            .preview-section {
                padding: 14px;
            }
        }

        /* Small mobile: max-width 480px */
        @media (max-width: 480px) {
            .hero-title {
                font-size: 1.35rem;
            }
            .landing-feature-card {
                min-height: auto;
                padding: 14px 12px;
            }
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
        f'<div class="hero-kicker-text">{html.escape(t("hero_langs"))}</div>'
        f'{note_html}'
        '</div>'
        '</div>'
        f'<div class="hero-title">{title}</div>'
        f'{sub_html}'
        '<div class="hero-pills">'
        f'<div class="hero-pill">{html.escape(t("hero_pill_reply"))}</div>'
        f'<div class="hero-pill">{html.escape(t("hero_pill_tone"))}</div>'
        f'<div class="hero-pill">{html.escape(t("hero_pill_history"))}</div>'
        '</div>'
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
        "subtitle": "A multilingual toolkit for Mandarin, Cantonese, Korean, Japanese, and English.",
        "subtitle_v2": "Cross-cultural communication coach for Mandarin, Cantonese, Korean, Japanese, and English.",
        "ui_language": "UI language",
        "account_title": "Account",
        "account_note": "We only store your task history locally on this app's database.",
        "login_tab": "Login",
        "register_tab": "Create account",
        "guest_tab": "Guest",
        "password": "Password",
        "confirm_password": "Confirm password",
        "create_account": "Create account",
        "invalid_login": "Invalid username or password.",
        "password_mismatch": "Passwords do not match.",
        "account_created": "Account created.",
        "username_too_short": "Username must be at least 2 characters.",
        "password_too_short": "Password must be at least 6 characters.",
        "username_exists": "This username already exists.",
        "account_error": "Could not create account.",
        "guest_note": "Try the app without creating an account. Guest mode does not save history, review cards, or vocab.",
        "auth_guest_mode": "Guest mode",
        "auth_password_mode": "Password account",
        "continue_guest": "Guest",
        "username_required": "Enter a username or continue as Guest.",
        "guest_user": "Guest",
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
        "provider_auto_option": "Auto: OpenAI → Anthropic → DeepSeek fallback",
        "all_filter": "All",
        "tts_too_long": "Text too long for TTS. Use shorter text.",
        "show_pron": "Show pronunciation and TTS",
        "tip": "Tip: Keep inputs short and specific for best results.",
        "hero_langs": "Mandarin · Cantonese · Korean · Japanese · English",
        "hero_pill_reply": "Reply coaching",
        "hero_pill_tone": "Tone analysis",
        "hero_pill_history": "Local history",
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
        "feature_course": "Course Learning",
        "feature_course_sub": "Guided daily lessons and drills",
        "feature_tone": "Tone Analysis",
        "feature_tone_sub": "Politeness, formality, directness",
        "recommendations_nav": "Recommendations",
        "recommendations_title": "AI Feature Recommendations",
        "recommendations_sub": "Personalised suggestions based on your language goals and activity.",
        "recommendations_top_pick": "Top pick",
        "recommendations_score": "Match",
        "recommendations_try": "Try",
        "recommendations_empty": "Complete a few tasks first, then come back for personalised recommendations.",
        "recommendations_feedback": "Recommendations update as you use more features. Check back after trying something new.",
        "recommendation_coach_name": "AI Chat Coach",
        "recommendation_coach_desc": "Get culturally-aware reply suggestions with tone analysis, cultural notes, and pronunciation guides.",
        "recommendation_pronunciation_name": "Pronunciation Guide",
        "recommendation_pronunciation_desc": "Hear native pronunciation with romanisation and text-to-speech for any language.",
        "recommendation_grammar_name": "Grammar Correction",
        "recommendation_grammar_desc": "Fix mistakes with level-appropriate explanations and reusable example patterns.",
        "recommendation_natural_name": "Natural Expression",
        "recommendation_natural_desc": "Turn translated-sounding sentences into something a native speaker would actually send.",
        "recommendation_tone_name": "Tone Analysis",
        "recommendation_tone_desc": "Check if your message sounds polite, rude, formal, friendly, or natural before you send it.",
        "recommendation_vocab_name": "Vocab Builder",
        "recommendation_vocab_desc": "Save phrases from real conversations and grow your personal phrase bank over time.",
        "recommendation_kpop_name": "K-pop / Drama Context",
        "recommendation_kpop_desc": "Understand lyrics, drama lines, slang, and cultural references in media content.",
        "recommendation_conversation_memory_name": "Conversation Memory Coach",
        "recommendation_conversation_memory_desc": "Continue natural multi-turn conversations where the AI remembers what you talked about.",
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
        "quota_guest_limit": "Guest preview limit reached. Log in for your own daily quota.",
        "quota_user_limit": "Daily AI action limit reached. Try again tomorrow.",
        "db_init_failed": "Database init failed",
        "history_save_failed": "Failed to save history",
        "detected_source": "Detected source",
        "pronunciation_label": "Pronunciation",
        "playing_audio": "Generating audio...",
        "tts_not_supported": "TTS not supported for this language.",
        "voice_input": "Voice input",
        "swap_unavailable_auto": "Auto — swap unavailable",
        "upload_audio": "Upload audio file",
        "transcribe": "Transcribe",
        "transcribing": "Transcribing...",
        "ok": "OK",
        "stt_unavailable": "Speech-to-text not available.",
        "please_upload_audio_first": "Please upload an audio file first.",
        "live_mic_note": "Record from your microphone.",
        "direct_mic_note": "Record directly here. The transcript will be placed into the text box above.",
        "upload_audio_fallback": "Upload audio instead",
        "phonetic_input_tip": "You can type pinyin, Jyutping/Cantonese romanization, Korean romanization, or Japanese romaji directly.",
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
        "verdict_natural": "Natural",
        "verdict_somewhat_natural": "Somewhat natural",
        "verdict_machine_translated": "Translated-sounding",
        "region_mode": "Regional / cultural mode",
        "region_mainland_cn": "Mainland Chinese mode",
        "region_hk_yue": "Hong Kong Cantonese mode",
        "region_korean": "Korean mode",
        "region_au_en": "Australian English mode",
        "region_us_en": "American English mode",
        "region_jp": "Japanese mode",
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
        "try_examples": "Try an example:",
        "workflow_1": "Paste a real message or situation",
        "workflow_2": "Choose language, region, tone, and task",
        "workflow_3": "Generate options with explanations",
        "workflow_4": "Save useful results in local history",
        "recent_activity": "Recent activity",
        "page_tip_title": "How to use this page",
        "say_translate_tip": "Paste a message, choose source and target language, then run. Use examples if you do not know where to start.",
        "coach_mean_tip": "Use a real chat line or situation. The app will explain tone, hidden meaning, or help you prepare a reply.",
        "grammar_tip": "Paste one sentence or short paragraph. Choose your level so the correction is not too difficult.",
        "natural_tip": "Paste a sentence that feels translated or stiff. Choose the tone you want.",
        "vocab_tip": "Paste words, lyrics, homework text, or chat messages. The app will explain useful phrases.",
        "tone_tip": "Paste a sentence before sending it. The app checks if it sounds cold, rude, polite, formal, or natural.",
        "start_tip_title": "Start in 10 seconds",
        "start_tip_body": "Enter a username for separate local history, or use Guest to try the app immediately.",
        "status_workspace": "Workspace",
        "status_learning_path": "Learning path",
        "status_ai": "AI status",
        "provider_ready": "Ready",
        "provider_auto_ready": "Auto fallback ready",
        "provider_missing_key": "Missing API key",
        "quick_coach": "Open Chat Coach",
        "quick_translate": "Translate",
        "quick_history": "History",
        "advanced_settings": "Advanced settings",
        "workspace_ready": "Workspace ready",
        "result_actions": "Next actions",
        "new_conversation": "🔄 New Conversation",
        "conversation_reset": "Conversation reset because language or region changed.",
        "download_result": "Download result",
        "copy_ready": "Copy-ready text",
        "group_chat": "Chat & replies",
        "group_understand": "Understand content",
        "group_learning": "Learning tools",
        "group_language_tools": "Language tools",
        "group_workspace": "Workspace",
        "workspace_nav": "Workspace",
        "workspace_assets": "Your assets",
        "login_required_title": "Login required",
        "guest_no_save_note": "Guest mode is for trying the app only. Log in with an account to save history, review cards, and vocab.",
        "asset_history": "Saved tasks",
        "asset_modes": "Modes used",
        "asset_latest": "Latest",
        "asset_review": "Review cards",
        "asset_vocab": "Vocab items",
        "asset_today": "Today points",
        "asset_streak": "Streak",
        "asset_top_mode": "Top mode",
        "save_review": "Save to review",
        "saved_review": "Saved to review.",
        "save_failed": "Save failed",
        "add_vocab": "Add to vocab",
        "saved_vocab": "Added to vocab.",
        "review_book": "Review Book",
        "vocab_bank": "Vocab Bank",
        "learning_report": "Learning Report",
        "metric_today": "Today",
        "metric_week": "This week",
        "metric_streak": "Streak",
        "metric_review": "Review",
        "review_title": "Review Book",
        "review_sub": "Saved corrections, replies, and explanations for spaced review.",
        "review_search": "Search review cards",
        "empty_review_title": "No review cards yet",
        "empty_review_body": "Run any AI task, then use Save to review under the result.",
        "review_again": "Practice again",
        "vocab_title": "Vocab Bank",
        "vocab_sub": "A personal phrase bank built from your real tasks.",
        "vocab_term": "Term or phrase",
        "vocab_meaning": "Meaning / note",
        "vocab_example": "Example sentence",
        "vocab_add_manual": "Add phrase",
        "vocab_term_required": "Add a term first.",
        "vocab_search": "Search vocab",
        "empty_vocab_title": "No vocab yet",
        "empty_vocab_body": "Add phrases manually or save outputs from Vocabulary explanations.",
        "report_title": "Learning Report",
        "report_sub": "A quick picture of what you practiced and what to do next.",
        "report_focus_title": "Current focus",
        "report_next_title": "Recommended next step",
        "report_next_body": "Review two saved cards, add one phrase to vocab, then finish one course drill.",
        "report_recent": "Recent learning signals",
        "course_title": "Course Learning",
        "course_sub": "A guided path that turns the tools into daily practice.",
        "course_note_title": "How this course works",
        "course_note_body": "Pick one short lesson, practice with a prepared prompt, then save useful outputs in your local history.",
        "course_today": "Today's path",
        "course_step_1": "Step 1",
        "course_step_2": "Step 2",
        "course_step_3": "Step 3",
        "course_lesson_grammar": "Fix one real sentence",
        "course_lesson_grammar_body": "Learn the mistake, the corrected sentence, and one pattern you can reuse.",
        "course_lesson_natural": "Make it sound natural",
        "course_lesson_natural_body": "Turn a translated-sounding sentence into a version you can actually send.",
        "course_lesson_reply": "Use it in a real chat",
        "course_lesson_reply_body": "Practice a culturally appropriate reply for school, work, friends, or dating.",
        "course_practice_grammar": "Practice grammar",
        "course_practice_natural": "Practice natural expression",
        "course_practice_reply": "Practice chat reply",
        "course_drills": "Focused drills",
        "course_drills_sub": "Short exercises you can repeat whenever you have five minutes.",
        "course_drill_vocab": "Vocabulary Builder",
        "course_drill_vocab_title": "Build a phrase bank",
        "course_drill_vocab_body": "Collect phrases from assignments, chats, lyrics, and daily situations.",
        "course_drill_tone": "Tone Check",
        "course_drill_tone_title": "Check before you send",
        "course_drill_tone_body": "Learn whether a message sounds cold, polite, direct, formal, or friendly.",
        "course_practice_vocab": "Practice vocabulary",
        "course_practice_tone": "Practice tone",
    },
    "zh": {
        "app_title": "TriLingua Bridge",
        "subtitle": "面向普通话、粤语、韩语、日语、英语的多语言沟通工具。",
        "subtitle_v2": "跨文化沟通教练（支持普通话 / 粤语 / 韩语 / 日语 / 英语）",
        "ui_language": "界面语言",
        "account_title": "账号",
        "account_note": "仅在本地数据库保存历史记录。",
        "login_tab": "登录",
        "register_tab": "创建账号",
        "guest_tab": "游客",
        "password": "密码",
        "confirm_password": "确认密码",
        "create_account": "创建账号",
        "invalid_login": "用户名或密码错误。",
        "password_mismatch": "两次输入的密码不一致。",
        "account_created": "账号已创建。",
        "username_too_short": "用户名至少需要 2 个字符。",
        "password_too_short": "密码至少需要 6 个字符。",
        "username_exists": "这个用户名已经存在。",
        "account_error": "无法创建账号。",
        "guest_note": "不创建账号也可以先试用。游客模式不会保存历史、复习卡片或词库。",
        "auth_guest_mode": "游客模式",
        "auth_password_mode": "密码账号",
        "continue_guest": "游客",
        "username_required": "请输入用户名，或使用游客模式。",
        "guest_user": "游客",
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
        "provider_auto_option": "自动：OpenAI → Anthropic → DeepSeek 依次回退",
        "all_filter": "全部",
        "tts_too_long": "文本太长，暂时无法朗读。请缩短一点再试。",
        "show_pron": "显示发音与朗读",
        "tip": "提示：输入越具体越好。",
        "hero_langs": "普通话 · 粤语 · 韩语 · 日语 · 英语",
        "hero_pill_reply": "回复教练",
        "hero_pill_tone": "语气分析",
        "hero_pill_history": "本地历史",
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
        "feature_course": "课程学习",
        "feature_course_sub": "每日课程与专项练习",
        "feature_tone": "语气分析",
        "feature_tone_sub": "礼貌 / 正式 / 直接程度",
        "recommendations_nav": "智能推荐",
        "recommendations_title": "AI 功能推荐",
        "recommendations_sub": "根据你的语言目标和使用情况推荐适合的功能。",
        "recommendations_top_pick": "首选推荐",
        "recommendations_score": "匹配度",
        "recommendations_try": "试试看",
        "recommendations_empty": "先完成几个任务，再回来查看个性化推荐。",
        "recommendations_feedback": "推荐会随着你的使用情况更新。试用新功能后可以回来看看。",
        "recommendation_coach_name": "AI 聊天教练",
        "recommendation_coach_desc": "根据文化语境生成回复建议，并提供语气、文化说明和发音参考。",
        "recommendation_pronunciation_name": "发音指南",
        "recommendation_pronunciation_desc": "听母语发音，并查看拼音/罗马字与朗读。",
        "recommendation_grammar_name": "语法纠错",
        "recommendation_grammar_desc": "按你的水平修改错误，并给出可复用的例句模式。",
        "recommendation_natural_name": "自然表达",
        "recommendation_natural_desc": "把翻译腔的句子改成母语者更会发送的表达。",
        "recommendation_tone_name": "语气分析",
        "recommendation_tone_desc": "发送前检查信息是否礼貌、冷淡、正式、友好或自然。",
        "recommendation_vocab_name": "词汇积累",
        "recommendation_vocab_desc": "保存真实对话中的短语，逐步建立个人词库。",
        "recommendation_kpop_name": "K-pop / 影视语境",
        "recommendation_kpop_desc": "理解歌词、影视台词、网络用语和文化梗。",
        "recommendation_conversation_memory_name": "对话记忆教练",
        "recommendation_conversation_memory_desc": "进行多轮自然对话，让 AI 记住前文。",
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
        "quota_guest_limit": "游客预览次数已达上限。登录后可获得独立的每日配额。",
        "quota_user_limit": "今日 AI 操作次数已达上限。请明天再试。",
        "db_init_failed": "数据库初始化失败",
        "history_save_failed": "保存历史失败",
        "detected_source": "检测到的源语言",
        "pronunciation_label": "发音",
        "playing_audio": "生成语音中...",
        "tts_not_supported": "当前语言暂不支持 TTS。",
        "voice_input": "语音输入",
        "swap_unavailable_auto": "自动检测 — 无法交换",
        "upload_audio": "上传音频文件",
        "transcribe": "转写",
        "transcribing": "转写中...",
        "ok": "完成",
        "stt_unavailable": "语音识别不可用。",
        "please_upload_audio_first": "请先上传音频文件。",
        "live_mic_note": "使用麦克风录音。",
        "direct_mic_note": "可以直接在这里录音，转写结果会自动填入上方文本框。",
        "upload_audio_fallback": "改为上传音频",
        "phonetic_input_tip": "支持直接输入拼音、粤拼/粤语罗马字、韩语罗马字、日语罗马字。",
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
        "verdict_natural": "自然",
        "verdict_somewhat_natural": "基本自然",
        "verdict_machine_translated": "有翻译腔",
        "region_mode": "地区 / 文化模式",
        "region_mainland_cn": "大陆普通话模式",
        "region_hk_yue": "香港粤语模式",
        "region_korean": "韩国语模式",
        "region_au_en": "澳式英语模式",
        "region_us_en": "美式英语模式",
        "region_jp": "日语模式",
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
        "try_examples": "试试示例：",
        "workflow_1": "粘贴真实消息或场景",
        "workflow_2": "选择语言、地区、语气和任务",
        "workflow_3": "生成多个选项和解释",
        "workflow_4": "把有用结果保存到本地历史",
        "recent_activity": "最近使用",
        "page_tip_title": "这个页面怎么用",
        "say_translate_tip": "粘贴消息，选择源语言和目标语言后运行。不知道写什么时可以先点示例。",
        "coach_mean_tip": "粘贴真实聊天句子或具体情境，应用会帮你分析语气、潜台词，也可以帮你准备回复。",
        "grammar_tip": "粘贴一句话或短段落，选择你的级别，避免纠错结果过难。",
        "natural_tip": "粘贴一段听起来像翻译腔或不自然的句子，然后选择想要的语气。",
        "vocab_tip": "粘贴单词、歌词、作业文本或聊天消息，应用会解释有用表达。",
        "tone_tip": "发送前粘贴一句话，检查它是否显得冷淡、冒犯、礼貌、正式或自然。",
        "start_tip_title": "10 秒开始使用",
        "start_tip_body": "输入用户名可以分开保存本地历史；也可以直接用游客模式体验。",
        "status_workspace": "工作区",
        "status_learning_path": "学习路径",
        "status_ai": "AI 状态",
        "provider_ready": "已就绪",
        "provider_auto_ready": "自动备用已就绪",
        "provider_missing_key": "缺少 API Key",
        "quick_coach": "打开聊天教练",
        "quick_translate": "翻译",
        "quick_history": "历史",
        "advanced_settings": "高级设置",
        "workspace_ready": "工作区已就绪",
        "result_actions": "下一步操作",
        "new_conversation": "🔄 新对话",
        "conversation_reset": "语言或地区已更改，对话已重置。",
        "download_result": "下载结果",
        "copy_ready": "便于复制的文本",
        "group_chat": "聊天与回复",
        "group_understand": "理解内容",
        "group_learning": "学习工具",
        "group_language_tools": "语言工具",
        "group_workspace": "工作区",
        "workspace_nav": "工作区",
        "workspace_assets": "你的资产",
        "login_required_title": "需要登录",
        "guest_no_save_note": "游客模式只用于试用。登录账号后才能保存历史、复习卡片和词库。",
        "asset_history": "保存任务",
        "asset_modes": "使用模式",
        "asset_latest": "最近",
        "asset_review": "复习卡片",
        "asset_vocab": "个人词库",
        "asset_today": "今日积分",
        "asset_streak": "连续学习",
        "asset_top_mode": "常用模式",
        "save_review": "保存到复习",
        "saved_review": "已保存到复习。",
        "save_failed": "保存失败",
        "add_vocab": "加入词库",
        "saved_vocab": "已加入词库。",
        "review_book": "复习本",
        "vocab_bank": "个人词库",
        "learning_report": "学习报告",
        "metric_today": "今日",
        "metric_week": "本周",
        "metric_streak": "连续",
        "metric_review": "复习",
        "review_title": "复习本",
        "review_sub": "把修正、回复和解释沉淀成可反复看的复习卡片。",
        "review_search": "搜索复习卡片",
        "empty_review_title": "还没有复习卡片",
        "empty_review_body": "先完成任意 AI 任务，然后在结果下方点击保存到复习。",
        "review_again": "再练一次",
        "vocab_title": "个人词库",
        "vocab_sub": "从真实任务里积累你自己的短语库。",
        "vocab_term": "词 / 短语",
        "vocab_meaning": "含义 / 笔记",
        "vocab_example": "例句",
        "vocab_add_manual": "添加短语",
        "vocab_term_required": "先输入一个词或短语。",
        "vocab_search": "搜索词库",
        "empty_vocab_title": "还没有词库内容",
        "empty_vocab_body": "可以手动添加，也可以从词汇解释结果里一键保存。",
        "report_title": "学习报告",
        "report_sub": "快速看看你练了什么，以及下一步该练什么。",
        "report_focus_title": "当前重点",
        "report_next_title": "推荐下一步",
        "report_next_body": "复习两张卡片，加入一个新短语，再完成一个课程练习。",
        "report_recent": "最近学习信号",
        "course_title": "课程学习",
        "course_sub": "把工具变成可持续练习的学习路线。",
        "course_note_title": "课程怎么用",
        "course_note_body": "选择一个短课时，用准备好的练习进入工具，再把有用结果保存到本地历史。",
        "course_today": "今日路线",
        "course_step_1": "第 1 步",
        "course_step_2": "第 2 步",
        "course_step_3": "第 3 步",
        "course_lesson_grammar": "修正一个真实句子",
        "course_lesson_grammar_body": "看懂错误、修正版本，以及一个可复用句型。",
        "course_lesson_natural": "改得更自然",
        "course_lesson_natural_body": "把翻译腔改成真的能发出去的表达。",
        "course_lesson_reply": "用到真实聊天里",
        "course_lesson_reply_body": "练习适合学习、工作、朋友或暧昧场景的跨文化回复。",
        "course_practice_grammar": "练语法",
        "course_practice_natural": "练自然表达",
        "course_practice_reply": "练聊天回复",
        "course_drills": "专项练习",
        "course_drills_sub": "有五分钟就可以反复练的小任务。",
        "course_drill_vocab": "词汇积累",
        "course_drill_vocab_title": "建立短语库",
        "course_drill_vocab_body": "从作业、聊天、歌词和日常场景里积累可用表达。",
        "course_drill_tone": "语气检查",
        "course_drill_tone_title": "发送前检查",
        "course_drill_tone_body": "学习一句话听起来冷淡、礼貌、直接、正式还是友好。",
        "course_practice_vocab": "练词汇",
        "course_practice_tone": "练语气",
    },
}

TEXTS["ko"] = {
    **TEXTS["en"],
    **{
        "app_title": "TriLingua Bridge",
        "subtitle": "중국어, 광둥어, 한국어, 일본어, 영어를 위한 다국어 소통 도구.",
        "subtitle_v2": "중국어 / 광둥어 / 한국어 / 일본어 / 영어를 위한 다문화 커뮤니케이션 코치.",
        "ui_language": "인터페이스 언어",
        "account_title": "계정",
        "account_note": "작업 기록은 이 앱의 로컬 데이터베이스에만 저장됩니다.",
        "login_tab": "로그인",
        "register_tab": "계정 만들기",
        "guest_tab": "게스트",
        "password": "비밀번호",
        "confirm_password": "비밀번호 확인",
        "create_account": "계정 만들기",
        "invalid_login": "사용자명 또는 비밀번호가 올바르지 않습니다.",
        "password_mismatch": "비밀번호가 일치하지 않습니다.",
        "account_created": "계정이 생성되었습니다.",
        "username_too_short": "사용자명은 최소 2자 이상이어야 합니다.",
        "password_too_short": "비밀번호는 최소 6자 이상이어야 합니다.",
        "username_exists": "이미 존재하는 사용자명입니다.",
        "account_error": "계정을 만들 수 없습니다.",
        "guest_note": "계정 없이 먼저 사용해 볼 수 있습니다. 게스트 모드는 기록, 복습 카드, 단어장을 저장하지 않습니다.",
        "auth_guest_mode": "게스트 모드",
        "auth_password_mode": "비밀번호 계정",
        "continue_guest": "게스트",
        "username_required": "사용자명을 입력하거나 게스트로 시작하세요.",
        "guest_user": "게스트",
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
        "provider_auto_option": "자동: OpenAI → Anthropic → DeepSeek 순차 폴백",
        "all_filter": "전체",
        "tts_too_long": "텍스트가 너무 길어 음성으로 읽을 수 없습니다. 조금 줄여 주세요.",
        "show_pron": "발음과 TTS 표시",
        "tip": "팁: 입력은 짧고 구체적일수록 좋아요.",
        "hero_langs": "중국어 · 광둥어 · 한국어 · 일본어 · 영어",
        "hero_pill_reply": "답장 코칭",
        "hero_pill_tone": "말투 분석",
        "hero_pill_history": "로컬 기록",

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
        "feature_course": "코스 학습",
        "feature_course_sub": "매일 따라 하는 수업과 연습",
        "feature_tone": "말투 분석",
        "feature_tone_sub": "공손함 / 격식 / 직접성을 분석해요",
        "recommendations_nav": "추천",
        "recommendations_title": "AI 기능 추천",
        "recommendations_sub": "언어 목표와 사용 패턴을 바탕으로 맞춤 기능을 추천해요.",
        "recommendations_top_pick": "추천 1순위",
        "recommendations_score": "적합도",
        "recommendations_try": "사용해 보기",
        "recommendations_empty": "몇 가지 작업을 완료한 뒤 다시 오면 맞춤 추천을 볼 수 있어요.",
        "recommendations_feedback": "추천은 더 많은 기능을 사용할수록 업데이트됩니다. 새 기능을 써 본 뒤 다시 확인해 보세요.",
        "recommendation_coach_name": "AI 채팅 코치",
        "recommendation_coach_desc": "문화 맥락에 맞는 답장 제안과 말투 분석, 문화 설명, 발음 안내를 제공합니다.",
        "recommendation_pronunciation_name": "발음 가이드",
        "recommendation_pronunciation_desc": "모든 언어에서 원어민 발음, 로마자 표기, 음성 읽기를 확인할 수 있어요.",
        "recommendation_grammar_name": "문법 교정",
        "recommendation_grammar_desc": "수준에 맞는 설명과 다시 쓸 수 있는 예문 패턴으로 실수를 고쳐요.",
        "recommendation_natural_name": "자연스러운 표현",
        "recommendation_natural_desc": "번역투 문장을 원어민이 실제로 보낼 법한 표현으로 바꿔요.",
        "recommendation_tone_name": "말투 분석",
        "recommendation_tone_desc": "보내기 전에 메시지가 공손한지, 차가운지, 격식 있는지, 친근한지 확인해요.",
        "recommendation_vocab_name": "어휘 빌더",
        "recommendation_vocab_desc": "실제 대화에서 나온 표현을 저장하고 나만의 표현장을 키워요.",
        "recommendation_kpop_name": "K-pop / 드라마 맥락",
        "recommendation_kpop_desc": "가사, 드라마 대사, 은어, 문화적 배경을 이해해요.",
        "recommendation_conversation_memory_name": "대화 기억 코치",
        "recommendation_conversation_memory_desc": "AI가 앞 내용을 기억하는 자연스러운 다중 턴 대화를 이어가요.",

        "input_text": "텍스트를 입력하거나 붙여넣으세요",
        "run": "실행",
        "enter_text_translate": "번역할 텍스트를 입력하세요",
        "translate_btn": "번역",
        "source_language": "원문 언어",
        "language_of_text": "텍스트 언어",
        "auto_detect": "자동 감지",
        "working": "처리 중...",
        "ai_call_failed": "AI 호출 실패",
        "quota_guest_limit": "게스트 미리보기 한도에 도달했습니다. 로그인하면 개인 할당량이 제공됩니다.",
        "quota_user_limit": "오늘의 AI 작업 한도에 도달했습니다. 내일 다시 시도해 주세요.",
        "db_init_failed": "데이터베이스 초기화 실패",
        "history_save_failed": "기록 저장 실패",
        "detected_source": "감지된 원문 언어",

        "voice_input": "음성 입력",
        "swap_unavailable_auto": "자동 감지 — 교체 불가",
        "upload_audio": "오디오 파일 업로드",
        "transcribe": "전사",
        "transcribing": "전사 중...",
        "ok": "완료",
        "stt_unavailable": "음성 인식을 사용할 수 없습니다.",
        "please_upload_audio_first": "먼저 오디오 파일을 업로드하세요.",
        "live_mic_note": "마이크로 녹음하세요.",
        "direct_mic_note": "여기서 바로 녹음하세요. 전사 결과가 위 텍스트 상자에 자동으로 입력됩니다.",
        "upload_audio_fallback": "오디오 파일 업로드로 대신하기",
        "phonetic_input_tip": "병음, 광둥어 로마자/월병, 한국어 로마자, 일본어 로마자 입력도 바로 인식합니다.",
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
        "verdict_natural": "자연스러움",
        "verdict_somewhat_natural": "대체로 자연스러움",
        "verdict_machine_translated": "번역투가 있음",

        "region_mode": "지역 / 문화 모드",
        "region_mainland_cn": "중국 본토 모드",
        "region_hk_yue": "홍콩 광둥어 모드",
        "region_korean": "한국어 모드",
        "region_au_en": "호주 영어 모드",
        "region_us_en": "미국 영어 모드",
        "region_jp": "일본어 모드",

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
        "try_examples": "예시를 사용해 보세요:",
        "workflow_1": "실제 메시지나 상황을 붙여넣기",
        "workflow_2": "언어, 지역, 말투, 작업 선택",
        "workflow_3": "설명과 함께 여러 선택지 생성",
        "workflow_4": "유용한 결과를 로컬 기록에 저장",
        "recent_activity": "최근 활동",
        "page_tip_title": "이 페이지 사용법",
        "say_translate_tip": "메시지를 붙여넣고 원문/목표 언어를 고른 뒤 실행하세요. 막막하면 예시부터 눌러 보세요.",
        "coach_mean_tip": "실제 채팅 문장이나 상황을 넣어 보세요. 말투와 숨은 의미를 설명하거나 답장을 준비해 줍니다.",
        "grammar_tip": "문장 하나나 짧은 문단을 붙여넣으세요. 레벨을 고르면 너무 어렵지 않게 교정합니다.",
        "natural_tip": "번역투처럼 느껴지거나 어색한 문장을 붙여넣고 원하는 말투를 선택하세요.",
        "vocab_tip": "단어, 가사, 과제 문장, 채팅 메시지를 붙여넣으면 유용한 표현을 설명합니다.",
        "tone_tip": "보내기 전 문장을 붙여넣으면 차갑거나 무례한지, 공손한지, 자연스러운지 확인합니다.",
        "start_tip_title": "10초 만에 시작하기",
        "start_tip_body": "사용자명을 입력하면 로컬 기록을 따로 저장할 수 있고, 게스트로 바로 체험할 수도 있습니다.",
        "status_workspace": "작업 공간",
        "status_learning_path": "학습 경로",
        "status_ai": "AI 상태",
        "provider_ready": "준비됨",
        "provider_auto_ready": "자동 대체 준비됨",
        "provider_missing_key": "API 키 없음",
        "quick_coach": "채팅 코치 열기",
        "quick_translate": "번역",
        "quick_history": "기록",
        "advanced_settings": "고급 설정",
        "workspace_ready": "작업 공간 준비됨",
        "result_actions": "다음 작업",
        "new_conversation": "🔄 새 대화",
        "conversation_reset": "언어 또는 지역이 변경되어 대화가 초기화되었습니다.",
        "download_result": "결과 다운로드",
        "copy_ready": "복사하기 쉬운 텍스트",
        "group_chat": "채팅과 답장",
        "group_understand": "내용 이해",
        "group_learning": "학습 도구",
        "group_language_tools": "언어 도구",
        "group_workspace": "작업 공간",
        "workspace_nav": "작업 공간",
        "workspace_assets": "내 학습 자산",
        "login_required_title": "로그인이 필요합니다",
        "guest_no_save_note": "게스트 모드는 체험용입니다. 기록, 복습 카드, 단어장을 저장하려면 계정으로 로그인하세요.",
        "asset_history": "저장된 작업",
        "asset_modes": "사용한 모드",
        "asset_latest": "최근",
        "asset_review": "복습 카드",
        "asset_vocab": "단어장 항목",
        "asset_today": "오늘 포인트",
        "asset_streak": "연속 학습",
        "asset_top_mode": "자주 쓴 모드",
        "save_review": "복습에 저장",
        "saved_review": "복습에 저장했어요.",
        "save_failed": "저장 실패",
        "add_vocab": "단어장에 추가",
        "saved_vocab": "단어장에 추가했어요.",
        "review_book": "복습장",
        "vocab_bank": "단어장",
        "learning_report": "학습 리포트",
        "metric_today": "오늘",
        "metric_week": "이번 주",
        "metric_streak": "연속",
        "metric_review": "복습",
        "review_title": "복습장",
        "review_sub": "저장한 교정, 답장, 설명을 다시 볼 수 있습니다.",
        "review_search": "복습 카드 검색",
        "empty_review_title": "아직 복습 카드가 없습니다",
        "empty_review_body": "AI 작업을 실행한 뒤 결과 아래에서 복습에 저장하세요.",
        "review_again": "다시 연습",
        "vocab_title": "단어장",
        "vocab_sub": "실제 작업에서 모은 나만의 표현 저장소입니다.",
        "vocab_term": "단어 / 표현",
        "vocab_meaning": "뜻 / 메모",
        "vocab_example": "예문",
        "vocab_add_manual": "표현 추가",
        "vocab_term_required": "먼저 단어나 표현을 입력하세요.",
        "vocab_search": "단어장 검색",
        "empty_vocab_title": "아직 단어장이 비어 있습니다",
        "empty_vocab_body": "직접 추가하거나 어휘 설명 결과에서 저장하세요.",
        "report_title": "학습 리포트",
        "report_sub": "무엇을 연습했고 다음에 무엇을 할지 빠르게 보여줍니다.",
        "report_focus_title": "현재 집중 영역",
        "report_next_title": "추천 다음 단계",
        "report_next_body": "복습 카드 두 장을 보고, 표현 하나를 단어장에 넣은 뒤 코스 드릴 하나를 끝내세요.",
        "report_recent": "최근 학습 신호",
        "course_title": "코스 학습",
        "course_sub": "도구를 매일 연습으로 이어 주는 학습 경로입니다.",
        "course_note_title": "코스 사용법",
        "course_note_body": "짧은 수업 하나를 고르고 준비된 프롬프트로 연습한 뒤, 유용한 결과를 로컬 기록에 저장하세요.",
        "course_today": "오늘의 경로",
        "course_step_1": "1단계",
        "course_step_2": "2단계",
        "course_step_3": "3단계",
        "course_lesson_grammar": "실제 문장 하나 고치기",
        "course_lesson_grammar_body": "틀린 부분, 수정된 문장, 다시 쓸 수 있는 패턴을 익혀요.",
        "course_lesson_natural": "더 자연스럽게 만들기",
        "course_lesson_natural_body": "번역투 문장을 실제로 보낼 수 있는 표현으로 바꿔요.",
        "course_lesson_reply": "실제 채팅에 써보기",
        "course_lesson_reply_body": "학교, 일, 친구, 연애 상황에 맞는 문화적으로 자연스러운 답장을 연습해요.",
        "course_practice_grammar": "문법 연습",
        "course_practice_natural": "자연스러운 표현 연습",
        "course_practice_reply": "채팅 답장 연습",
        "course_drills": "집중 연습",
        "course_drills_sub": "5분만 있어도 반복할 수 있는 짧은 연습입니다.",
        "course_drill_vocab": "어휘 쌓기",
        "course_drill_vocab_title": "표현 모음 만들기",
        "course_drill_vocab_body": "과제, 채팅, 가사, 일상 상황에서 쓸 수 있는 표현을 모아요.",
        "course_drill_tone": "말투 점검",
        "course_drill_tone_title": "보내기 전에 확인",
        "course_drill_tone_body": "문장이 차갑게, 공손하게, 직접적으로, 격식 있게, 친근하게 들리는지 배워요.",
        "course_practice_vocab": "어휘 연습",
        "course_practice_tone": "말투 연습",
    },
}

TEXTS["yue"] = {
    **TEXTS["zh"],
    **{
        "app_title": "TriLingua Bridge",
        "subtitle": "面向普通話、粵語、韓文、日文、英文嘅多語言溝通工具。",
        "subtitle_v2": "跨文化溝通教練（支援普通話 / 粵語 / 韓文 / 日文 / 英文）",
        "ui_language": "介面語言",
        "account_title": "帳號",
        "account_note": "只會喺本地資料庫儲存任務記錄。",
        "login_tab": "登入",
        "register_tab": "建立帳號",
        "guest_tab": "訪客",
        "password": "密碼",
        "confirm_password": "確認密碼",
        "create_account": "建立帳號",
        "invalid_login": "用戶名或者密碼唔啱。",
        "password_mismatch": "兩次輸入嘅密碼唔一致。",
        "account_created": "帳號已建立。",
        "username_too_short": "用戶名最少要 2 個字元。",
        "password_too_short": "密碼最少要 6 個字元。",
        "username_exists": "呢個用戶名已經有人用。",
        "account_error": "暫時建立唔到帳號。",
        "guest_note": "可以唔建立帳號先試用。訪客模式唔會儲存歷史、溫習卡或者詞庫。",
        "auth_guest_mode": "訪客模式",
        "auth_password_mode": "密碼帳號",
        "continue_guest": "訪客",
        "username_required": "請輸入用戶名，或者用訪客模式。",
        "guest_user": "訪客",
        "username": "用戶名",
        "login": "登入",
        "logout": "登出",
        "prefs_title": "偏好設定",
        "my_native": "我嘅母語",
        "i_learn": "我想學",
        "persona": "人設",
        "creativity": "創意度",
        "model": "模型",
        "ai_provider": "AI 模型服務",
        "provider_auto_option": "自動：OpenAI → Anthropic → DeepSeek 依次回退",
        "all_filter": "全部",
        "tts_too_long": "文字太長，暫時朗讀唔到。請縮短少少再試。",
        "show_pron": "顯示發音同朗讀",
        "tip": "貼士：輸入越短越具體，效果越好。",
        "hero_langs": "普通話 · 粵語 · 韓文 · 日文 · 英文",
        "hero_pill_reply": "回覆教練",
        "hero_pill_tone": "語氣分析",
        "hero_pill_history": "本地歷史",

        "nav_home": "首頁",
        "back_home": "返首頁",
        "nav_history": "歷史",
        "nav_about": "關於",

        "what_can": "可以做啲咩？",
        "what_can_v2": "你嘅跨文化聊天助手",
        "what_can_sub": "揀一個任務，保持語言、語氣同文化語境一致。",
        "not_social": "呢個應用唔係社交平台。",

        "mode_say": "講得自然啲",
        "mode_say_sub": "令你句嘢聽落更自然",
        "mode_mean": "佢想表達咩？",
        "mode_mean_sub": "解釋潛台詞同語氣",
        "mode_kpop": "歌詞同影視語境",
        "mode_kpop_sub": "K-pop / 影視 / 網絡語境解析",
        "mode_coach": "AI 聊天教練",
        "mode_coach_sub": "按文化語境幫你諗回覆",
        "mode_coach_v2": "AI 聊天教練",
        "mode_coach_sub_v2": "針對大陸 / 香港 / 韓國 / 澳洲 / 美國文化風格調整",

        "feature_translate": "翻譯",
        "feature_grammar": "文法",
        "feature_grammar_sub": "按你程度改錯同提點",
        "feature_natural": "自然表達",
        "feature_natural_sub": "講到似母語者",
        "feature_vocab": "詞彙",
        "feature_vocab_sub": "解釋重點詞組",
        "feature_course": "課程學習",
        "feature_course_sub": "每日課程同專項練習",
        "feature_tone": "語氣分析",
        "feature_tone_sub": "禮貌 / 正式 / 直接程度",
        "recommendations_nav": "智能推薦",
        "recommendations_title": "AI 功能推薦",
        "recommendations_sub": "根據你嘅語言目標同使用情況，推薦啱用嘅功能。",
        "recommendations_top_pick": "首選推薦",
        "recommendations_score": "匹配度",
        "recommendations_try": "試吓",
        "recommendations_empty": "先完成幾個任務，再返嚟睇個人化推薦。",
        "recommendations_feedback": "推薦會跟住你嘅使用情況更新。試完新功能之後可以返嚟睇吓。",
        "recommendation_coach_name": "AI 聊天教練",
        "recommendation_coach_desc": "按文化語境幫你諗回覆，並提供語氣分析、文化說明同發音提示。",
        "recommendation_pronunciation_name": "發音指南",
        "recommendation_pronunciation_desc": "聽母語者發音，睇羅馬字／拼音，亦可以朗讀文字。",
        "recommendation_grammar_name": "文法改錯",
        "recommendation_grammar_desc": "按你程度改錯，並提供可以重用嘅例句模式。",
        "recommendation_natural_name": "自然表達",
        "recommendation_natural_desc": "將翻譯腔句子改到似母語者真係會send嘅講法。",
        "recommendation_tone_name": "語氣分析",
        "recommendation_tone_desc": "send 出去之前，先睇吓語氣係禮貌、冷淡、正式、友善定自然。",
        "recommendation_vocab_name": "詞彙累積",
        "recommendation_vocab_desc": "保存真實對話入面嘅短語，慢慢建立自己嘅詞庫。",
        "recommendation_kpop_name": "K-pop / 影視語境",
        "recommendation_kpop_desc": "理解歌詞、影視對白、網絡用語同文化梗。",
        "recommendation_conversation_memory_name": "對話記憶教練",
        "recommendation_conversation_memory_desc": "延續多輪自然對話，等 AI 記住之前講過嘅內容。",

        "input_text": "輸入或者貼上文字",
        "run": "開始",
        "enter_text_translate": "輸入要翻譯嘅文字",
        "translate_btn": "翻譯",
        "source_language": "原文語言",
        "language_of_text": "呢段文字嘅語言",
        "auto_detect": "自動偵測",
        "working": "處理中...",
        "ai_call_failed": "AI 連線失敗",
        "quota_guest_limit": "訪客預覽次數已達上限。登入後可獲得獨立嘅每日配額。",
        "quota_user_limit": "今日 AI 操作次數已達上限。請聽日再試。",
        "db_init_failed": "資料庫初始化失敗",
        "history_save_failed": "儲存歷史失敗",
        "detected_source": "偵測到嘅原文語言",

        "voice_input": "語音輸入",
        "swap_unavailable_auto": "自動偵測 — 無法交換",
        "upload_audio": "上載音頻文件",
        "transcribe": "轉寫",
        "transcribing": "轉寫中...",
        "ok": "完成",
        "stt_unavailable": "語音識別暫時不可用。",
        "please_upload_audio_first": "請先上載音頻文件。",
        "live_mic_note": "用咪高峰錄音。",
        "direct_mic_note": "可以直接喺度錄音，轉寫結果會自動填入上面個文字框。",
        "upload_audio_fallback": "改為上載音頻",
        "phonetic_input_tip": "可以直接輸入拼音、粵拼/粵語羅馬字、韓文羅馬字、日文羅馬字。",
        "start_recording": "開始錄音",
        "stop_recording": "停止",
        "mic_not_installed": "未安裝 streamlit-mic-recorder，暫時用唔到咪高峰錄音。",

        "pronunciation_label": "發音",
        "playing_audio": "生成語音中...",
        "tts_not_supported": "目前語言暫時唔支援 TTS。",

        "relation_mode": "關係 / 風格",
        "style_friend": "朋友",
        "style_crush": "曖昧對象",
        "style_work": "同事 / 工作",
        "style_formal": "正式",
        "style_cute": "可愛",
        "style_cold": "冷淡少少",
        "style_kpop": "K-pop 氛圍",
        "style_hk": "香港本地味",

        "ctx_kpop": "K-pop 歌詞",
        "ctx_kdrama": "韓劇對白",
        "ctx_cantodrama": "港劇對白",
        "ctx_cdrama": "國劇對白",
        "ctx_eng_tv": "英文影視",
        "ctx_inet": "網絡用語",
        "ctx_pop": "流行文化",
        "context_type": "語境類型",

        "enter_text_correct": "輸入要修正嘅文字",
        "correct_btn": "文法修正",
        "learner_level": "學習者程度",
        "enter_text_natural": "輸入你嘅草稿",
        "desired_tone": "想要嘅語氣",
        "suggest_btn": "畀個建議",
        "enter_text_vocab": "輸入文字嚟解釋詞彙",
        "max_items": "最多項目",
        "explain_vocab_btn": "解釋詞彙",
        "enter_text_tone": "輸入文字以分析語氣",
        "analyze_tone_btn": "分析語氣",

        "history_title": "歷史記錄",
        "history_sub": "最近任務",
        "filter_mode": "模式",
        "filter_source": "原文語言",
        "filter_target": "想轉成嘅語言",
        "filter_persona": "人設",
        "search_in": "搜尋歷史",
        "show_last": "顯示最近 N 筆",
        "history_load_failed": "讀取歷史失敗",
        "no_history": "暫時未有歷史。",
        "input_label": "輸入",
        "output_label": "輸出",

        "model_info_prefix": "模型",
        "tokens_label": "Tokens",
        "latency_label": "延遲",

        "about_title": "關於",
        "about_desc": "TriLingua Bridge v2 — 跨文化溝通教練。",
        "enter_text_warn": "請先輸入文字先。",

        "naturalness_score_title": "自然程度評分",
        "naturalness_verdict": "判斷",
        "naturalness_score": "分數",
        "naturalness_reason": "原因",
        "naturalness_suggestion": "更自然版本",
        "verdict_natural": "自然",
        "verdict_somewhat_natural": "大致自然",
        "verdict_machine_translated": "有翻譯腔",

        "region_mode": "地區 / 文化模式",
        "region_mainland_cn": "大陸普通話模式",
        "region_hk_yue": "香港粵語模式",
        "region_korean": "韓國語模式",
        "region_au_en": "澳式英文模式",
        "region_us_en": "美式英文模式",
        "region_jp": "日文模式",

        "screenshot_mode": "聊天截圖分析",
        "analyze_screenshot_btn": "分析截圖",
        "upload_screenshot": "上載聊天截圖",
        "please_upload_image_first": "請先上載圖片。",
        "screenshot_not_available": "暫時用唔到截圖分析。",

        "reply_options": "回覆建議",
        "tone_notes": "語氣說明",
        "cultural_notes": "文化說明",
        "suggested_best_reply": "建議用呢句",
        "why_this_works": "點解咁回",
        "pronunciation": "發音",
        "examples": "例子",
        "corrected_version": "修正後版本",
        "notes": "說明",
        "clean_translation": "自然翻譯",
        "summary": "總結",
        "recommended_understanding": "建議咁理解",
        "tone_summary": "語氣總結",
        "intent": "意圖",
        "tips": "建議",
        "better_version": "更自然版本",
        "items": "項目",
        "key_phrases": "重點短語",
        "slang_pop_culture": "俚語 / 流行文化",
        "suggestions": "建議",
        "try_examples": "試吓例子：",
        "workflow_1": "貼上真實訊息或者情境",
        "workflow_2": "揀語言、地區、語氣同任務",
        "workflow_3": "產生幾個講法同解釋",
        "workflow_4": "有用嘅結果會留喺本地歷史",
        "recent_activity": "最近用過",
        "page_tip_title": "呢頁點用",
        "say_translate_tip": "貼上訊息，揀原文同想轉成嘅語言，再撳開始。唔知點試可以先撳例子。",
        "coach_mean_tip": "貼上真實聊天句子或者情境；我哋會幫你睇語氣、潛台詞，或者諗點樣回覆。",
        "grammar_tip": "貼上一句或者一小段，揀返你程度，改出嚟就唔會太深。",
        "natural_tip": "貼上覺得似翻譯腔或者唔夠自然嘅句子，再揀想要嘅語氣。",
        "vocab_tip": "貼上單字、歌詞、功課文字或者聊天訊息，幫你拆解有用表達。",
        "tone_tip": "傳送前貼上句子，睇吓會唔會太冷淡、太直接、夠唔夠禮貌或者自然。",
        "start_tip_title": "10 秒即刻開始",
        "start_tip_body": "輸入用戶名可以分開儲存本地歷史；或者直接用訪客模式試玩。",
        "status_workspace": "工作區",
        "status_learning_path": "學習路線",
        "status_ai": "AI 狀態",
        "provider_ready": "已準備好",
        "provider_auto_ready": "自動備用已準備好",
        "provider_missing_key": "未設定 API Key",
        "quick_coach": "開聊天教練",
        "quick_translate": "翻譯",
        "quick_history": "歷史",
        "advanced_settings": "進階設定",
        "workspace_ready": "工作區已準備好",
        "result_actions": "下一步",
        "new_conversation": "🔄 新對話",
        "conversation_reset": "語言或地區已更改，對話已重置。",
        "download_result": "下載結果",
        "copy_ready": "方便複製嘅文字",
        "group_chat": "聊天同回覆",
        "group_understand": "睇明內容",
        "group_learning": "學習工具",
        "group_language_tools": "語言工具",
        "group_workspace": "工作區",
        "workspace_nav": "工作區",
        "workspace_assets": "你嘅學習資產",
        "login_required_title": "需要登入",
        "guest_no_save_note": "訪客模式只係用嚟試用。登入帳號之後先可以儲存歷史、溫習卡同詞庫。",
        "asset_history": "已儲存任務",
        "asset_modes": "用過嘅模式",
        "asset_latest": "最近",
        "asset_review": "溫習卡",
        "asset_vocab": "詞庫項目",
        "asset_today": "今日分數",
        "asset_streak": "連續學習",
        "asset_top_mode": "常用模式",
        "save_review": "儲存去溫習",
        "saved_review": "已儲存去溫習。",
        "save_failed": "儲存失敗",
        "add_vocab": "加入詞庫",
        "saved_vocab": "已加入詞庫。",
        "review_book": "溫習本",
        "vocab_bank": "個人詞庫",
        "learning_report": "學習報告",
        "metric_today": "今日",
        "metric_week": "今個星期",
        "metric_streak": "連續",
        "metric_review": "溫習",
        "review_title": "溫習本",
        "review_sub": "將修正、回覆同解釋儲存成可以再睇嘅溫習卡。",
        "review_search": "搜尋溫習卡",
        "empty_review_title": "暫時未有溫習卡",
        "empty_review_body": "先做一次 AI 任務，再喺結果下面撳儲存去溫習。",
        "review_again": "再練一次",
        "vocab_title": "個人詞庫",
        "vocab_sub": "由真實任務累積你自己嘅短語庫。",
        "vocab_term": "詞 / 短語",
        "vocab_meaning": "意思 / 筆記",
        "vocab_example": "例句",
        "vocab_add_manual": "新增短語",
        "vocab_term_required": "請先輸入詞或短語。",
        "vocab_search": "搜尋詞庫",
        "empty_vocab_title": "詞庫暫時未有內容",
        "empty_vocab_body": "可以手動新增，亦可以由詞彙解釋結果儲存。",
        "report_title": "學習報告",
        "report_sub": "快速睇你練咗啲咩，同下一步應該練咩。",
        "report_focus_title": "而家重點",
        "report_next_title": "建議下一步",
        "report_next_body": "溫習兩張卡、加一個新短語入詞庫，再完成一個課程練習。",
        "report_recent": "最近學習訊號",
        "course_title": "課程學習",
        "course_sub": "將工具變成可以每日練習嘅學習路線。",
        "course_note_title": "課程點用",
        "course_note_body": "揀一個短課，用準備好嘅練習入工具，之後將有用結果留喺本地歷史。",
        "course_today": "今日路線",
        "course_step_1": "第 1 步",
        "course_step_2": "第 2 步",
        "course_step_3": "第 3 步",
        "course_lesson_grammar": "改一個真實句子",
        "course_lesson_grammar_body": "睇明錯喺邊、點改，同埋一個下次可以再用嘅句式。",
        "course_lesson_natural": "改到自然啲",
        "course_lesson_natural_body": "將翻譯腔改成真係可以發出去嘅講法。",
        "course_lesson_reply": "用喺真實聊天",
        "course_lesson_reply_body": "練習學校、工作、朋友或者曖昧場景入面啱文化語境嘅回覆。",
        "course_practice_grammar": "練文法",
        "course_practice_natural": "練自然表達",
        "course_practice_reply": "練聊天回覆",
        "course_drills": "專項練習",
        "course_drills_sub": "有五分鐘就可以重複練嘅小任務。",
        "course_drill_vocab": "詞彙累積",
        "course_drill_vocab_title": "建立短語庫",
        "course_drill_vocab_body": "由功課、聊天、歌詞同日常情境入面累積用得着嘅表達。",
        "course_drill_tone": "語氣檢查",
        "course_drill_tone_title": "發送前睇一睇",
        "course_drill_tone_body": "學一句話聽落係冷淡、禮貌、直接、正式定友善。",
        "course_practice_vocab": "練詞彙",
        "course_practice_tone": "練語氣",
    },
}

TEXTS["ja"] = {
    **TEXTS["en"],
    **{
        "app_title": "TriLingua Bridge",
        "subtitle": "北京語、広東語、韓国語、英語のための多言語ツールキット。",
        "subtitle_v2": "北京語・広東語・韓国語・英語対応の異文化コミュニケーションコーチ。",
        "ui_language": "表示言語",
        "account_title": "アカウント",
        "account_note": "タスク履歴はこのアプリのローカルDBにのみ保存されます。",
        "login_tab": "ログイン",
        "register_tab": "アカウント作成",
        "guest_tab": "ゲスト",
        "password": "パスワード",
        "confirm_password": "パスワード確認",
        "create_account": "アカウント作成",
        "invalid_login": "ユーザー名またはパスワードが違います。",
        "password_mismatch": "パスワードが一致しません。",
        "account_created": "アカウントを作成しました。",
        "username_too_short": "ユーザー名は2文字以上で入力してください。",
        "password_too_short": "パスワードは6文字以上で入力してください。",
        "username_exists": "このユーザー名は既に使われています。",
        "account_error": "アカウントを作成できませんでした。",
        "guest_note": "アカウントを作成せずに試せます。ゲストモードでは履歴・復習カード・単語帳は保存されません。",
        "auth_guest_mode": "ゲストモード",
        "auth_password_mode": "パスワードアカウント",
        "continue_guest": "ゲスト",
        "username_required": "ユーザー名を入力するか、ゲストとして続けてください。",
        "guest_user": "ゲスト",
        "username": "ユーザー名",
        "login": "ログイン",
        "logout": "ログアウト",
        "prefs_title": "設定",
        "my_native": "母国語",
        "i_learn": "学習言語",
        "persona": "ペルソナ",
        "creativity": "創造性",
        "model": "モデル",
        "ai_provider": "AIプロバイダー",
        "provider_auto_option": "自動：OpenAI → Anthropic → DeepSeek の順にフォールバック",
        "all_filter": "すべて",
        "tts_too_long": "テキストが長すぎて音声再生できません。短くしてください。",
        "show_pron": "発音と音声を表示",
        "tip": "ヒント：入力は短く具体的にするほど良い結果が得られます。",
        "hero_langs": "北京語 · 広東語 · 韓国語 · 英語 · 日本語",
        "hero_pill_reply": "返信コーチ",
        "hero_pill_tone": "トーン分析",
        "hero_pill_history": "ローカル履歴",
        "nav_home": "ホーム",
        "mode_say": "より自然に言い換え",
        "mode_say_sub": "文をもっと自然な表現に",
        "mode_mean": "どういう意味？",
        "mode_mean_sub": "隠れた意味やトーンを解説",
        "mode_kpop": "歌詞・ドラマの文脈",
        "mode_kpop_sub": "K-pop / ドラマ / ネットスラングを解説",
        "mode_coach": "AIチャットコーチ",
        "mode_coach_sub": "文化的に適切な返信を提案",
        "feature_translate": "翻訳",
        "feature_grammar": "文法",
        "feature_grammar_sub": "レベルに合わせて添削",
        "feature_natural": "自然な表現",
        "feature_natural_sub": "ネイティブらしく聞こえるように",
        "feature_vocab": "語彙",
        "feature_vocab_sub": "キーワード・フレーズを解説",
        "feature_course": "コース学習",
        "feature_course_sub": "日々のレッスンとドリル",
        "feature_tone": "トーン分析",
        "feature_tone_sub": "丁寧さ・フォーマルさ・直接性",
        "recommendations_nav": "おすすめ",
        "recommendations_title": "AI機能のおすすめ",
        "recommendations_sub": "言語目標と利用状況に合わせて、使うべき機能を提案します。",
        "recommendations_top_pick": "一番のおすすめ",
        "recommendations_score": "一致度",
        "recommendations_try": "試す",
        "recommendations_empty": "いくつかのタスクを完了すると、個別のおすすめが表示されます。",
        "recommendations_feedback": "おすすめは利用状況に応じて更新されます。新しい機能を試したあと、また確認してみてください。",
        "recommendation_coach_name": "AIチャットコーチ",
        "recommendation_coach_desc": "文化的な文脈に合う返信案、トーン分析、文化メモ、発音ガイドを確認できます。",
        "recommendation_pronunciation_name": "発音ガイド",
        "recommendation_pronunciation_desc": "各言語のネイティブ発音、ローマ字表記、音声読み上げを確認できます。",
        "recommendation_grammar_name": "文法添削",
        "recommendation_grammar_desc": "レベルに合う説明と再利用しやすい例文パターンで間違いを直します。",
        "recommendation_natural_name": "自然な表現",
        "recommendation_natural_desc": "翻訳っぽい文を、ネイティブが実際に送りそうな表現に整えます。",
        "recommendation_tone_name": "トーン分析",
        "recommendation_tone_desc": "送信前に、丁寧さ・冷たさ・フォーマルさ・親しみやすさを確認できます。",
        "recommendation_vocab_name": "語彙ビルダー",
        "recommendation_vocab_desc": "実際の会話から表現を保存し、自分だけのフレーズ集を育てます。",
        "recommendation_kpop_name": "K-pop / ドラマの文脈",
        "recommendation_kpop_desc": "歌詞、ドラマのセリフ、スラング、文化的な含意を理解できます。",
        "recommendation_conversation_memory_name": "会話記憶コーチ",
        "recommendation_conversation_memory_desc": "AIが前の流れを覚えたまま、自然な複数ターンの会話を続けられます。",
        "nav_history": "履歴",
        "nav_about": "このアプリについて",
        "what_can": "何ができる？",
        "what_can_v2": "あなたの異文化チャットアシスタント",
        "what_can_sub": "タスクを選び、言語・トーン・文化的文脈を整えましょう。",
        "not_social": "これはSNSではありません。",
        "back_home": "ホームに戻る",
        "input_text": "テキストを入力・ペースト",
        "run": "実行",
        "enter_text_translate": "翻訳するテキストを入力",
        "translate_btn": "翻訳",
        "source_language": "原文の言語",
        "language_of_text": "テキストの言語",
        "auto_detect": "自動検出",
        "working": "処理中...",
        "ai_call_failed": "AI呼び出しに失敗",
        "quota_guest_limit": "ゲストのプレビュー制限に達しました。ログインすると独自の1日割り当てが利用できます。",
        "quota_user_limit": "1日のAIアクション制限に達しました。明日再度お試しください。",
        "db_init_failed": "DB初期化に失敗",
        "history_save_failed": "履歴の保存に失敗",
        "detected_source": "検出された言語",
        "pronunciation_label": "発音",
        "playing_audio": "音声生成中...",
        "tts_not_supported": "この言語はTTSに対応していません。",
        "voice_input": "音声入力",
        "swap_unavailable_auto": "自動検出 — 交換不可",
        "upload_audio": "音声ファイルをアップロード",
        "transcribe": "文字起こし",
        "transcribing": "文字起こし中...",
        "ok": "完了",
        "stt_unavailable": "音声認識が利用できません。",
        "please_upload_audio_first": "音声ファイルを先にアップロードしてください。",
        "live_mic_note": "マイクで録音。",
        "direct_mic_note": "ここで録音すると、文字起こし結果が上のテキストボックスに入力されます。",
        "upload_audio_fallback": "音声ファイルで代用",
        "phonetic_input_tip": "ピンイン、粤拼、韓国語ローマ字、日本語ローマ字の入力に対応。",
        "start_recording": "録音開始",
        "stop_recording": "停止",
        "mic_not_installed": "streamlit-mic-recorderがインストールされていません。",
        "relation_mode": "関係性 / スタイル",
        "ctx_kpop": "K-pop歌詞",
        "ctx_kdrama": "韓国ドラマ",
        "ctx_cantodrama": "広東語ドラマ",
        "ctx_cdrama": "中国ドラマ",
        "ctx_eng_tv": "英語の映像作品",
        "ctx_inet": "ネットスラング",
        "ctx_pop": "ポップカルチャー",
        "context_type": "コンテキスト",
        "enter_text_correct": "添削するテキストを入力",
        "correct_btn": "文法を添削",
        "learner_level": "学習者レベル",
        "enter_text_natural": "下書きを入力",
        "desired_tone": "希望のトーン",
        "suggest_btn": "提案",
        "enter_text_vocab": "語彙を解説するテキストを入力",
        "max_items": "最大項目数",
        "explain_vocab_btn": "語彙を解説",
        "enter_text_tone": "トーン分析するテキストを入力",
        "analyze_tone_btn": "トーンを分析",
        "history_title": "履歴",
        "history_sub": "最近のタスク",
        "filter_mode": "モード",
        "filter_source": "原文言語",
        "filter_target": "ターゲット言語",
        "filter_persona": "ペルソナ",
        "search_in": "履歴を検索",
        "show_last": "最新N件を表示",
        "history_load_failed": "履歴の読み込みに失敗",
        "no_history": "履歴がまだありません。",
        "input_label": "入力",
        "output_label": "出力",
        "model_info_prefix": "モデル",
        "tokens_label": "トークン",
        "latency_label": "レイテンシ",
        "about_title": "このアプリについて",
        "about_desc": "TriLingua Bridge v2 — 異文化コミュニケーションコーチ。",
        "enter_text_warn": "先にテキストを入力してください。",
        "naturalness_score_title": "自然さスコア",
        "naturalness_verdict": "判定",
        "naturalness_score": "スコア",
        "naturalness_reason": "理由",
        "naturalness_suggestion": "より自然な表現",
        "verdict_natural": "自然",
        "verdict_somewhat_natural": "やや自然",
        "verdict_machine_translated": "翻訳調",
        "region_mode": "地域 / 文化モード",
        "region_mainland_cn": "中国本土モード",
        "region_hk_yue": "香港広東語モード",
        "region_korean": "韓国語モード",
        "region_au_en": "オーストラリア英語モード",
        "region_us_en": "アメリカ英語モード",
        "region_jp": "日本語モード",
        "screenshot_mode": "スクリーンショット分析",
        "analyze_screenshot_btn": "スクショ分析",
        "upload_screenshot": "チャットのスクリーンショットをアップロード",
        "please_upload_image_first": "先に画像をアップロードしてください。",
        "screenshot_not_available": "スクリーンショット分析は利用できません。",
        "mode_coach_v2": "AIチャットコーチ",
        "mode_coach_sub_v2": "中国/香港/韓国/豪/米の文化に合わせた返信",
        "style_friend": "友人",
        "style_crush": "好意あり",
        "style_work": "仕事",
        "style_formal": "フォーマル",
        "style_cute": "可愛く",
        "style_cold": "やや冷たく",
        "style_kpop": "K-pop風",
        "style_hk": "香港ローカル風",
        "reply_options": "返信オプション",
        "tone_notes": "トーンの解説",
        "cultural_notes": "文化的解説",
        "suggested_best_reply": "おすすめ返信",
        "why_this_works": "この返信が良い理由",
        "pronunciation": "発音",
        "examples": "例文",
        "corrected_version": "修正版",
        "notes": "解説",
        "clean_translation": "自然な翻訳",
        "summary": "要約",
        "recommended_understanding": "推奨される解釈",
        "tone_summary": "トーン要約",
        "intent": "意図",
        "tips": "アドバイス",
        "better_version": "より自然な表現",
        "items": "項目",
        "key_phrases": "重要フレーズ",
        "slang_pop_culture": "スラング・ポップカルチャー",
        "suggestions": "提案",
        "try_examples": "例を試す：",
        "workflow_1": "実際のメッセージや状況をペースト",
        "workflow_2": "言語・地域・トーン・タスクを選択",
        "workflow_3": "AIが選択肢と解説を生成",
        "workflow_4": "役立つ結果をローカル履歴に保存",
        "recent_activity": "最近のアクティビティ",
        "page_tip_title": "このページの使い方",
        "say_translate_tip": "メッセージをペーストし、原文とターゲット言語を選んで実行。迷ったら例をどうぞ。",
        "coach_mean_tip": "実際のチャットの一文や状況を使ってください。トーンや隠れた意味を解説し、返信を準備します。",
        "grammar_tip": "一文か短いパラグラフをペースト。レベルを選ぶと難しすぎない添削結果になります。",
        "natural_tip": "翻訳調や不自然に感じる文をペーストし、希望のトーンを選んでください。",
        "vocab_tip": "単語、歌詞、宿題の文章、チャットメッセージをペースト。役立つ表現を解説します。",
        "tone_tip": "送信前に文をペースト。冷たすぎ・失礼・丁寧・フォーマル・自然かをチェック。",
        "start_tip_title": "10秒でスタート",
        "start_tip_body": "ユーザー名を入力すると履歴を保存できます。ゲストのまま即試すことも可能。",
        "status_workspace": "ワークスペース",
        "status_learning_path": "学習パス",
        "status_ai": "AI状態",
        "provider_ready": "利用可能",
        "provider_auto_ready": "自動フォールバック準備完了",
        "provider_missing_key": "APIキー未設定",
        "quick_coach": "チャットコーチを開く",
        "quick_translate": "翻訳",
        "quick_history": "履歴",
        "advanced_settings": "詳細設定",
        "workspace_ready": "ワークスペース準備完了",
        "result_actions": "次のアクション",
        "new_conversation": "🔄 新しい会話",
        "conversation_reset": "言語または地域が変更されたため、会話をリセットしました。",
        "download_result": "結果をダウンロード",
        "copy_ready": "コピー用テキスト",
        "group_chat": "チャットと返信",
        "group_understand": "コンテンツを理解",
        "group_learning": "学習ツール",
        "group_language_tools": "言語ツール",
        "group_workspace": "ワークスペース",
        "workspace_nav": "ワークスペース",
        "workspace_assets": "あなたのアセット",
        "login_required_title": "ログインが必要です",
        "guest_no_save_note": "ゲストモードはお試し用です。履歴・復習カード・単語帳を保存するにはアカウントでログインしてください。",
        "asset_history": "保存タスク",
        "asset_modes": "使用モード",
        "asset_latest": "最新",
        "asset_review": "復習カード",
        "asset_vocab": "単語帳アイテム",
        "asset_today": "今日のポイント",
        "asset_streak": "連続学習",
        "asset_top_mode": "よく使うモード",
        "save_review": "復習に保存",
        "saved_review": "復習に保存しました。",
        "save_failed": "保存に失敗",
        "add_vocab": "単語帳に追加",
        "saved_vocab": "単語帳に追加しました。",
        "review_book": "復習ノート",
        "vocab_bank": "単語帳",
        "learning_report": "学習レポート",
        "metric_today": "今日",
        "metric_week": "今週",
        "metric_streak": "連続",
        "metric_review": "復習",
        "review_title": "復習ノート",
        "review_sub": "保存した添削・返信・解説を復習カードとして見直せます。",
        "review_search": "復習カードを検索",
        "empty_review_title": "復習カードがまだありません",
        "empty_review_body": "AIタスクを実行後、結果の下にある「復習に保存」をクリックしてください。",
        "review_again": "もう一度練習",
        "vocab_title": "単語帳",
        "vocab_sub": "実際のタスクから作った自分だけのフレーズ集。",
        "vocab_term": "単語・フレーズ",
        "vocab_meaning": "意味・メモ",
        "vocab_example": "例文",
        "vocab_add_manual": "フレーズを追加",
        "vocab_term_required": "先に単語やフレーズを入力してください。",
        "vocab_search": "単語帳を検索",
        "empty_vocab_title": "単語帳がまだ空です",
        "empty_vocab_body": "手動で追加するか、語彙解説の結果から保存してください。",
        "report_title": "学習レポート",
        "report_sub": "何を練習したか、次に何をすべきかをひと目で確認。",
        "report_focus_title": "現在のフォーカス",
        "report_next_title": "おすすめ次のステップ",
        "report_next_body": "復習カード2枚を見直し、単語帳に1フレーズ追加、コースドリルを1つ完了。",
        "report_recent": "最近の学習シグナル",
        "course_title": "コース学習",
        "course_sub": "ツールを日常的な練習につなげるガイド付きパス。",
        "course_note_title": "コースの使い方",
        "course_note_body": "短いレッスンを選び、用意されたプロンプトで練習。役立つ結果をローカル履歴に保存。",
        "course_today": "今日のパス",
        "course_step_1": "ステップ1",
        "course_step_2": "ステップ2",
        "course_step_3": "ステップ3",
        "course_lesson_grammar": "実践的な文を一つ直す",
        "course_lesson_grammar_body": "間違い・修正文・再利用可能なパターンを学びます。",
        "course_lesson_natural": "自然な表現に改良",
        "course_lesson_natural_body": "翻訳調の文を実際に送れる表現に変えます。",
        "course_lesson_reply": "実際のチャットで使う",
        "course_lesson_reply_body": "学校・仕事・友人・デートに合った文化的に適切な返信を練習。",
        "course_practice_grammar": "文法を練習",
        "course_practice_natural": "自然表現を練習",
        "course_practice_reply": "チャット返信を練習",
        "course_drills": "集中ドリル",
        "course_drills_sub": "5分あれば繰り返せる短い練習。",
        "course_drill_vocab": "語彙ビルダー",
        "course_drill_vocab_title": "フレーズ集を作る",
        "course_drill_vocab_body": "宿題・チャット・歌詞・日常生活から表現を収集。",
        "course_drill_tone": "トーンチェック",
        "course_drill_tone_title": "送信前に確認",
        "course_drill_tone_body": "文が冷たく聞こえるか、丁寧か、直接的か、フォーマルか、親しみやすいかを学びます。",
        "course_practice_vocab": "語彙を練習",
        "course_practice_tone": "トーンを練習",
    },
}
