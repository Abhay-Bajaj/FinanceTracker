import streamlit as st


# Guest helpers
def get_guest_transactions():
    return st.session_state.get("guest_transactions", [])


def add_guest_transaction(tx):
    st.session_state.setdefault("guest_transactions", [])
    st.session_state["guest_transactions"].append(tx)


# Refresh behavior: ALWAYS default to guest
def enforce_guest_on_refresh(authenticator):
    if "just_logged_in" not in st.session_state:
        st.session_state.just_logged_in = False

    if (
        st.session_state.get("authentication_status") is True
        and not st.session_state.get("just_logged_in", False)
    ):
        st.session_state["authentication_status"] = None
        st.session_state["username"] = None
        st.session_state["name"] = None

        try:
            authenticator.cookie_manager.delete(authenticator.cookie_name)
        except Exception:
            try:
                cookie_name = st.secrets.get("auth", {}).get(
                    "cookie_name", "finance_tracker_auth"
                )
                authenticator.cookie_manager.delete(cookie_name)
            except Exception:
                pass

        st.rerun()
