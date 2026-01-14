import streamlit as st
from datetime import date
from typing import Optional

from src.db import add_transaction
from src.state import add_guest_transaction


def render_add_entry_tab(logged_in: bool, user_id: Optional[int], categories: list[str]):
    st.subheader("Add An Entry")

    category_options = [" "] + categories

    if "amount_input_pending" in st.session_state:
        st.session_state["amount_input"] = st.session_state.pop("amount_input_pending")

    with st.form("add_entry_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            tx_date = st.date_input("Date", value=date.today(), format="MM/DD/YYYY")

        with col2:
            amount_str = st.text_input(
                "Amount ($)", value="", placeholder="0.00", key="amount_input"
            )

        with col3:
            category = st.selectbox("Category", category_options, index=0)

        merchant = st.text_input(
            "Merchant (optional)", value="", placeholder="Target"
        )
        notes = st.text_input(
            "Notes (optional)", value="", placeholder="groceries for the week"
        )

        submitted = st.form_submit_button("Save")

    if submitted:
        raw = (st.session_state.get("amount_input", "") or "").strip().replace(",", "")
        raw = raw.replace("$", "")

        try:
            amount = float(raw)
        except ValueError:
            amount = -1

        if category == " ":
            st.error("Please select a category.")
        elif amount <= 0:
            st.error("Enter a valid amount greater than 0 (example: 12.50).")
        else:
            if logged_in:
                add_transaction(user_id, str(tx_date), amount, category, merchant, notes)
            else:
                add_guest_transaction(
                    {
                        "id": None,
                        "user_id": None,
                        "date": str(tx_date),
                        "amount": float(amount),
                        "category": category,
                        "merchant": merchant.strip() or None,
                        "notes": notes.strip() or None,
                        "created_at": None,
                    }
                )

            st.success("Saved!")

            st.session_state["amount_input_pending"] = f"{amount:.2f}"
            st.rerun()
