"""
dashboard.py — AI Grid Orchestrator Live Dashboard
=====================================================
UNIFIED SHELL — loads state-specific panels from the panels/ folder.

Each teammate owns their own panel file:
  • Gary  → panels/maine.py   (ISO-NE data)
  • Ibrahima → panels/texas.py   (ERCOT data)

This file is the thin router. You should RARELY need to edit it.
Adding a new state = adding a file in panels/ and one line in panels/__init__.py.

Run:
    streamlit run dashboard.py

PRD Feature 5: "Built to demo in under 3 minutes."
"""

import importlib
import streamlit as st
import time

from panels import STATE_PANELS
from panels.shared import SHARED_CSS

# ──────────────────────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Grid Orchestrator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# Inject shared CSS (used by all panels)
# ──────────────────────────────────────────────────────────────
st.markdown(SHARED_CSS, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# Sidebar — shared across all states
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ AI Grid Orchestrator")
    st.markdown("**Real-time grid monitoring & autonomous load control**")
    st.markdown("---")

    # State selector — built dynamically from the registry
    state_labels = list(STATE_PANELS.keys())
    state = st.radio("Select Grid Region", state_labels, index=0)

    # Load the selected panel module
    panel_module_name = STATE_PANELS[state]
    panel = importlib.import_module(panel_module_name)

    # Show state-specific thresholds in the sidebar
    if hasattr(panel, "get_sidebar_info"):
        info = panel.get_sidebar_info()
        st.markdown("---")
        st.markdown(f"### {info.get('thresholds_title', 'Thresholds')}")
        for rule in info.get("rules", []):
            st.markdown(f"- {rule}")

    st.markdown("---")
    auto_refresh = st.checkbox("🔄 Auto-refresh (60s)", value=True)
    if st.button("🔃 Refresh Now"):
        st.rerun()

    st.markdown("---")
    st.markdown(
        "<div style='color: #64748b; font-size: 0.75rem;'>"
        "AI Grid Orchestrator v0.1.0<br>"
        "Gary Gonzalez & Ibrahima Diallo<br>"
        "Pursuit Fellowship 2026"
        "</div>",
        unsafe_allow_html=True,
    )

# ──────────────────────────────────────────────────────────────
# Main content — delegate to the selected panel's render()
# ──────────────────────────────────────────────────────────────
panel.render()

# ──────────────────────────────────────────────────────────────
# Auto-refresh
# ──────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(60)
    st.rerun()
