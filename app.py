import os
import time
from dotenv import load_dotenv
import streamlit as st

from helpers.db import init_db, insert_history, fetch_history
from helpers.ai_helper import (
    translate_text,
    correct_grammar,
    suggest_natural_expression,
    explain_vocabulary,
    analyze_tone,
)

load_dotenv()
init_db()

st.set_page_config(page_title="TriLingua Bridge", layout="centered")

APP_TITLE = "TriLingua Bridge"
LANG_OPTIONS = {
    "Chinese (中文)": "zh",
    "Korean (한국어)": "ko",
    "English": "en",
}

def lang_label(code):
    for k, v in LANG_OPTIONS.items():
        if v == code:
            return k
    return code

st.title(APP_TITLE)
st.caption("An AI language tool for Chinese and Korean speakers to learn Korean, Chinese, and English.")

# Sidebar - language pairing
st.sidebar.header("Learning Preferences")

native_choice = st.sidebar.selectbox(
    "I speak (Native language)",
    ["Chinese (中文)", "Korean (한국어)"],
    index=0
)
native_lang = LANG_OPTIONS[native_choice]

if native_lang == "zh":
    target_choices = ["Korean (한국어)", "English"]
else:
    target_choices = ["Chinese (中文)", "English"]

target_choice = st.sidebar.selectbox("I want to learn (Target language)", target_choices, index=0)
target_lang = LANG_OPTIONS[target_choice]

# Determine source for translation page (auto-detect optional)
source_choice = st.sidebar.selectbox(
    "Source language for translation",
    [native_choice, target_choice, "Auto-detect"],
    index=0
)
source_lang = LANG_OPTIONS.get(source_choice, "auto")

st.sidebar.info(
    "Tip: Explanations will primarily use your native language, while examples and rewrites use the target language."
)

tabs = st.tabs([
    "Translate",
    "Grammar",
    "Natural Expression",
    "Vocabulary",
    "Tone",
    "History"
])

# Translate Tab
with tabs[0]:
    st.subheader("Text Translation")
    text = st.text_area("Enter text to translate", height=150)
    col1, col2 = st.columns(2)
    with col1:
        temperature = st.slider("Creativity (temperature)", 0.0, 1.0, 0.2, 0.1)
    with col2:
        run_btn = st.button("Translate")
    if run_btn:
        if not text.strip():
            st.warning("Please enter some text.")
        else:
            start = time.time()
            result, usage = translate_text(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                native_lang=native_lang,
                temperature=temperature
            )
            latency_ms = int((time.time() - start) * 1000)
            st.write(result)
            insert_history(
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

# Grammar Tab
with tabs[1]:
    st.subheader("Grammar Correction")
    st.caption("Paste your sentence or paragraph in the target language.")
    text = st.text_area("Enter text to correct", height=150)
    col1, col2 = st.columns(2)
    with col1:
        level = st.selectbox("Learner level", ["Beginner", "Intermediate", "Advanced"], index=1)
    with col2:
        run_btn = st.button("Correct Grammar")
    if run_btn:
        if not text.strip():
            st.warning("Please enter some text.")
        else:
            start = time.time()
            result, usage = correct_grammar(
                text=text,
                target_lang=target_lang,
                native_lang=native_lang,
                level=level.lower()
            )
            latency_ms = int((time.time() - start) * 1000)
            st.write(result)
            insert_history(
                feature="grammar",
                source_lang=target_lang,  # assume input is in target for grammar correction
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

# Natural Expression Tab
with tabs[2]:
    st.subheader("Natural Expression Suggestions")
    st.caption("Get more natural, native-like phrasing in the target language.")
    text = st.text_area("Enter text for natural expression suggestions", height=150)
    col1, col2 = st.columns(2)
    with col1:
        tone_pref = st.selectbox("Desired tone", ["Neutral", "Polite", "Casual", "Formal"], index=0)
    with col2:
        run_btn = st.button("Suggest")
    if run_btn:
        if not text.strip():
            st.warning("Please enter some text.")
        else:
            start = time.time()
            result, usage = suggest_natural_expression(
                text=text,
                target_lang=target_lang,
                native_lang=native_lang,
                tone_preference=tone_pref.lower()
            )
            latency_ms = int((time.time() - start) * 1000)
            st.write(result)
            insert_history(
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

# Vocabulary Tab
with tabs[3]:
    st.subheader("Vocabulary Explanation")
    st.caption("Get key words/phrases explained with examples and usage notes.")
    text = st.text_area("Enter text to extract and explain vocabulary", height=150)
    col1, col2 = st.columns(2)
    with col1:
        max_items = st.slider("Max items", 3, 10, 5, 1)
    with col2:
        run_btn = st.button("Explain Vocabulary")
    if run_btn:
        if not text.strip():
            st.warning("Please enter some text.")
        else:
            start = time.time()
            result, usage = explain_vocabulary(
                text=text,
                target_lang=target_lang,
                native_lang=native_lang,
                max_items=max_items
            )
            latency_ms = int((time.time() - start) * 1000)
            st.write(result)
            insert_history(
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

# Tone Tab
with tabs[4]:
    st.subheader("Tone Analysis")
    st.caption("Detect tone (polite, casual, formal) and get rewrites.")
    text = st.text_area("Enter text to analyze tone", height=150)
    col1, col2 = st.columns(2)
    with col1:
        lang_for_tone = st.selectbox("Language of the text", [target_choice, native_choice, "English"], index=0)
    with col2:
        run_btn = st.button("Analyze Tone")
    if run_btn:
        if not text.strip():
            st.warning("Please enter some text.")
        else:
            lang_code = LANG_OPTIONS.get(lang_for_tone, target_lang)
            start = time.time()
            result, usage = analyze_tone(
                text=text,
                lang=lang_code,
                native_lang=native_lang
            )
            latency_ms = int((time.time() - start) * 1000)
            st.write(result)
            insert_history(
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

# History Tab
with tabs[5]:
    st.subheader("Learning History")
    colf1, colf2, colf3 = st.columns(3)
    with colf1:
        f_feature = st.selectbox("Feature", ["All", "translate", "grammar", "natural", "vocabulary", "tone"], index=0)
    with colf2:
        f_source = st.selectbox("Source", ["All", "auto", "zh", "ko", "en"], index=0)
    with colf3:
        f_target = st.selectbox("Target", ["All", "zh", "ko", "en"], index=0)
    search = st.text_input("Search in input/output")
    limit = st.slider("Show last N records", 10, 200, 50, 10)
    refresh = st.button("Refresh history")

    feature_filter = None if f_feature == "All" else f_feature
    src_filter = None if f_source == "All" else f_source
    tgt_filter = None if f_target == "All" else f_target

    rows = fetch_history(
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
            st.write(f"[{r['timestamp']}] {r['feature']} | {r['source_lang']} -> {r['target_lang']}")
            with st.expander("Input"):
                st.write(r["user_input"])
            with st.expander("Output"):
                st.write(r["ai_output"])
            st.caption(f"Model: {r.get('model')}, Tokens (in/out): {r.get('tokens_input')}/{r.get('tokens_output')}, Latency: {r.get('latency_ms')} ms")
            st.divider()

st.caption("© 2026 TriLingua Bridge")