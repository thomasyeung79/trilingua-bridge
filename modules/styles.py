"""Additional product styles for TriLingua Bridge (extracted from app.py)."""

PRODUCT_CSS = """
<style>
[data-testid="stSidebar"] {
    display: none;
}

[data-testid="collapsedControl"] {
    display: none;
}

.product-note {
    display: flex;
    gap: 12px;
    border: 1px solid rgba(37, 99, 235, 0.18);
    background: linear-gradient(135deg, rgba(239, 246, 255, 0.94), rgba(236, 253, 245, 0.78));
    border-radius: 8px;
    padding: 15px;
    margin: 14px 0;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.045);
}

.product-note-icon {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    background: #ffffff;
    flex: 0 0 32px;
}

.product-note-title {
    font-weight: 750;
    color: #111827;
    margin-bottom: 2px;
}

.product-note-body {
    color: #4b5563;
    line-height: 1.45;
    font-size: 0.92rem;
}

.workflow-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
    margin: 12px 0 18px;
}

.workflow-step {
    border: 1px solid rgba(148, 163, 184, 0.28);
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.9);
    padding: 14px;
    min-height: 98px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.045);
}

.workflow-number {
    width: 28px;
    height: 28px;
    border-radius: 999px;
    background: linear-gradient(135deg, #0f172a, #2563eb);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    margin-bottom: 8px;
}

.workflow-label {
    font-size: 0.88rem;
    line-height: 1.35;
    color: #374151;
    font-weight: 620;
}

.product-status-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
    margin: 14px 0 6px;
}

.product-status-card {
    border: 1px solid rgba(148, 163, 184, 0.28);
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.92);
    padding: 14px;
    min-height: 86px;
    box-shadow: 0 7px 18px rgba(15, 23, 42, 0.045);
}

.product-status-label {
    color: #6b7280;
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 6px;
}

.product-status-value {
    color: #111827;
    font-size: 1rem;
    font-weight: 760;
    line-height: 1.35;
}

.feature-group-title {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 24px 0 10px;
    color: #0f172a;
    font-weight: 820;
    font-size: 0.96rem;
}

.feature-group-title::before {
    content: "";
    width: 8px;
    height: 22px;
    border-radius: 999px;
    background: linear-gradient(180deg, #2563eb, #0f766e);
}

.course-card {
    border: 1px solid rgba(148, 163, 184, 0.28);
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.92);
    padding: 16px;
    min-height: 150px;
    box-shadow: 0 7px 18px rgba(15, 23, 42, 0.045);
    margin-bottom: 10px;
}

.course-kicker {
    color: #2563eb;
    font-size: 0.78rem;
    font-weight: 780;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.course-title {
    color: #0f172a;
    font-size: 1.02rem;
    font-weight: 820;
    line-height: 1.35;
    margin-bottom: 6px;
}

.course-body {
    color: #475569;
    font-size: 0.9rem;
    line-height: 1.5;
}

.workspace-rail {
    border: 1px solid rgba(148, 163, 184, 0.28);
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.86);
    box-shadow: 0 7px 18px rgba(15, 23, 42, 0.045);
    padding: 14px;
    margin-bottom: 12px;
}

.workspace-rail-title {
    color: #0f172a;
    font-size: 0.92rem;
    font-weight: 820;
    margin-bottom: 8px;
}

.asset-metric {
    border: 1px solid rgba(148, 163, 184, 0.24);
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 10px;
    background: rgba(255, 255, 255, 0.88);
}

.asset-metric-label {
    color: #64748b;
    font-size: 0.78rem;
    font-weight: 760;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.asset-metric-value {
    color: #0f172a;
    font-size: 1.35rem;
    font-weight: 850;
    margin-top: 2px;
}

@media (max-width: 760px) {
    .workflow-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 560px) {
    .product-status-grid {
        grid-template-columns: 1fr;
    }
}
</style>
"""


def inject_product_css():
    import streamlit as st
    st.markdown(PRODUCT_CSS, unsafe_allow_html=True)
