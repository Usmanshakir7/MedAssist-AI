"""Compatibility wrapper for the one-page MedAssistAI layout."""
from views.home import insights_section


def insights_page():
    import streamlit as st
    user = st.session_state["user"]
    insights_section(user["id"])
