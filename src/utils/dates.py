import pandas as pd


def build_month_map(df: pd.DataFrame) -> pd.DataFrame:
    """
    Expects df to contain a datetime column named 'date'.
    Returns a dataframe with month_key (YYYY-MM) and month_label (MM/YYYY),
    sorted descending by month_key.
    """
    tmp = df.copy()
    tmp["month_key"] = tmp["date"].dt.strftime("%Y-%m")
    tmp["month_label"] = tmp["date"].dt.strftime("%m/%Y")

    month_map = (
        tmp[["month_key", "month_label"]]
        .drop_duplicates()
        .sort_values("month_key", ascending=False)
    )
    return month_map
