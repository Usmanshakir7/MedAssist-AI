import streamlit as st
from database.user_model import create_user


def signup_page():

    st.title("📝 Create Account")

    full_name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Create Account"):

        if not full_name or not email or not password:
            st.error("Please fill all fields.")
            return

        if password != confirm_password:
            st.error("Passwords do not match.")
            return

        success, message = create_user(
            full_name,
            email,
            password
        )

        if success:
            st.success(message)
        else:
            st.error(message)