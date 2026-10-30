"""Declarative semantic boundary for the pinned spending snapshot.

Shared contracts are data, not the producer's row-search implementation. The
independent reader checks these identities against raw workbook labels/headers.
Changing snapshot coverage requires an explicit contract change and source review.
"""
from openpyxl.utils import get_column_letter

BASE = "2025-26"
YEARS = [f"{y}-{(y + 1) % 100:02d}" for y in range(2003, 2026)]
AGG_YEARS = [f"{y}-{(y + 1) % 100:02d}" for y in range(1985, 2029)]
DECADES = [f"{y}-{(y + 1) % 100:02d}" for y in range(1945, 2026, 10)]
FUNCTION_ROWS = {
    "general": (6, "1. General public services"),
    "defence": (10, "2. Defence"),
    "order": (11, "3. Public order and safety"),
    "economic": (12, "4. Economic affairs"),
    "environment": (18, "5. Environment protection"),
    "housing": (19, "6. Housing and community amenities"),
    "health": (20, "7. Health"),
    "culture": (21, "8. Recreation, culture and religion"),
    "education": (22, "9. Education"),
    "social": (23, "10. Social protection"),
    "eu": (24, "EU transactions"),
}
DETAIL_ROWS = {
    "pensions": (107, "of which: pensions", "social"),
    "medical": (76, "Medical services", "health"),
    "uc": (118, "of which: family benefits, income support, Universal Credit and tax credits", "social"),
    "cg_interest": (15, "of which: central government debt interest", "general"),
    "disability": (104, "of which: incapacity, disability and injury benefits", "social"),
    "secondary": (92, "9.2 Secondary education", "education"),
    "military": (22, "2.1 Military defence", "defence"),
    "primary": (91, "of which: primary education", "education"),
    "railway": (50, "of which: railway", "economic"),
    "police": (31, "of which: other police services", "order"),
}
DEBT_LABELS = ["central government debt interest", "local government debt interest",
               "public corporation debt interest", "Bank of England", "public sector pensions"]
TOTAL_COLS = {
    "spending": ("D", "Total spending\n(TME)"),
    "receipts": ("C", "Total receipts\n(PSCR)"),
    "borrowing": ("E", "Public sector net borrowing\n(PSNB)"),
    "debt": ("F", "Public sector net debt\n(PSND)"),
}
AREA_COLS = {
    "health": ("H", "Health6", "D52"),
    "education": ("L", "Education8", "D56"),
    "social": ("I", "Social Security7", "D53"),
    "defence": ("G", "Defence5", "D51"),
    "interest": ("M", "Debt Interest9", "D57"),
}


def keyed(rows, expected, what):
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)) or set(ids) != set(expected):
        raise ValueError(f"Fiscal schema: missing, duplicate or overlapping {what}")
    return {row["id"]: row for row in rows}


def exact_keys(value, expected, what):
    if set(value) != set(expected):
        raise ValueError(f"Fiscal schema: missing or extra {what}")


def spec(sheet, cell, period, series, label_ref, label, period_ref, unit_ref,
         unit_label, scope, precision=3, note=None):
    sid = ("pesa_ch4" if sheet.startswith("4_") else "pesa_ch5" if sheet == "5_2"
           else "obr_databank" if sheet == "Public finances since 1900" else "obr_hist")
    percent = sheet in ("4_4", "Public finances since 1900", "Spending (per cent of GDP)") or "Per cent" in unit_label
    basis = "GDP share" if percent else "2025-26 prices" if sheet == "4_3" or "Real terms" in unit_label else "cash"
    return {"ref": f"{sheet}!{cell}", "source_id": sid, "period": period,
            "series": series, "unit": "percent GDP" if percent else "GBP billion",
            "scale": 0.001 if sheet == "5_2" else 1, "geography": "UK",
            "scope": scope, "basis": basis, "precision": precision,
            "identity": {"label": [f"{sheet}!{label_ref}", label],
                         "period": [f"{sheet}!{period_ref}", period],
                         "unit": [f"{sheet}!{unit_ref}", unit_label]},
            "note": note}


def selections(data):
    """Yield every permitted leaf with its independent semantic expectation."""
    if data["years"] != YEARS or data["latest_year"] != BASE or data["base_year"] != BASE:
        raise ValueError("Fiscal schema: missing or changed functional periods")
    if [r["year"] for r in data["aggregates"]] != AGG_YEARS:
        raise ValueError("Fiscal schema: missing, duplicate or changed aggregate periods")
    for row in data["aggregates"]:
        y = row["year"]
        r = int(y[:4]) - 1985 + 6
        exact_keys(row, ("year", "forecast", "tme", "current", "investment"), "aggregate categories")
        if row["forecast"] != (y > BASE):
            raise ValueError("Fiscal schema: wrong forecast status")
        for key, col, label in (("tme", 13, "Total Managed Expenditure"),
                                ("current", 3, "Public sector current expenditure"),
                                ("investment", 9, "Public sector net investment")):
            exact_keys(row[key], ("nominal", "real", "gdp"), "aggregate units")
            for view, offset, unit_label in (("nominal", 0, "Nominal\n£ billion"),
                    ("real", 1, "Real terms (1)\n£ billion"), ("gdp", 2, "Per cent\nof GDP (2)")):
                c = get_column_letter(col + offset)
                yield row[key][view], spec("4_1", f"{c}{r}", y, f"aggregate.{key}.{view}",
                    f"{get_column_letter(col)}4", label, f"B{r}", f"{c}5", unit_label,
                    f"public sector {key}", precision=None)

    funcs = keyed(data["functions"], FUNCTION_ROWS, "functional categories")
    for key, (r, label) in FUNCTION_ROWS.items():
        area = funcs[key]
        if area["official"] != label.split(". ", 1)[-1]:
            raise ValueError("Fiscal schema: functional label mismatch")
        exact_keys(area["series"], YEARS, "functional periods")
        for y in YEARS:
            exact_keys(area["series"][y], ("nominal", "real", "gdp"), "functional units")
            c = get_column_letter(int(y[:4]) - 2003 + 2)
            for view, sheet, unit_label in (("nominal", "4_2", "£ billion"),
                    ("real", "4_3", "£ billion"), ("gdp", "4_4", "per cent")):
                yield area["series"][y][view], spec(sheet, f"{c}{r}", y,
                    f"function.{key}.{view}", f"A{r}", label, f"{c}5", "X3",
                    unit_label, f"TES/COFOG/{key}")

    for key, r, label in (("services_total", 25, "Public sector expenditure on services"),
                           ("debt_interest", 9, "of which: public sector debt interest")):
        exact_keys(data[key], YEARS, key + " periods")
        for y in YEARS:
            c = get_column_letter(int(y[:4]) - 2003 + 2)
            yield data[key][y], spec("4_2", f"{c}{r}", y, key, f"A{r}", label,
                f"{c}5", "X3", "£ billion", "TES" if r == 25 else "TES/COFOG/general/debt transactions")

    details = keyed(data["details"], DETAIL_ROWS, "selected items")
    for key, (r, label, parent) in DETAIL_ROWS.items():
        if details[key]["official"] != label.replace("of which: ", ""):
            raise ValueError("Fiscal schema: selected-item label mismatch")
        yield details[key], spec("5_2", f"G{r}", BASE, f"detail.{key}", f"B{r}", label,
            "G5", "G3", "£ million", f"TES/COFOG/{parent}/selected/{key}", precision=1)
    if [p["official"] for p in data["debt_parts"]] != DEBT_LABELS:
        raise ValueError("Fiscal schema: missing, duplicate or overlapping debt components")
    for r, part in enumerate(data["debt_parts"], 15):
        label = "of which:" + ("" if r == 18 else " ") + part["official"]
        yield part, spec("5_2", f"G{r}", BASE, f"debt_component.{r}", f"B{r}", label,
            "G5", "G3", "£ million", "TES/COFOG/general/debt transactions/" + part["official"], precision=1)

    history = data["history"]
    if history["decades"] != DECADES or history["areas_last_year"] != "2022-23":
        raise ValueError("Fiscal schema: changed historical coverage")
    for group, columns in (("totals", TOTAL_COLS), ("areas", AREA_COLS)):
        series = keyed(history[group], columns, "historical " + group)
        for key, column in columns.items():
            col, label = column[:2]
            sheet = "Public finances since 1900" if group == "totals" else "Spending (per cent of GDP)"
            ys = DECADES if group == "totals" else DECADES[:-1]
            exact_keys(series[key]["values"], ys, "historical periods")
            if series[key]["official"] != (label.replace("\n", " ") if group == "totals" else label.rstrip("0123456789")):
                raise ValueError("Fiscal schema: historical label mismatch")
            for y in ys:
                r = int(y[:4]) - (1900 if group == "totals" else 1700) + 7
                scope = ("public sector " + key if group == "totals" else
                         "joined historical functions/" + key)
                if group == "areas" and key == "interest":
                    scope = "central government interest net of APF"
                if group == "totals" and key == "debt":
                    scope = "public sector net debt stock; centred end-March GDP denominator"
                yield series[key]["values"][y], spec(sheet, f"{col}{r}", y,
                    f"history.{group}.{key}", f"{col}{6 if group == 'totals' else 4}", label,
                    f"B{r}", "C5" if group == "totals" else "@sheet",
                    "Per cent of GDP" if group == "totals" else sheet, scope, precision=1,
                    note=None if group == "totals" else column[2])
