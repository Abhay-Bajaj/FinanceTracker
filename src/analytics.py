import pandas as pd


def rows_to_df(rows):
    """
    Accepts:
      - sqlite3.Row rows from DB (dict-like)
      - OR list of dicts from guest session
    Returns a DataFrame with:
      id, user_id (optional), date (datetime), date_display, amount, category, merchant, notes, created_at
    """
    if not rows:
        return pd.DataFrame(
            columns=["id", "user_id", "date", "amount", "category", "merchant", "notes", "created_at", "date_display"]
        )

    df = pd.DataFrame([dict(r) for r in rows])

    for col in ["id", "user_id", "created_at", "merchant", "notes"]:
        if col not in df.columns:
            df[col] = None

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # If any date failed parsing, drop those rows (prevents .dt errors)
    df = df.dropna(subset=["date"]).copy()

    # Display-only date column
    df["date_display"] = df["date"].dt.strftime("%m/%d/%Y")

    # Amount numeric
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)

    return df


def monthly_summary(df: pd.DataFrame, month_key: str):
    """
    month_key: "YYYY-MM"

    Returns:
      by_cat_expenses: expense totals by category (Income excluded)
      by_day_expenses: daily expense totals (Income excluded)
      total_income: sum of Income rows
      total_expenses: sum of non-Income rows
      net: income - expenses
      remaining: (same as net) kept for optional feature
    """
    empty_cat = pd.DataFrame(columns=["category", "amount"])
    empty_day = pd.DataFrame(columns=["day", "amount"])

    if df.empty:
        return empty_cat, empty_day, 0.0, 0.0, 0.0, 0.0

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    df_m = df[df["date"].dt.strftime("%Y-%m") == month_key].copy()
    if df_m.empty:
        return empty_cat, empty_day, 0.0, 0.0, 0.0, 0.0

    income_df = df_m[df_m["category"] == "Income"].copy()
    exp_df = df_m[df_m["category"] != "Income"].copy()

    total_income = float(income_df["amount"].sum()) if not income_df.empty else 0.0
    total_expenses = float(exp_df["amount"].sum()) if not exp_df.empty else 0.0

    net = total_income - total_expenses
    remaining = net

    by_cat_expenses = (
        exp_df.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
        if not exp_df.empty
        else empty_cat
    )

    by_day_expenses = (
        exp_df.assign(day=exp_df["date"].dt.date)
        .groupby("day", as_index=False)["amount"]
        .sum()
        if not exp_df.empty
        else empty_day
    )

    return by_cat_expenses, by_day_expenses, total_income, total_expenses, net, remaining
