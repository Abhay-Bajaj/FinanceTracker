import streamlit as st
import pandas as pd
from typing import Optional

from src.db import fetch_transactions, clear_user_data
from src.analytics import rows_to_df
from src.state import get_guest_transactions


def render_transactions_tab(logged_in: bool, user_id: Optional[int], categories: list[str]):
    st.subheader("Monthly Transactions")

    if logged_in:
        rows = fetch_transactions(user_id)
    else:
        rows = get_guest_transactions()

    df = rows_to_df(rows)

    colA, colB = st.columns([3, 1])
    with colB:
        if logged_in:
            with st.popover("Clear My Data"):
                st.warning("This permanently deletes your transactions (and budgets).")
                confirm = st.checkbox("I understand", key="confirm_clear")
                if st.button("Delete everything", disabled=not confirm):
                    clear_user_data(user_id)
                    st.success("Your data was cleared.")
                    st.rerun()
        else:
            if st.button("Clear Guest Data"):
                st.session_state["guest_transactions"] = []
                st.success("Guest data cleared.")
                st.rerun()

    if df.empty:
        st.info("No transactions yet. Add your first entry in the first tab.")
    else:
        df["month_key"] = df["date"].dt.strftime("%Y-%m")
        df["month_label"] = df["date"].dt.strftime("%m/%Y")

        month_map = (
            df[["month_key", "month_label"]]
            .drop_duplicates()
            .sort_values("month_key", ascending=False)
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            selected_label = st.selectbox(
                "Month",
                options=month_map["month_label"].tolist(),
            )
            month_filter = month_map.loc[
                month_map["month_label"] == selected_label, "month_key"
            ].iloc[0]

        with c2:
            cat_filter = st.selectbox("Category", options=["All"] + categories)

        with c3:
            search = st.text_input("Search Merchant/Notes", placeholder="Type to Filter")

        df_view = df[df["month_key"] == month_filter].copy()

        if cat_filter != "All":
            df_view = df_view[df_view["category"] == cat_filter]

        if search.strip():
            s = search.strip().lower()
            df_view = df_view[
                df_view["merchant"].fillna("").str.lower().str.contains(s)
                | df_view["notes"].fillna("").str.lower().str.contains(s)
            ]

        df_display = df_view.copy()
        df_display["amount"] = df_display["amount"].apply(lambda x: f"${float(x):,.2f}")

        df_display = (
            df_display.sort_values("date", ascending=False)
            .reset_index(drop=True)
        )
        df_display.index = df_display.index + 1
        df_display.index.name = "#"

        st.dataframe(
            df_display[
                ["date_display", "amount", "category", "merchant", "notes"]
            ].rename(
                columns={
                    "date_display": "Date",
                    "amount": "Amount ($)",
                    "category": "Category",
                    "merchant": "Merchant",
                    "notes": "Notes",
                }
            ),
            use_container_width=True,
        )

        # Clean CSV export (oldest -> newest)
        export_df = (
            df_view.sort_values(["date", "id"], ascending=[True, True])[
                ["date", "amount", "category", "merchant", "notes"]
            ]
            .copy()
        )

        export_df["date"] = pd.to_datetime(
            export_df["date"], errors="coerce"
        ).dt.strftime("%m/%d/%Y")

        export_df["amount"] = (
            pd.to_numeric(export_df["amount"], errors="coerce")
            .fillna(0.0)
            .apply(lambda x: f"${x:,.2f}")
        )
        export_df["merchant"] = export_df["merchant"].fillna("")
        export_df["notes"] = export_df["notes"].fillna("")

        export_df = export_df.rename(
            columns={
                "date": "Date",
                "amount": "Amount ($)",
                "category": "Category",
                "merchant": "Merchant",
                "notes": "Notes",
            }
        )

        safe_month = selected_label.replace("/", "-")
        st.download_button(
            "Download CSV",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name=f"Transactions_{safe_month}.csv",
            mime="text/csv",
        )
