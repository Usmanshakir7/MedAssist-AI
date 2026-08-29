import streamlit as st
from datetime import datetime

from database.user_model import create_user
from database.google_sheets import save_new_user


def signup_page():
    st.markdown("### 📝 Create Account")

    with st.form("signup_form", clear_on_submit=False):
        full_name = st.text_input("Full Name", placeholder="Your full name")
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="At least 6 characters")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Repeat password")

        submitted = st.form_submit_button(
            "Create Account",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            if not full_name or not email or not password:
                st.error("Please fill all fields.")
                return

            if len(password) < 6:
                st.error("Password must be at least 6 characters.")
                return

            if password != confirm_password:
                st.error("Passwords do not match.")
                return

            success, message = create_user(
                full_name.strip(),
                email.strip().lower(),
                password,
            )

            if not success:
                st.error(message)
                return

            # Get the newly-created user ID from SQLite.
            from database.user_model import get_user_by_email
            new_user = get_user_by_email(email.strip().lower())

            if new_user:
                created_at = new_user["created_at"] or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ok, sheet_error = save_new_user(
                    user_id=new_user["id"],
                    full_name=new_user["full_name"],
                    email=new_user["email"],
                    created_at=created_at,
                )

                if ok:
                    st.success("Account created successfully. You can now log in.")
                else:
                    # Registration still succeeded in SQLite. Google Sheets is only
                    # a secondary viewing/synchronization service.
                    st.success("Account created successfully. You can now log in.")
                    st.warning(
                        "Your account was saved, but Google Sheets synchronization "
                        "failed. You can fix the Google Sheets setup later."
                    )
                    with st.expander("Google Sheets error"):
                        st.code(sheet_error)
            else:
                st.success(message + " You can now log in.")
