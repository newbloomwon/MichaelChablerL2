"""Streamlit dashboard for the Energy Grid project.

Run with:
    streamlit run streamlit_app/app.py
"""

import requests
import streamlit as st
import pandas as pd

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Energy Grid Dashboard",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ Energy Grid Dashboard")
st.caption("Real-time data from ERCOT (Texas) and ISO-NE (New England)")

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    api_host = st.text_input("API Base URL", value=API_BASE)
    auto_refresh = st.toggle("Auto-refresh (30 s)", value=False)
    if auto_refresh:
        st.info("Page will reload every 30 seconds.")
        st.markdown(
            '<meta http-equiv="refresh" content="30">',
            unsafe_allow_html=True,
        )


def fetch(endpoint: str) -> dict | None:
    try:
        resp = requests.get(f"{api_host}{endpoint}", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        st.error(f"API error ({endpoint}): {exc}")
        return None


# ─── ERCOT ───────────────────────────────────────────────────────────────────
st.header("🤠 ERCOT — Texas Grid")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Real-Time Prices")
    with st.spinner("Fetching…"):
        data = fetch("/ercot/prices")
    if data:
        st.json(data)

with col2:
    st.subheader("Load Forecast")
    with st.spinner("Fetching…"):
        data = fetch("/ercot/load-forecast")
    if data:
        st.json(data)

# ─── ISO-NE ──────────────────────────────────────────────────────────────────
st.header("🏔️ ISO-NE — New England Grid")

col3, col4, col5 = st.columns(3)

with col3:
    st.subheader("Real-Time LMP")
    with st.spinner("Fetching…"):
        data = fetch("/isone/lmp/realtime")
    if data:
        st.json(data)

with col4:
    st.subheader("Day-Ahead LMP")
    with st.spinner("Fetching…"):
        data = fetch("/isone/lmp/dayahead")
    if data:
        st.json(data)

with col5:
    st.subheader("System Demand")
    with st.spinner("Fetching…"):
        data = fetch("/isone/demand")
    if data:
        st.json(data)
