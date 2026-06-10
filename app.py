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


# ── PWA injection ─────────────────────────────────
def inject_pwa_tags():
    """Inject PWA manifest link, meta tags, and service worker registration."""
    import streamlit as st

    js = """
<script>
(function() {
    // ── Manifest link ──
    var link = document.createElement('link');
    link.rel = 'manifest';
    link.href = '/manifest.json';
    document.head.appendChild(link);

    // ── Apple / iOS meta tags ──
    var tags = {
        'apple-mobile-web-app-capable': 'yes',
        'apple-mobile-web-app-status-bar-style': 'default',
        'apple-mobile-web-app-title': 'TriLingua Bridge',
        'mobile-web-app-capable': 'yes',
        'application-name': 'TriLingua Bridge',
        'theme-color': '#2563eb',
    };
    for (var name in tags) {
        var m = document.createElement('meta');
        if (name.indexOf('apple') !== -1 || name.indexOf('mobile') !== -1 || name === 'application-name') {
            m.setAttribute('name', name);
        } else {
            m.setAttribute('name', name);
        }
        m.content = tags[name];
        document.head.appendChild(m);
    }

    // ── Apple touch icon ──
    var appleIcon = document.createElement('link');
    appleIcon.rel = 'apple-touch-icon';
    appleIcon.href = '/icon-192.png';
    document.head.appendChild(appleIcon);

    // ── Service worker registration ──
    // Skip on Streamlit Cloud (no static file serving for /sw.js)
    if ('serviceWorker' in navigator && !window.location.hostname.includes('streamlit.app')) {
        navigator.serviceWorker.register('/sw.js').catch(function() {
            // Silently fail if SW not available (e.g. direct Streamlit access)
        });
    }
})();
</script>
"""
    st.markdown(js, unsafe_allow_html=True)


st.set_page_config(
    page_title="TriLingua Bridge",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── PWA manifest & service worker injection ─────────
inject_pwa_tags()
# ── end PWA ──────────────────────────────────────────

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
