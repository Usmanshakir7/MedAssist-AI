import streamlit as st

from auth.login import login_page
from auth.signup import signup_page
from views.upload import upload_page
# ---------- Session ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "show_signup" not in st.session_state:
    st.session_state.show_signup = False


# ---------- Login Screen ----------
if not st.session_state.logged_in:

    if st.session_state.show_signup:

        signup_page()

        if st.button("Already have an account? Login"):
            st.session_state.show_signup = False
            st.rerun()

    else:

        login_page()

        if st.button("Create New Account"):
            st.session_state.show_signup = True
            st.rerun()

# ---------- Main App ----------
else:

    st.sidebar.success(
        f"Welcome {st.session_state.user['full_name']}"
    )

    page = st.sidebar.radio(
        "Navigation",
        [
            "Home",
            "Upload Report",
            "Reports",
            "Dashboard",
            "AI Insights",
            "Settings"
        ]
    )

    if page == "Home":
        st.title("🏠 Home")

    elif page == "Upload Report":
       upload_page()

    elif page == "Reports":
        st.title("📄 Reports")

    elif page == "Dashboard":
        st.title("📊 Dashboard")

    elif page == "AI Insights":
        st.title("🤖 AI Insights")

    elif page == "Settings":
        st.title("⚙ Settings")

    st.sidebar.divider()

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()