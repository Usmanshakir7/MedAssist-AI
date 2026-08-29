import streamlit as st
from datetime import datetime

from database.user_model import login_user
from database.google_sheets import update_last_login


def login_page():
    st.markdown("### 🔐 Login")

    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button(
            "Login",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            if not email or not password:
                st.error("Please enter both email and password.")
                return

            clean_email = email.strip().lower()
            success, result = login_user(clean_email, password)

            if success:
                st.session_state.logged_in = True
                st.session_state.user = dict(result)

                # Google Sheets is only a secondary activity log.
                # Login still works if Sheets is unavailable.
                try:
                    update_last_login(
                        clean_email,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    )
                except Exception:
                    pass

                st.rerun()
            else:
                st.error(result)
