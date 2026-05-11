import os
import json
import time
from typing import Dict, Any
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

# ---------------- UI Helpers ----------------
def inject_css():
    st.markdown(
        """
        <style>
        .app-container {max-width: 960px; margin: 0 auto;}
        .card {
            background: white;
            border: 1px solid #E6E6E6;
            border-radius: 12px;
            padding: 16px 18px;
            margin: 10px 0 16px 0;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }
        .card h4 { margin: 0 0 8px 0; font-size: 1.02rem; }
        .muted { color: #666; font-size: 0.9rem; }
        .spacer { height: 8px; }
        .tight { margin-top: 2px; margin-bottom: 2px; }
        @media (max-width: 768px) {
            .card { padding: 14px 14px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def card(title: str, body=None):
    with st.container():
        st.markdown(f'<div class="card"><h4>{title}</h4>', unsafe_allow_html=True)
        if body is not None:
            st.write(body)
        st.markdown("</div>", unsafe_allow_html=True)

inject_css()

APP_TITLE = "TriLingua Bridge"
LANG_OPTIONS = {
    "Chinese (中文)": "zh",
    "Korean (한국어)": "ko",
    "English": "en",
}
LANG_LABEL_BY_CODE = {v: k for k, v in LANG_OPTIONS.items()}


def require_login() -> str:
    # Returns username or stops rendering until login
    if "username" not in st.session_state:
        st.session_state.username = ""
    st.sidebar.header("Account")
    st.sidebar.caption("User Account Isolation: Each user only sees their own data.")
    ucol1, ucol2 = st.sidebar.columns([3, 1])
    with ucol1:
        username_input = st.text_input("Username", value=st.session_state.username, key="username_input")
    with ucol2:
        login_clicked = st.button("Login", use_container_width=True)
    if login_clicked:
        st.session_state.username = username_input.strip()
    if st.session_state.username:
        st.sidebar.success(f"Logged in as: {st.session_state.username}")
        if st.sidebar.button("Log out"):
            st.session_state.username = ""
            st.experimental_rerun()
        return st.session_state.username
    else:
        st.title(APP_TITLE)
        st.caption("Please log in with a username to use the app.")
        st.stop()


# ---------------- Sidebar Navigation & Preferences ----------------
st.title(APP_TITLE)
st.caption("An AI language tool for Chinese and Korean speakers to learn Korean, Chinese, and English.")
username = require_login()

st.sidebar.header("Learning Preferences")
native_choice = st.sidebar.selectbox(
    "I speak (Native language)",
    ["Chinese (中文)", "Korean (한국어)"],
    index=0,
    key="native_choice",
)
native_lang = LANG_OPTIONS[native_choice]

if native_lang == "zh":
    target_choices = ["Korean (한국어)", "English"]
else:
    target_choices = ["Chinese (中文)", "English"]

target_choice = st.sidebar.selectbox(
    "I want to learn (Target language)",
    target_choices,
    index=0,
    key="target_choice",
)
target_lang = LANG_OPTIONS[target_choice]

st.sidebar.divider()
st.sidebar.header("Navigation")
PAGE_OPTIONS = [
    "Chat Assistant",
    "Translate",
    "Grammar",
    "Natural Expression",
    "Vocabulary",
    "Tone",
    "History",
    "About",
]
current_page = st.sidebar.radio("Go to", PAGE_OPTIONS, index=0)

st.sidebar.info("Tip: Explanations use your native language; examples/rewrites use the target language.")

def now_ms() -> int:
    return int(time.time() * 1000)

# ---------------- Pages ----------------

if current_page == "Chat Assistant":
    st.subheader("AI Chat Reply Assistant")
    st.caption("Type a message (in Korean, Chinese, or English). Get translation, vocab highlights, and ready-to-send replies.")

    with st.container():
        lang_select = st.selectbox(
            "Message language",
            ["Auto-detect", "Chinese (中文)", "Korean (한국어)", "English"],
            index=0,
        )
        if lang_select == "Auto-detect":
            source_lang = "auto"
        else:
            source_lang = LANG_OPTIONS[lang_select]

        text = st.text_area("Your message", height=140, key="chat_message")
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

            # Render results in cards
            if isinstance(result_dict, dict) and result_dict:
                det = result_dict.get("detected_source_lang")
                trans = result_dict.get("translation")
                vocab = result_dict.get("vocabulary", [])
                r_nat = result_dict.get("reply_natural")
                r_pol = result_dict.get("reply_polite")
                r_cas = result_dict.get("reply_casual")

                if det:
                    card("Detected source language", LANG_LABEL_BY_CODE.get(det, det))
                if trans:
                    card(f"Translation → {LANG_LABEL_BY_CODE.get(target_lang, target_lang)}", trans)

                if vocab:
                    with st.container():
                        st.markdown('<div class="card"><h4>Important vocabulary</h4>', unsafe_allow_html=True)
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
                    card("Natural reply", r_nat)
                if r_pol:
                    card("Polite version", r_pol)
                if r_cas:
                    card("Casual/friend version", r_cas)

                # Save full JSON result
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

elif current_page == "Translate":
    st.subheader("Text Translation")
    st.caption("Translate between Chinese, Korean, and English.")
    source_choice = st.selectbox(
        "Source language",
        [native_choice, target_choice, "English", "Auto-detect"],
        index=0
    )
    source_lang = LANG_OPTIONS.get(source_choice, "auto")
    text = st.text_area("Enter text to translate", height=150, key="translate_text")
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
            card("Translation", result)
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
            st.caption(f"Model: {usage.get('model')}, Tokens (in/out): {usage.get('prompt_tokens')}/{usage.get('completion_tokens')}, Latency: {latency_ms} ms")

elif current_page == "Grammar":
    st.subheader("Grammar Correction")
    st.caption("Paste your sentence or paragraph in the target language.")
    text = st.text_area("Enter text to correct", height=150, key="grammar_text")
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
            card("Correction", result)
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
            st.caption(f"Model: {usage.get('model')}, Tokens (in/out): {usage.get('prompt_tokens')}/{usage.get('completion_tokens')}, Latency: {latency_ms} ms")

elif current_page == "Natural Expression":
    st.subheader("Natural Expression Suggestions")
    st.caption("Get more natural, native-like phrasing in the target language.")
    text = st.text_area("Enter text for natural expression suggestions", height=150, key="natural_text")
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
            card("Suggestions", result)
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
            st.caption(f"Model: {usage.get('model')}, Tokens (in/out): {usage.get('prompt_tokens')}/{usage.get('completion_tokens')}, Latency: {latency_ms} ms")

elif current_page == "Vocabulary":
    st.subheader("Vocabulary Explanation")
    st.caption("Extract key words/phrases with examples and usage notes.")
    text = st.text_area("Enter text to extract and explain vocabulary", height=150, key="vocab_text")
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
            card("Vocabulary", result)
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
            st.caption(f"Model: {usage.get('model')}, Tokens (in/out): {usage.get('prompt_tokens')}/{usage.get('completion_tokens')}, Latency: {latency_ms} ms")

elif current_page == "Tone":
    st.subheader("Tone Analysis")
    st.caption("Detect tone (polite, casual, formal) and get rewrites.")
    lang_for_tone = st.selectbox("Language of the text", [target_choice, native_choice, "English"], index=0)
    text = st.text_area("Enter text to analyze tone", height=150, key="tone_text")
    col1, col2 = st.columns(2)
    with col1:
        pass
    with col2:
        run_btn = st.button("Analyze Tone", use_container_width=True)
    if run_btn:
        if not text.strip():
            st.warning("Please enter some text.")
        else:
            lang_code = LANG_OPTIONS.get(lang_for_tone, target_lang)
            start = now_ms()
            result, usage = analyze_tone(
                text=text,
                lang=lang_code,
                native_lang=native_lang
            )
            latency_ms = now_ms() - start
            card("Tone Analysis", result)
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
            st.caption(f"Model: {usage.get('model')}, Tokens (in/out): {usage.get('prompt_tokens')}/{usage.get('completion_tokens')}, Latency: {latency_ms} ms")

elif current_page == "History":
    st.subheader("Learning History")
    st.caption("Only your own records are shown (user-isolated).")
    colf1, colf2, colf3 = st.columns(3)
    with colf1:
        f_feature = st.selectbox("Feature", ["All", "chat", "translate", "grammar", "natural", "vocabulary", "tone"], index=0)
    with colf2:
        f_source = st.selectbox("Source", ["All", "auto", "zh", "ko", "en"], index=0)
    with colf3:
        f_target = st.selectbox("Target", ["All", "zh", "ko", "en"], index=0)
    search = st.text_input("Search in input/output")
    limit = st.slider("Show last N records", 10, 200, 50, 10)
    refresh = st.button("Refresh", use_container_width=True)

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
            st.markdown(f'<div class="card"><h4>{title}</h4>', unsafe_allow_html=True)
            with st.expander("Input"):
                st.write(r["user_input"])
            with st.expander("Output"):
                # Pretty print JSON if it's chat result
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
            st.markdown("</div>", unsafe_allow_html=True)

elif current_page == "About":
    st.subheader("About TriLingua Bridge")
    st.write(
        "- AI tool for Chinese and Korean speakers to learn Korean, Chinese, and English.\n"
        "- All data is user-isolated by username. Set your username in the sidebar."
    )

st.caption("© 2026 TriLingua Bridge")
