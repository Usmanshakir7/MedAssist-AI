import streamlit as st
import theme
from database.database import create_tables
from auth.login import login_page
from auth.signup import signup_page
from views.home import home_page

st.set_page_config(
    page_title="MedAssist AI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

create_tables()
theme.inject()

st.session_state.setdefault("logged_in", False)
st.session_state.setdefault("show_signup", False)
st.session_state.setdefault("ai_cache", {})
st.session_state.setdefault("recipe_cache", {})

if not st.session_state.logged_in:
    left, center, right = st.columns([1, 1.25, 1])
    with center:
        theme.app_header(False)
        st.markdown(
            '<div class="auth-tagline">Your reports. Your history. A clearer view of your health data.</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        if st.session_state.show_signup:
            signup_page()
            if st.button("Already have an account? Log in", use_container_width=True):
                st.session_state.show_signup = False
                st.rerun()
        else:
            login_page()
            if st.button("Create a new account", use_container_width=True):
                st.session_state.show_signup = True
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

user = st.session_state["user"]

with st.sidebar:
    theme.sidebar_brand()
    st.markdown(
        f'<div class="sidebar-user">🟢 {user.get("full_name", "User")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("### Navigate")
    st.markdown(
        """<div class="side-links">
        <a href="#home-section">⌂ Home</a>
        <a href="#upload-section">＋ Upload report</a>
        <a href="#reports-section">▤ Reports</a>
        <a href="#dashboard-section">◈ Dashboard</a>
        <a href="#insights-section">✦ AI Insights</a>
        <a href="#settings-section">⚙ Settings</a>
        </div>""",
        unsafe_allow_html=True,
    )
    st.markdown(
        """<div class="sidebar-tip"><b>Quick guide</b><br><br>
        1️⃣ Start at Home<br>2️⃣ Upload a report<br>3️⃣ Review extracted values<br>
        4️⃣ Explore your dashboard<br>5️⃣ Read AI Insights</div>""",
        unsafe_allow_html=True,
    )
    st.divider()
    if st.button("🚪 Log out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

home_page()
