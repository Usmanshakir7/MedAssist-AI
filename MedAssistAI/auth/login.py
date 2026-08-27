import streamlit as st
from database.user_model import login_user


def login_page():

    st.title("🔐 Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        success, result = login_user(email, password)

        if success:
         st.session_state.logged_in = True
         st.session_state.user = dict(result)
         st.rerun()

        else:
            st.error(result)