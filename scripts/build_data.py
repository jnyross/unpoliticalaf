"""Turn the raw HM Treasury PESA and OBR spreadsheets into data/spending.json.

Every value keeps a reference to the exact sheet and cell it came from. The build
stops with an error if the files do not match their recorded hashes or if the
figures do not reconcile with the published totals.
"""

import hashlib
import json
import math
import re
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

from fiscal_schema import enrich

ROOT = Path(__file__).resolve().parent.parent
YEAR = re.compile(r"^\d{4}-\d{2}$")
BASE_YEAR = "2025-26"
LAST_OUTTURN = "2025-26"

# Plain-English names sit next to the official UN COFOG names; the official name is
# always shown too, so a reader can find the line in the source table.
FUNCTIONS = [
    ("general", "1. General public services", "Running government, and interest on debt"),
    ("defence", "2. Defence", "Defence"),
    ("order", "3. Public order and safety", "Police, courts, prisons and fire services"),
    ("economic", "4. Economic affairs", "Transport, business support and research"),
    ("environment", "5. Environment protection", "Waste, pollution and nature"),
    ("housing", "6. Housing and community amenities", "Housing and local amenities"),
    ("health", "7. Health", "Health"),
    ("culture", "8. Recreation, culture and religion", "Culture, sport and broadcasting"),
    ("education", "9. Education", "Education"),
    ("social", "10. Social protection", "Pensions, benefits and social care"),
    ("eu", "EU transactions", "Payments to and from the EU"),
]

# Selected items from table 5.2 (2025-26 detail), within the function totals.
DETAIL = [
    ("pensions", "of which: pensions", "Pensions paid in old age"),
    ("medical", "Medical services", "Hospitals, GPs and other medical services"),
    ("uc", "of which: family benefits, income support, Universal Credit and tax credits",
     "Universal Credit and tax credits"),
    ("cg_interest", "of which: central government debt interest", "Interest on central government debt"),
    ("disability", "of which: incapacity, disability and injury benefits",
     "Incapacity, disability and injury benefits"),
    ("secondary", "9.2 Secondary education", "Secondary schools"),
    ("military", "2.1 Military defence", "Military defence"),
    ("primary", "of which: primary education", "Primary schools"),
    ("railway", "of which: railway", "Railways"),
    ("police", "of which: other police services", "Police (excluding immigration)"),
]

# Footnotes from the source, attached to the series they affect so pages can show
# them on the chart rather than only at the bottom.
NOTES = {
    "defence": "This uses the UN way of counting defence. NATO targets count it a different way, "
               "so the two do not match. NATO includes pay-outs to retired forces staff. "
               "Here those are under pensions and benefits. (PESA Table 4.2, note 1)",
    "education": "From 2011-12 the cost of student loans is not counted here. So you cannot "
                 "fairly compare years before and after 2011-12. (PESA Table 4.2, note 5)",
    "economic": "Network Rail is only counted from 2015-16. From 2011-12 the transport figures include "
                "the local government part of Transport Trading Limited (TfL). From 2008-09 the figures include help "
                "for banks. From 2020-21 they include help during Covid and when prices rose fast. "
                "(PESA Table 4.2, notes 2, 3 and 4)",
}


def clean(label):
    """Normalise a row label: collapse spaces and drop footnote markers like (3) or (4)."""
    if label is None:
        return None
    label = str(label).replace(" ", " ")
    label = re.sub(r"\s*\(\d+\)(,\s*\(\d+\))*", "", label)
    return re.sub(r"\s+", " ", label).strip()


def number(cell):
    if cell is None:
        return None
    if isinstance(cell, str):
        if cell.strip() in ("-", ""):
            return None
        cell = cell.replace(",", "")
    value = float(cell)
    if not math.isfinite(value):
        raise ValueError("Non-finite source value")
    return value


def verify(sources):
    manifest = ROOT / "data/sources.json"
    if manifest.is_symlink() or hashlib.sha256(manifest.read_bytes()).hexdigest() != "5e7ebb343bee091960052b1727bf7bff6997216e8a5bf7805d18770aa7d5914a":
        raise ValueError("Source catalogue differs from the pinned seed")
    for key, src in sources.items():
        path = ROOT / src["file"]
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError(f"{key}: source path contains a symlink")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != src["sha256"]:
            raise ValueError(f"{key}: {src['file']} does not match its recorded SHA-256")


def grid(path, sheet):
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        return [list(r) for r in book[sheet].iter_rows(values_only=True)]
    finally:
        book.close()


def ref(sheet, row, col):
    return f"{sheet}!{get_column_letter(col + 1)}{row + 1}"


def function_table(rows, sheet, scale=1.0):
    """Parse a 'by function' table: one header row of years, one row per label."""
    header = next(i for i, r in enumerate(rows) if sum(bool(YEAR.match(str(c or ""))) for c in r) > 3)
    cols = {str(c): j for j, c in enumerate(rows[header]) if YEAR.match(str(c or ""))}
    out = []
    for i in range(header + 1, len(rows)):
        r = rows[i]
        label_col = next((j for j, c in enumerate(r) if isinstance(c, str) and not YEAR.match(c)), None)
        if label_col is None or label_col >= min(cols.values()):
            continue
        values = {y: number(r[j]) for y, j in cols.items()}
        if all(v is None for v in values.values()):
            continue
        out.append({
            "row": i,
            "label": clean(r[label_col]),
            "values": {y: (None if v is None else round(v * scale, 3)) for y, v in values.items()},
            "refs": {y: ref(sheet, i, j) for y, j in cols.items()},
        })
    return out, list(cols)


def find(rows, label, after=None):
    matches = [r for r in rows if r["label"] == label and (after is None or r["row"] > after)]
    if len(matches) != 1:
        raise ValueError(f"Missing or duplicate source category: {label}")
    return matches[0]


def pesa_context(rows):
    """Read the pinned table's status and price/vintage notes, fail if ambiguous."""
    notes = {ref("4_1", i, j): c for i, row in enumerate(rows) for j, c in enumerate(row)
             if isinstance(c, str)}
    status = [(cell, re.search(r"Outturn data in this table up to (\d{4}-\d{2})", text))
              for cell, text in notes.items() if "Outturn data in this table up to" in text]
    if len(status) != 1 or status[0][1] is None:
        raise ValueError("PESA outturn boundary is missing or ambiguous")
    boundary = status[0][1].group(1)
    deflator = [(cell, text) for cell, text in notes.items() if "Real terms figures are" in text]
    gdp = [(cell, text) for cell, text in notes.items() if "GDP forecasts from" in text]
    if len(deflator) != 1 or len(gdp) != 1:
        raise ValueError("PESA forecast/deflator notes missing or ambiguous")
    date_pattern = r"Economic and fiscal outlook - (\d{1,2} [A-Za-z]+ \d{4})"
    dates = [re.search(date_pattern, text) for _, text in deflator + gdp]
    if any(d is None for d in dates) or dates[0].group(1) != dates[1].group(1):
        raise ValueError("PESA forecast dates missing or conflicting")
    base = re.search(r"adjusted to (\d{4}-\d{2}) price levels", deflator[0][1])
    if boundary != LAST_OUTTURN or base is None or base.group(1) != BASE_YEAR:
        raise ValueError("PESA status/base year differs from supported spending snapshot")
    return {"last_outturn": boundary, "status_ref": status[0][0],
            "forecast_date": dates[0].group(1), "forecast_ref": gdp[0][0],
            "deflator_ref": deflator[0][0], "base_year": base.group(1)}


def aggregates(rows):
    """Table 4.1: two header rows (group, then measure) above one row per year."""
    context = pesa_context(rows)
    group_row = next(i for i, r in enumerate(rows) if "Total Managed Expenditure" in " ".join(map(str, r)))
    groups, current = {}, None
    for j, c in enumerate(rows[group_row]):
        if c:
            current = clean(c)
        groups[j] = current
    measures = {}
    for j, c in enumerate(rows[group_row + 1]):
        if not c:
            continue
        kind = "nominal" if c.startswith("Nominal") else "real" if c.startswith("Real") else "gdp"
        measures[(groups[j], kind)] = j
    wanted = {
        "tme": "Total Managed Expenditure",
        "current": "Public sector current expenditure",
        "investment": "Public sector net investment",
    }
    out = []
    for i, r in enumerate(rows):
        year = next((c for c in r if isinstance(c, str) and YEAR.match(c)), None)
        if not year:
            continue
        entry = {"year": year, "forecast": year > context["last_outturn"]}
        for key, group in wanted.items():
            entry[key] = {
                kind: {"v": number(r[j]), "ref": ref("4_1", i, j)}
                for (g, kind), j in measures.items() if g == group
            }
        out.append(entry)
    return out


def required(value, what):
    if value is None:
        raise ValueError(f"{what}: missing source value; cannot establish this comparison")
    return value


def close(a, b, tol, what):
    if a is None or b is None:
        raise ValueError(f"{what}: missing source value; reconciliation cannot be established")
    if abs(a - b) > tol + 1e-9:
        raise AssertionError(f"{what}: {a} vs {b} (tolerance {tol})")


# Long-run comparisons go back from the latest year in steps of ten years, to the
# first year after the Second World War (1945-46), so no year is picked by hand.
DECADES = [f"{y}-{(y + 1) % 100:02d}" for y in range(1945, int(LAST_OUTTURN[:4]) + 1, 10)]

LONG_TOTALS = [
    ("spending", "Total spending\n(TME)", "Total spending"),
    ("receipts", "Total receipts\n(PSCR)", "Total income, mostly taxes"),
    ("borrowing", "Public sector net borrowing\n(PSNB)", "Borrowing in the year"),
    ("debt", "Public sector net debt\n(PSND)", "Total debt owed"),
]

LONG_AREAS = [
    ("health", "Health6", "Health"),
    ("education", "Education8", "Education"),
    ("social", "Social Security7", "Benefits and state pensions"),
    ("defence", "Defence5", "Defence"),
    ("interest", "Debt Interest9", "Interest on government debt"),
]


def year_rows(rows, header_row, year_col, sheet, wanted, missing):
    """Read a sheet with one row per year and one column per series."""
    cols = {c: j for j, c in enumerate(rows[header_row]) if c}
    out = {}
    for i, r in enumerate(rows):
        y = r[year_col] if year_col < len(r) else None
        if not (isinstance(y, str) and YEAR.match(y)):
            continue
        out[y] = {}
        for key, label in wanted:
            v = number(r[cols[label]])
            out[y][key] = {"v": None if v is None else round(v, 1), "raw": v, "ref": ref(sheet, i, cols[label])}
    return out


def long_run(sources, agg):
    sheet = "Public finances since 1900"
    rows = grid(ROOT / sources["obr_databank"]["file"], sheet)
    header = next(i for i, r in enumerate(rows) if "Years" in r)
    totals = year_rows(rows, header, rows[header].index("Years"), sheet,
                       [(k, label) for k, label, _ in LONG_TOTALS], ())

    sheet = "Spending (per cent of GDP)"
    rows = grid(ROOT / sources["obr_hist"]["file"], sheet)
    header = next(i for i, r in enumerate(rows) if "Defence5" in r)
    extra = [("total", "Total Public Sector Spending2 "), ("current", "Current spending3"),
             ("investment", "Public sector gross investment4"), ("pensioners", "o/w pensioners"),
             ("nonpensioners", "o/w non-pensioners"), ("other", "Other Public Sector Spending10 ")]
    areas = year_rows(rows, header, 1, sheet, [(k, label) for k, label, _ in LONG_AREAS] + extra, ("-",))

    checks = []  # The schema ledger checks raw operands, missingness and residuals.

    for d in (totals, areas):
        for y in d:
            for v in d[y].values():
                v.pop("raw")
    return {
        "decades": DECADES,
        "totals": [{"id": k, "official": label.replace("\n", " "), "plain": plain,
                    "values": {y: totals[y][k] for y in DECADES}} for k, label, plain in LONG_TOTALS],
        "areas": [{"id": k, "official": label.rstrip("0123456789"), "plain": plain,
                   "values": {y: areas[y][k] for y in DECADES if y in areas}} for k, label, plain in LONG_AREAS],
        "areas_last_year": max(areas),
    }, checks


def build_data():
    """Read and validate the retained workbooks without changing any files."""
    sources = json.loads((ROOT / "data/sources.json").read_text())
    verify(sources)
    ch4 = ROOT / sources["pesa_ch4"]["file"]
    ch5 = ROOT / sources["pesa_ch5"]["file"]

    aggregate_rows = grid(ch4, "4_1")
    context = pesa_context(aggregate_rows)
    agg = aggregates(aggregate_rows)
    nominal, years = function_table(grid(ch4, "4_2"), "4_2")
    real, _ = function_table(grid(ch4, "4_3"), "4_3")
    gdp, _ = function_table(grid(ch4, "4_4"), "4_4")
    detail, _ = function_table(grid(ch5, "5_2"), "5_2", scale=0.001)  # £ million to £ billion

    checks = []

    functions = []
    for key, official, plain in FUNCTIONS:
        n, r, g = find(nominal, official), find(real, official), find(gdp, official)
        functions.append({
            "id": key, "official": official.split(". ", 1)[-1], "plain": plain,
            "note": NOTES.get(key),
            "series": {
                y: {
                    "nominal": {"v": n["values"][y], "ref": n["refs"][y]},
                    "real": {"v": r["values"][y], "ref": r["refs"][y]},
                    "gdp": {"v": g["values"][y], "ref": g["refs"][y]},
                } for y in years
            },
        })

    services = find(nominal, "Public sector expenditure on services")
    interest = find(nominal, "of which: public sector debt interest")
    details = []
    for key, label, plain in DETAIL:
        row = find(detail, label)
        details.append({"id": key, "official": label.replace("of which: ", ""), "plain": plain,
                        "v": round(required(row["values"][LAST_OUTTURN], f"5.2 {label}, {LAST_OUTTURN}"), 1), "ref": row["refs"][LAST_OUTTURN]})
    details.sort(key=lambda d: -d["v"])

    # PESA's "debt interest" line is Table 5.2's "public debt transactions", which also
    # includes Bank of England and public sector pension items. Show the parts.
    debt_total = find(detail, "1.7 Public debt transactions")
    debt_parts = []
    for label in ("of which: central government debt interest", "of which: local government debt interest",
                  "of which: public corporation debt interest", "of which:Bank of England",
                  "of which: public sector pensions"):
        row = find(detail, label, after=debt_total["row"])
        debt_parts.append({"official": label.split(":", 1)[1].strip(),
                           "v": round(row["values"][LAST_OUTTURN], 1), "ref": row["refs"][LAST_OUTTURN]})
    # Reconcile the unrounded integer-million debt parts in the schema ledger.

    history, more = long_run(sources, agg)
    checks += more

    out = {
        "sources": sources,
        "base_year": BASE_YEAR,
        "pesa_context": context,
        "latest_year": LAST_OUTTURN,
        "checks": checks,
        "aggregates": agg,
        "years": years,
        "functions": functions,
        "services_total": {y: {"v": services["values"][y], "ref": services["refs"][y]} for y in years},
        "debt_interest": {y: {"v": interest["values"][y], "ref": interest["refs"][y]} for y in years},
        "details": details,
        "debt_parts": debt_parts,
        "history": history,
    }
    out["product_source"] = {
        "repository": "jnyross/un-political",
        "revision": "8eb81d6c7075e4b4e89e4aa1cc398fbae12eb713",
    }
    out["status_notes"] = {
        "pesa": "PESA outturn through 2025-26; later aggregate years are forecasts. Outturn can be revised.",
        "obr_databank": "Historical actual/estimate status is uncertain. Series-specific numerator and denominator update notes are retained, including conflicting March/October forecast notes B2/B139/B144/B148.",
        "obr_hist": "Joined historical series; actual/estimate status uncertain; not National Statistics. Displayed decades stop at 2015-16. Contents D51:D56 describe extrapolated 2022-23 values.",
        "missing": "Blank cells and dash markers remain missing; required missing operands stop the build.",
    }
    out["checks"] = [
        "Each value is checked against its source label, year, unit and accounting scope.",
        "PESA sums use stored source rounding steps. The data file shows each residual and its budget.",
        "OBR identities use stored ratios, not the one-decimal values shown on the page.",
        "A sum with missing operands is not tested. The data file names each missing cell.",
        "OBR and PESA use different vintages. Their difference has no established error bound.",
    ]
    return enrich(out)
