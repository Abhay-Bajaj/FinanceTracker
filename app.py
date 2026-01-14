import streamlit as st

from src.db import init_db, get_user_by_username
from src.auth import get_authenticator, render_signup
from src.config import CATEGORIES
from src.state import enforce_guest_on_refresh

from src.features.add_entry import render_add_entry_tab
from src.features.transactions import render_transactions_tab
from src.features.dashboard import render_dashboard_tab

st.set_page_config(page_title="Finance Tracker", page_icon="💸", layout="wide")
init_db()

# -------------------- Auth --------------------
authenticator = get_authenticator()

# -------------------- Refresh behavior: ALWAYS default to guest --------------------
enforce_guest_on_refresh(authenticator)

# -------------------- Top Bar --------------------
top_left, top_right = st.columns([6, 2], vertical_alignment="center")

with top_left:
    st.title("Personal Finance Tracker")
    st.caption("Budget Your Income and Track Your Expenses")

with top_right:
    auth_status = st.session_state.get("authentication_status")
    username = st.session_state.get("username")

    if auth_status is True and username:
        user_row = get_user_by_username(username)
        display_name = user_row["name"] if user_row and user_row["name"] else username

        st.markdown(f"Signed in as: **{display_name}**")

        if authenticator.logout(location="main"):
            st.session_state.just_logged_in = False
            st.rerun()
    else:
        with st.popover("Log in / Sign up", use_container_width=True):
            tab_login, tab_signup = st.tabs(["Log in", "Sign up"])

            with tab_login:
                name, auth_status, username = authenticator.login(location="main")

                if auth_status is True:
                    st.session_state.just_logged_in = True
                    st.rerun()
                elif auth_status is False:
                    st.error("Incorrect username or password.")
                else:
                    st.caption("Guest mode (Data Not Saved).")

            with tab_signup:
                render_signup(show_title=False)

# -------------------- Mode detection --------------------
logged_in = st.session_state.get("authentication_status") is True
user_id = None

if logged_in:
    user_row = get_user_by_username(st.session_state.get("username"))
    if not user_row:
        st.error("User not found in database. Please contact support.")
        st.stop()
    user_id = int(user_row["id"])

if not logged_in:
    st.info(
        "Guest mode: your data is temporary. Log in to save your records.", icon="ℹ️"
    )

tabs = st.tabs(["➕ Add Entry", "📄 Transactions", "📊 Dashboard"])

# -------------------- Add Entry --------------------
with tabs[0]:
    render_add_entry_tab(logged_in=logged_in, user_id=user_id, categories=CATEGORIES)

# -------------------- Transactions --------------------
with tabs[1]:
    render_transactions_tab(logged_in=logged_in, user_id=user_id, categories=CATEGORIES)

# -------------------- Dashboard --------------------
with tabs[2]:
    render_dashboard_tab(logged_in=logged_in, user_id=user_id)

