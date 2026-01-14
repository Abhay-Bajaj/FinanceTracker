import pandas as pd
from src.utils.money import fmt_money


def build_transactions_export_csv(df_view: pd.DataFrame, selected_label: str) -> tuple[bytes, str]:
    """
    Returns: (csv_bytes, filename)
    """
    export_df = (
        df_view.sort_values(["date", "id"], ascending=[True, True])[
            ["date", "amount", "category", "merchant", "notes"]
        ]
        .copy()
    )

    export_df["date"] = pd.to_datetime(export_df["date"], errors="coerce").dt.strftime("%m/%d/%Y")
    export_df["amount"] = (
        pd.to_numeric(export_df["amount"], errors="coerce")
        .fillna(0)
        .apply(fmt_money)
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
    filename = f"Transactions_{safe_month}.csv"
    return export_df.to_csv(index=False).encode("utf-8"), filename
