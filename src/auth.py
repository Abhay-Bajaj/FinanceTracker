import re
import streamlit as st
import streamlit_authenticator as stauth

from src.db import fetch_users, user_exists, create_user


def build_credentials_from_db():
    users = fetch_users()
    usernames = {}
    for u in users:
        usernames[u["username"]] = {
            "name": u["name"],
            "email": u["email"],
            "password": u["password_hash"],
        }
    return {"usernames": usernames}


def get_authenticator():
    cookie_name = st.secrets.get("auth", {}).get("cookie_name", "finance_tracker_auth")
    cookie_key = st.secrets.get("auth", {}).get("cookie_key", "CHANGE_ME_TO_A_LONG_RANDOM_SECRET")
    cookie_expiry_days = int(st.secrets.get("auth", {}).get("cookie_expiry_days", 30))

    credentials = build_credentials_from_db()

    authenticator = stauth.Authenticate(
        credentials=credentials,
        cookie_name=cookie_name,
        cookie_key=cookie_key,
        cookie_expiry_days=cookie_expiry_days,
    )
    return authenticator


def render_signup(show_title: bool = True):
    if show_title:
        st.markdown("### Create an account")

    with st.form("signup_form", clear_on_submit=True):
        username = st.text_input("Username", placeholder="user1")
        name = st.text_input("Full name", placeholder="User One")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button("Sign up")

    if not submitted:
        return

    username = username.strip()
    name = name.strip()

    errors = []

    # Username rules
    if not username:
        errors.append("• Username is required.")
    elif not re.fullmatch(r"[A-Za-z0-9]{5,20}", username):
        errors.append(
            "• Username must be 5–20 characters and use only letters and numbers."
        )
    elif user_exists(username):
        errors.append(
            "• There’s already an account with this username. Please sign in instead."
        )

    # Full name
    if not name:
        errors.append("• Full name is required.")

    # Password rules
    if not password:
        errors.append("• Password is required.")
    else:
        if len(password) < 8:
            errors.append("• Password must be at least 8 characters.")
        if not re.search(r"[A-Z]", password):
            errors.append("• Password must include at least one uppercase letter.")
        if not re.search(r"\d", password):
            errors.append("• Password must include at least one number.")
        if not re.search(r"[^A-Za-z0-9]", password):
            errors.append("• Password must include at least one special character.")

    # Confirm password
    if password and password != confirm:
        errors.append("• Passwords do not match.")

    # Show all errors at once
    if errors:
        st.error("Please fix the following issues:")
        for err in errors:
            st.write(err)
        return

    # Create account
    password_hash = stauth.Hasher([password]).generate()[0]

    create_user(
        username=username,
        name=name,
        email="",
        password_hash=password_hash,
    )

    st.success("Account created! Please log in.")
    st.rerun()
