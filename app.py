"""Streamlit app for local portfolio tracking and AI‑assisted trading."""

from pathlib import Path

import streamlit as st
from streamlit import config as _config

from components.nav import navbar
from ui.dashboard import render_dashboard
from ui.user_guide import render_user_guide

st.set_page_config(
    page_title="AI Assisted Trading",
    page_icon="🚀",  # optional, if you want an icon
    layout="wide",  # optional, choose your layout
    initial_sidebar_state="expanded",  # keep the sidebar visible on load
)

navbar(Path(__file__).name)

st.title("📊 Portfolio Dashboard")


def main() -> None:
    """Application entry point."""

    dashboard_tab, guide_tab = st.tabs(["Dashboard", "User Guide"])
    with dashboard_tab:
        render_dashboard()
    with guide_tab:
        render_user_guide()


if __name__ == "__main__":
    main()
