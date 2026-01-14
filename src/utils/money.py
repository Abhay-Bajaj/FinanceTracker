def parse_money(raw: str) -> float | None:
    s = (raw or "").strip()
    if not s:
        return None

    s = s.replace(",", "").replace("$", "").strip()
    try:
        val = float(s)
    except ValueError:
        return None

    if val <= 0:
        return None
    return val


def fmt_money(x: float) -> str:
    return f"${float(x):,.2f}"
