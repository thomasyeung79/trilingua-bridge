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

APP_TITLE = "TriLingua Bridge"
APP_SUBTITLE = "Learn Chinese, Korean, and English with AI"

LANG_OPTIONS = {
    "Chinese (中文)": "zh",
    "Korean (한국어)": "ko",
    "English": "en",
}
LANG_LABEL_BY_CODE = {v: k for k, v in LANG_OPTIONS.items()}


# ---------------- UI Helpers ----------------
def inject_css():
    st.markdown(
        """
        <style>
        :root{
            --bg-soft:#f6f8fb;
            --bg-hero: linear-gradient(135deg, #e7f3ff 0%, #f9f5ff 100%);
            --card:#ffffff;
            --primary:#6b8afd; /* blue-violet */
            --accent:#00c2a8;  /* teal */
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
        .block-container{ max-width: 980px; padding-top: 1rem; padding-bottom: 3rem; }

        /* Sidebar */
        [data-testid="stSidebar"]{
            background: #ffffff;
            border-right: 1px solid var(--border);
        }
        [data-testid="stSidebar"] .sidebar-content { padding: 1rem 0.75rem; }
        .sb-title{
            font-weight: 700; font-size: 1.05rem; color: var(--text); margin-bottom: 0.25rem;
        }
        .sb-sub{ color: var(--muted); font-size: 0.88rem; margin-bottom: 0.5rem; }

        /* Hero */
        .hero{
            background: var(--bg-hero);
            border: 1px solid var(--border);
            border-radius: 22px;
            padding: 28px 24px;
            box-shadow: var(--shadow);
            margin-bottom: 18px;
        }
        .hero h1{
            margin: 0; padding: 0;
            font-size: 2.0rem; line-height: 1.2;
            letter-spacing: -0.005em;
        }
        .hero p.sub{
            color: var(--muted);
            font-size: 1.05rem;
            margin: 6px 0 0 0;
        }

        /* Feature grid */
        .grid{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 14px;
        }
        @media (max-width: 950px){
            .grid{ grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .hero h1{ font-size: 1.7rem; }
        }
        @media (max-width: 640px){
            .grid{ grid-template-columns: 1fr; }
            .block-container{ padding-left: 0.5rem; padding-right: 0.5rem; }
            .hero{ padding: 22px 16px; }
        }

        /* Cards */
        .card{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 16px 16px;
            box-shadow: var(--shadow);
        }
        .card-header{
            display: flex; align-items: center; gap: 10px; margin-bottom: 6px;
        }
        .card-title{
            font-weight: 700; color: var(--text);
        }
        .card-sub{ color: var(--muted); font-size: 0.92rem; margin-top: 2px; }

        /* Colored accents */
        .accent-blue{ border-left: 6px solid #6b8afd; }
        .accent-green{ border-left: 6px solid #10b981; }
        .accent-purple{ border-left: 6px solid #a78bfa; }
        .accent-yellow{ border-left: 6px solid #f59e0b; }
        .accent-pink{ border-left: 6px solid #ec4899; }

        /* Buttons-as-cards */
        .card-btn{
            background: #ffffff; border: 1px solid var(--border);
            border-radius: var(--radius); padding: 16px;
            text-align: left; width: 100%;
        }
        .card-btn:hover{
            border-color: #b9c1ff; box-shadow: 0 0 0 4px rgba(107,138,253,0.15);
        }
        .card-icon{ font-size: 1.25rem; }
        .card-headline{ font-weight: 700; margin-left: 8px; }

        /* Input/Output areas */
        div[data-testid="stTextArea"] textarea{
            background: var(--input-bg);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
        }
        .io-section{ margin-top: 8px; }
        .input-wrap{ background: var(--input-bg); border: 1px dashed #d1d5db; border-radius: var(--radius); padding: 10px 12px; }
        .output-wrap{ background: var(--output-bg); border: 1px solid var(--border); border-radius: var(--radius); padding: 12px 14px; }

        /* Expanders */
        [data-testid="stExpander"]{
            background: #ffffff; border-radius: var(--radius-sm); border: 1px solid var(--border);
        }
        [data-testid="stExpander"] details{ padding: 6px 10px; }

        /* Small badges */
        .badge{
            display: inline-block;
            padding: 2px 8px;
            font-size: 0.78rem;
            color: #0f172a; background: #eef2ff;
            border: 1px solid #dbeafe; border-radius: 999px;
            margin-right: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def card(title: str, content=None, accent: str = "blue"):
    color_class = {
        "blue":"accent-blue",
        "green":"accent-green",
        "purple":"accent-purple",
        "yellow":"accent-yellow",
        "pink":"accent-pink",
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

def feature_card(icon: str, title: str, desc: str, target_label: str, key: str):
    # Button that looks like a card; sets sidebar radio to target page and reruns
    clicked = st.button(
        f"{icon}  {title}\n\n{desc}",
        key=key,
        use_container_width=True,
        type="secondary",
        help=f"Open {title}",
    )
    if clicked:
        st.session_state["nav_radio"] = target_label
        st.experimental_rerun()

def now_ms() -> int:
    return int(time.time() * 1000)


inject_css()

# ---------------- Auth (username) ----------------
def require_login() -> str:
    if "username" not in st.session_state:
        st.session_state.username = ""
    st.sidebar.markdown('<div class="sb-title">Account</div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sb-sub">Each user only sees their own data.</div>', unsafe_allow_html=True)
    ucol1, ucol2 = st.sidebar.columns([3, 1])
    with ucol1:
        username_input = st.text_input("Username", value=st.session_state.username, key="username_input")
    with ucol2:
        login_clicked = st.button("Login", use_container_width=True)
    if login_clicked:
        st.session_state.username = username_input.strip()
    if st.session_state.username:
        st.sidebar.success(f"Logged in: {st.session_state.username}")
        if st.sidebar.button("Log out", use_container_width=True):
            st.session_state.username = ""
            st.experimental_rerun()
        return st.session_state.username
    else:
        hero(APP_TITLE, APP_SUBTITLE)
        st.caption("Please log in with a username to use the app.")
        st.stop()

username = require_login()

# ---------------- Sidebar Preferences + Navigation ----------------
st.sidebar.markdown('<div class="sb-title">Learning Preferences</div>', unsafe_allow_html=True)
native_choice = st.sidebar.selectbox(
    "I speak (Native language)",
    ["Chinese (中文)", "Korean (한국어)"],
    index=0,
    key="native_choice",
)
native_lang = LANG_OPTIONS[native_choice]
target_choices = ["Korean (한국어)", "English"] if native_lang == "zh" else ["Chinese (中文)", "English"]
target_choice = st.sidebar.selectbox(
    "I want to learn (Target language)",
    target_choices,
    index=0,
    key="target_choice",
)
target_lang = LANG_OPTIONS[target_choice]

st.sidebar.markdown("---")
st.sidebar.markdown('<div class="sb-title">Navigation</div>', unsafe_allow_html=True)
PAGES: List[Tuple[str, str]] = [
    ("Home", "🏠 Home"),
    ("Chat Assistant", "💬 Chat Assistant"),
    ("Translate", "🌐 Translation"),
    ("Grammar", "✍️ Grammar"),
    ("Natural Expression", "🎯 Natural Expression"),
    ("Vocabulary", "📚 Vocabulary"),
    ("Tone", "🗣️ Tone"),
    ("History", "🕘 History"),
    ("About", "ℹ️ About"),
]
labels = [label for _, label in PAGES]
default_index = 0
selected_label = st.sidebar.radio("Go to", labels, index=st.session_state.get("nav_index", default_index), key="nav_radio")
# Map label to page id
current_page = next(pid for pid, lab in PAGES if lab == selected_label)
st.session_state["nav_index"] = labels.index(selected_label)

st.sidebar.info("Tip: Explanations use your native language; examples and rewrites use the target language.")

# ---------------- Pages ----------------

if current_page == "Home":
    hero(APP_TITLE, APP_SUBTITLE)
    section_header("What can you do here?", "Practice, translate, refine writing, and track your learning.")

    # Feature cards (grid)
    st.markdown('<div class="grid">', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        feature_card("💬", "Chat Reply Assistant", "Translate, learn key words, and get natural/polite/casual replies.", "💬 Chat Assistant", key="fc_chat")
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        feature_card("🌐", "Translation", "Fast, clear translation between Chinese, Korean, and English.", "🌐 Translation", key="fc_translation")
        st.markdown('</div>', unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        feature_card("✍️", "Grammar Correction", "Fix grammar and spacing with short explanations and examples.", "✍️ Grammar", key="fc_grammar")
        st.markdown('</div>', unsafe_allow_html=True)

    c4, c5, _ = st.columns(3)
    with c4:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        feature_card("🎯", "Natural Expression", "Sound more native with tone-aware rewrites.", "🎯 Natural Expression", key="fc_natural")
        st.markdown('</div>', unsafe_allow_html=True)
    with c5:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        feature_card("🕘", "Learning History", "Review your past work by feature and language.", "🕘 History", key="fc_history")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

elif current_page == "Chat Assistant":
    section_header("Chat Reply Assistant 💬", "Type a message (in Korean, Chinese, or English). Get translation, key vocabulary, and multiple reply styles.")
    # Input area
    with st.container():
        lang_select = st.selectbox("Message language", ["Auto-detect", "Chinese (中文)", "Korean (한국어)", "English"], index=0)
        source_lang = "auto" if lang_select == "Auto-detect" else LANG_OPTIONS[lang_select]
        st.markdown('<div class="input-wrap io-section">', unsafe_allow_html=True)
        text = st.text_area("Your message", height=140, key="chat_message")
        st.markdown('</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            temperature = st.slider("Creativity (temperature)", 0.0, 1.0, 0.3, 0.1, key="chat_temp")
        with c2:
            run_btn = st.button("Generate Reply", use_container_width=True)

    if run_btn:
        if not text.strip():
            st.warning("Please enter a message.")
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

            st.markdown('<div class="output-wrap io-section">', unsafe_allow_html=True)
            if isinstance(result_dict, dict) and result_dict:
                det = result_dict.get("detected_source_lang")
                trans = result_dict.get("translation")
                vocab = result_dict.get("vocabulary", [])
                r_nat = result_dict.get("reply_natural")
                r_pol = result_dict.get("reply_polite")
                r_cas = result_dict.get("reply_casual")

                if det:
                    card("Detected source language", LANG_LABEL_BY_CODE.get(det, det), accent="yellow")
                if trans:
                    card(f"Translation → {LANG_LABEL_BY_CODE.get(target_lang, target_lang)}", trans, accent="blue")

                if vocab:
                    st.markdown('<div class="card accent-green">', unsafe_allow_html=True)
                    st.markdown('<div class="card-header"><span class="card-title">Important vocabulary</span></div>', unsafe_allow_html=True)
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
                    card("Natural reply", r_nat, accent="purple")
                if r_pol:
                    card("Polite version", r_pol, accent="green")
                if r_cas:
                    card("Casual/friend version", r_cas, accent="pink")

                insert_history(
                    username=username,
                    feature="chat",
                    source_lang=det or source_lang,
                    target_lang=target_lang,
                    user_input=text,
                    ai_output=json.dumps(result_dict, ensure_ascii=False, indent=2),
                    extra={"note": "chat_assistant"},
                    tokens_input=usage.get("prompt_tokens"),
                    tokens_output=usage.get("completion_tokens"),
                    model=usage.get("model"),
                    latency_ms=latency_ms,
                )
                st.caption(f"Model: {usage.get('model')}, Tokens (in/out): {usage.get('prompt_tokens')}/{usage.get('completion_tokens')}, Latency: {latency_ms} ms")
            else:
                st.error("Failed to generate a structured reply. Please try again.")
            st.markdown('</div>', unsafe_allow_html=True)

elif current_page == "🌐 Translation" or current_page == "Translate":
    section_header("Translation 🌐", "Translate between Chinese, Korean, and English.")
    source_choice = st.selectbox("Source language", [native_choice, target_choice, "English", "Auto-detect"], index=0)
    source_lang = LANG_OPTIONS.get(source_choice, "auto")
    st.markdown('<div class="input-wrap io-section">', unsafe_allow_html=True)
    text = st.text_area("Enter text to translate", height=150, key="translate_text")
    st.markdown('</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        temperature = st.slider("Creativity (temperature)", 0.0, 1.0, 0.2, 0.1, key="translate_temp")
    with col2:
        run_btn = st.button("Translate", use_container_width=True)
    if run_btn:
        if not text.strip():
            st.warning("Please enter some text.")
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
            st.markdown('<div class="output-wrap io-section">', unsafe_allow_html=True)
            card("Translation", result, accent="blue")
            st.caption(f"Model: {usage.get('model')}, Tokens (in/out): {usage.get('prompt_tokens')}/{usage.get('completion_tokens')}, Latency: {latency_ms} ms")
            st.markdown('</div>', unsafe_allow_html=True)
            insert_history(
                username=username,
                feature="translate",
                source_lang=source_lang,
                target_lang=target_lang,
                user_input=text,
                ai_output=result,
                extra={"note": "translation"},
                tokens_input=usage.get("prompt_tokens"),
                tokens_output=usage.get("completion_tokens"),
                model=usage.get("model"),
                latency_ms=latency_ms
            )

elif current_page == "✍️ Grammar" or current_page == "Grammar":
    section_header("Grammar Correction ✍️", "Paste your sentence or paragraph in the target language.")
    st.markdown('<div class="input-wrap io-section">', unsafe_allow_html=True)
    text = st.text_area("Enter text to correct", height=150, key="grammar_text")
    st.markdown('</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        level = st.selectbox("Learner level", ["Beginner", "Intermediate", "Advanced"], index=1)
    with col2:
        run_btn = st.button("Correct Grammar", use_container_width=True)
    if run_btn:
        if not text.strip():
            st.warning("Please enter some text.")
        else:
            start = now_ms()
            result, usage = correct_grammar(
                text=text,
                target_lang=target_lang,
                native_lang=native_lang,
                level=level.lower()
            )
            latency_ms = now_ms() - start
            st.markdown('<div class="output-wrap io-section">', unsafe_allow_html=True)
            card("Correction", result, accent="green")
            st.caption(f"Model: {usage.get('model')}, Tokens (in/out): {usage.get('prompt_tokens')}/{usage.get('completion_tokens')}, Latency: {latency_ms} ms")
            st.markdown('</div>', unsafe_allow_html=True)
            insert_history(
                username=username,
                feature="grammar",
                source_lang=target_lang,
                target_lang=target_lang,
                user_input=text,
                ai_output=result,
                extra={"level": level},
                tokens_input=usage.get("prompt_tokens"),
                tokens_output=usage.get("completion_tokens"),
                model=usage.get("model"),
                latency_ms=latency_ms
            )

elif current_page == "🎯 Natural Expression" or current_page == "Natural Expression":
    section_header("Natural Expression 🎯", "Get more native-like phrasing with tone control.")
    st.markdown('<div class="input-wrap io-section">', unsafe_allow_html=True)
    text = st.text_area("Enter text for natural expression suggestions", height=150, key="natural_text")
    st.markdown('</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        tone_pref = st.selectbox("Desired tone", ["Neutral", "Polite", "Casual", "Formal"], index=0)
    with col2:
        run_btn = st.button("Suggest", use_container_width=True)
    if run_btn:
        if not text.strip():
            st.warning("Please enter some text.")
        else:
            start = now_ms()
            result, usage = suggest_natural_expression(
                text=text,
                target_lang=target_lang,
                native_lang=native_lang,
                tone_preference=tone_pref.lower()
            )
            latency_ms = now_ms() - start
            st.markdown('<div class="output-wrap io-section">', unsafe_allow_html=True)
            card("Suggestions", result, accent="purple")
            st.caption(f"Model: {usage.get('model')}, Tokens (in/out): {usage.get('prompt_tokens')}/{usage.get('completion_tokens')}, Latency: {latency_ms} ms")
            st.markdown('</div>', unsafe_allow_html=True)
            insert_history(
                username=username,
                feature="natural",
                source_lang=target_lang,
                target_lang=target_lang,
                user_input=text,
                ai_output=result,
                extra={"tone_preference": tone_pref},
                tokens_input=usage.get("prompt_tokens"),
                tokens_output=usage.get("completion_tokens"),
                model=usage.get("model"),
                latency_ms=latency_ms
            )

elif current_page == "📚 Vocabulary" or current_page == "Vocabulary":
    section_header("Vocabulary 📚", "Extract key words/phrases with examples and usage notes.")
    st.markdown('<div class="input-wrap io-section">', unsafe_allow_html=True)
    text = st.text_area("Enter text to extract and explain vocabulary", height=150, key="vocab_text")
    st.markdown('</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        max_items = st.slider("Max items", 3, 10, 5, 1, key="vocab_max")
    with col2:
        run_btn = st.button("Explain Vocabulary", use_container_width=True)
    if run_btn:
        if not text.strip():
            st.warning("Please enter some text.")
        else:
            start = now_ms()
            result, usage = explain_vocabulary(
                text=text,
                target_lang=target_lang,
                native_lang=native_lang,
                max_items=max_items
            )
            latency_ms = now_ms() - start
            st.markdown('<div class="output-wrap io-section">', unsafe_allow_html=True)
            card("Vocabulary", result, accent="yellow")
            st.caption(f"Model: {usage.get('model')}, Tokens (in/out): {usage.get('prompt_tokens')}/{usage.get('completion_tokens')}, Latency: {latency_ms} ms")
            st.markdown('</div>', unsafe_allow_html=True)
            insert_history(
                username=username,
                feature="vocabulary",
                source_lang="auto",
                target_lang=target_lang,
                user_input=text,
                ai_output=result,
                extra={"max_items": max_items},
                tokens_input=usage.get("prompt_tokens"),
                tokens_output=usage.get("completion_tokens"),
                model=usage.get("model"),
                latency_ms=latency_ms
            )

elif current_page == "🗣️ Tone" or current_page == "Tone":
    section_header("Tone Analysis 🗣️", "Detect tone (polite, casual, formal) and get rewrites.")
    lang_for_tone = st.selectbox("Language of the text", [target_choice, native_choice, "English"], index=0)
    st.markdown('<div class="input-wrap io-section">', unsafe_allow_html=True)
    text = st.text_area("Enter text to analyze tone", height=150, key="tone_text")
    st.markdown('</div>', unsafe_allow_html=True)
    run_btn = st.button("Analyze Tone", use_container_width=True)
    if run_btn:
        if not text.strip():
            st.warning("Please enter some text.")
        else:
            lang_code = LANG_OPTIONS.get(lang_for_tone, target_lang)
            start = now_ms()
            result, usage = analyze_tone(text=text, lang=lang_code, native_lang=native_lang)
            latency_ms = now_ms() - start
            st.markdown('<div class="output-wrap io-section">', unsafe_allow_html=True)
            card("Tone Analysis", result, accent="pink")
            st.caption(f"Model: {usage.get('model')}, Tokens (in/out): {usage.get('prompt_tokens')}/{usage.get('completion_tokens')}, Latency: {latency_ms} ms")
            st.markdown('</div>', unsafe_allow_html=True)
            insert_history(
                username=username,
                feature="tone",
                source_lang=lang_code,
                target_lang=lang_code,
                user_input=text,
                ai_output=result,
                extra={"analysis": "tone"},
                tokens_input=usage.get("prompt_tokens"),
                tokens_output=usage.get("completion_tokens"),
                model=usage.get("model"),
                latency_ms=latency_ms
            )

elif current_page == "🕘 History" or current_page == "History":
    section_header("Learning History 🕘", "Only your records are shown (user-isolated).")
    colf1, colf2, colf3 = st.columns(3)
    with colf1:
        f_feature = st.selectbox("Feature", ["All", "chat", "translate", "grammar", "natural", "vocabulary", "tone"], index=0)
    with colf2:
        f_source = st.selectbox("Source", ["All", "auto", "zh", "ko", "en"], index=0)
    with colf3:
        f_target = st.selectbox("Target", ["All", "zh", "ko", "en"], index=0)
    st.markdown('<div class="input-wrap io-section">', unsafe_allow_html=True)
    search = st.text_input("Search in input/output")
    st.markdown('</div>', unsafe_allow_html=True)
    limit = st.slider("Show last N records", 10, 200, 50, 10)
    st.markdown("---")

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
        st.info("No history yet.")
    else:
        for r in rows:
            title = f"{r['timestamp']} • {r['feature']} • {r['source_lang']} → {r['target_lang']}"
            st.markdown('<div class="output-wrap io-section">', unsafe_allow_html=True)
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
            st.caption(f"Model: {r.get('model')}, Tokens (in/out): {r.get('tokens_input')}/{r.get('tokens_output')}, Latency: {r.get('latency_ms')} ms")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

elif current_page == "ℹ️ About" or current_page == "About":
    section_header("About TriLingua Bridge ℹ️", "")
    st.write(
        "- AI tool for Chinese and Korean speakers to learn Korean, Chinese, and English.\n"
        "- All data is user-isolated by username. Set your username in the sidebar.\n"
        "- Inspired by modern learning apps with clean, friendly UI."
    )

st.caption("© 2026 TriLingua Bridge")
