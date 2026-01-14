import streamlit as st
import pandas as pd
from typing import Optional

from src.db import fetch_transactions
from src.state import get_guest_transactions
from src.analytics import rows_to_df, monthly_summary
from src.exports.pdf_report import build_dashboard_pdf_bytes


def render_dashboard_tab(logged_in: bool, user_id: Optional[int]):
    st.subheader("Monthly Dashboard")

    if logged_in:
        rows = fetch_transactions(user_id)
    else:
        rows = get_guest_transactions()

    df = rows_to_df(rows)

    if df.empty:
        st.info("Add some transactions first.")
    else:
        df["month_key"] = df["date"].dt.strftime("%Y-%m")
        df["month_label"] = df["date"].dt.strftime("%m/%Y")

        month_map = (
            df[["month_key", "month_label"]]
            .drop_duplicates()
            .sort_values("month_key", ascending=False)
        )

        selected_label = st.selectbox("Select Month", month_map["month_label"].tolist())
        month = month_map.loc[
            month_map["month_label"] == selected_label, "month_key"
        ].iloc[0]

        by_cat, by_day, total_income, total_expenses, net, _remaining = monthly_summary(
            df, month
        )

        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric("Income", f"${total_income:,.2f}")
        with k2:
            st.metric("Expenses", f"${total_expenses:,.2f}")
        with k3:
            st.metric("Net", f"${net:,.2f}")

        st.write("Income vs Expenses")
        income_vs_expense = pd.DataFrame(
            {"Type": ["Income", "Expenses"], "Amount": [total_income, total_expenses]}
        ).set_index("Type")
        st.bar_chart(income_vs_expense["Amount"])

        c1, c2 = st.columns(2)
        with c1:
            st.write("Spending By Category (Expenses Only)")
            if not by_cat.empty:
                st.bar_chart(by_cat.set_index("category")["amount"])
            else:
                st.caption("No expense data for this month.")

        with c2:
            st.write("Daily Spending Trend (Expenses Only)")
            if not by_day.empty:
                by_day_plot = by_day.copy()
                by_day_plot["day"] = pd.to_datetime(by_day_plot["day"])
                by_day_plot = by_day_plot.set_index("day")["amount"]
                st.line_chart(by_day_plot)
            else:
                st.caption("No expense data for this month.")

        pdf_bytes = build_dashboard_pdf_bytes(
            selected_label=selected_label,
            total_income=total_income,
            total_expenses=total_expenses,
            net=net,
            by_cat=by_cat,
            by_day=by_day,
        )

        st.download_button(
            "Download Monthly Dashboard PDF",
            data=pdf_bytes,
            file_name=f"Monthly_Dashboard_{selected_label.replace('/','-')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
