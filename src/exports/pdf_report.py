import io
import pandas as pd

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


def build_dashboard_pdf_bytes(
    selected_label: str,
    total_income: float,
    total_expenses: float,
    net: float,
    by_cat: pd.DataFrame,
    by_day: pd.DataFrame,
) -> bytes:
    
    # Download Monthly Dashboard PDF (report)
    def _money(x: float) -> str:
        return f"${float(x):,.2f}"

    income_vs_expense_rows = [
        ["Type", "Amount ($)"],
        ["Income", f"{float(total_income):.2f}"],
        ["Expenses", f"{float(total_expenses):.2f}"],
    ]

    by_cat_rows = [["Category", "Amount ($)"]]
    if not by_cat.empty:
        for _, r in by_cat.sort_values("amount", ascending=False).iterrows():
            by_cat_rows.append([str(r["category"]), f"{float(r['amount']):.2f}"])
    else:
        by_cat_rows.append(["(no data)", ""])

    by_day_rows = [["Day", "Amount ($)"]]
    if not by_day.empty:
        tmp = by_day.copy()
        tmp["day"] = pd.to_datetime(tmp["day"], errors="coerce")
        tmp = tmp.dropna(subset=["day"]).sort_values("day")
        for _, r in tmp.iterrows():
            by_day_rows.append(
                [r["day"].strftime("%m/%d/%Y"), f"{float(r['amount']):.2f}"]
            )
    else:
        by_day_rows.append(["(no data)", ""])

    def _make_table(data):
        t = Table(data, hAlign="LEFT")
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9CA3AF")),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.whitesmoke, colors.lightgrey],
                    ),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return t

    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
    )
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Monthly Dashboard - {selected_label}", styles["Title"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f"Income: {_money(total_income)}", styles["Normal"]))
    story.append(Paragraph(f"Expenses: {_money(total_expenses)}", styles["Normal"]))
    story.append(Paragraph(f"Net: {_money(net)}", styles["Normal"]))
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Income vs Expenses", styles["Heading2"]))
    story.append(_make_table(income_vs_expense_rows))
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Spending by Category (Expenses Only)", styles["Heading2"]))
    story.append(_make_table(by_cat_rows))
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Daily Spending Trend (Expenses Only)", styles["Heading2"]))
    story.append(_make_table(by_day_rows))

    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()
