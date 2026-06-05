"""TriLingua Bridge — main app router.

Imports page rendering from modules/ and dispatches via st.session_state.page.
"""

import os

import streamlit as st
from dotenv import load_dotenv

from ui_helper import inject_css, t, TEXTS
from db_helper import init_db, ensure_history_columns
from modules.styles import inject_product_css
from modules.pages import (
    init_state,
    is_demo_mode,
    ui_text,
    render_home_dashboard,
    render_say_translate_page,
    render_mean_coach_kpop_page,
    render_lessons_page,
    render_review_page,
    render_vocab_bank_page,
    render_learning_report_page,
    render_grammar_page,
    render_natural_page,
    render_vocabulary_page,
    render_tone_page,
    render_history_page,
    render_about_page,
)

load_dotenv()

st.set_page_config(
    page_title="TriLingua Bridge",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()
inject_product_css()

init_state()

# ── Database ─────────────────────────────────────
try:
    init_db()
    ensure_history_columns()
except Exception as e:
    st.warning(f"{t('db_init_failed')}: {e}")

# ── Demo mode banner ─────────────────────────────
if is_demo_mode():
    st.info(
        ui_text(
            "demo_mode_banner",
            "Demo deployment — data resets when the app restarts. Please do not use real passwords.",
        ),
        icon="ℹ️",
    )

# ── Page routing ─────────────────────────────────
page = st.session_state.page
username = st.session_state.username

if page != "Home" and not username:
    st.session_state.page = "Home"
    st.rerun()

if page == "Home":
    render_home_dashboard()

elif page in ["Say", "Translate"]:
    render_say_translate_page(page)

elif page in ["Mean", "Coach", "Kpop"]:
    render_mean_coach_kpop_page(page)

elif page == "Lessons":
    render_lessons_page()

elif page == "Review":
    render_review_page(username)

elif page == "Vocab Bank":
    render_vocab_bank_page(username)

elif page == "Report":
    render_learning_report_page(username)

elif page == "Grammar":
    render_grammar_page()

elif page == "Natural":
    render_natural_page()

elif page == "Vocabulary":
    render_vocabulary_page()

elif page == "Tone":
    render_tone_page()

elif page == "History":
    render_history_page(username)

elif page == "About":
    render_about_page()

st.caption("© 2026 TriLingua Bridge")
