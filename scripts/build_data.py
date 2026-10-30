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

# Items from table 5.2 (2025-26 detail) shown as "the biggest single items".
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
    "economic": "Network Rail is only counted from 2015-16. From 2008-09 the figures include help "
                "for banks. From 2020-21 they include help during Covid and when prices rose fast. "
                "(PESA Table 4.2, notes 2 and 3)",
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
    for r in rows:
        if r["label"] == label and (after is None or r["row"] > after):
            return r
    raise KeyError(label)


def aggregates(rows):
    """Table 4.1: two header rows (group, then measure) above one row per year."""
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
        entry = {"year": year, "forecast": year > LAST_OUTTURN}
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


def reconcile(nominal, real, years, agg, detail_rows):
    checks = []
    names = [official for _, official, _ in FUNCTIONS]
    for y in years:
        parts = sum(required(find(nominal, n)["values"][y], f"4.2 {n}, {y}") for n in names)
        total = required(find(nominal, "Public sector expenditure on services")["values"][y], f"4.2 services, {y}")
        close(parts, total, 0.05 * len(names), f"4.2 functions sum to services total, {y}")
        adj = required(find(nominal, "Accounting adjustments")["values"][y], f"4.2 adjustments, {y}")
        tme = find(nominal, "Total Managed Expenditure")["values"][y]
        close(total + adj, tme, 0.1, f"4.2 services + adjustments = TME, {y}")
        a = next(e for e in agg if e["year"] == y)
        close(tme, a["tme"]["nominal"]["v"], 0.1, f"4.2 TME matches 4.1 TME, {y}")
    checks.append(f"Table 4.2: the 11 areas add up to spending on services in all {len(years)} years")
    checks.append("Table 4.2: spending on services plus accounting adjustments equals TME in every year")
    checks.append("Table 4.2 TME matches Table 4.1 TME in every year")

    for r in nominal:
        close(r["values"][BASE_YEAR], find(real, r["label"])["values"][BASE_YEAR], 0.05,
              f"4.3 equals 4.2 in base year for {r['label']}")
    checks.append(f"Table 4.3 (real terms) equals Table 4.2 (cash) in the base year {BASE_YEAR}")
    base = next(e for e in agg if e["year"] == BASE_YEAR)
    for key in ("tme", "current", "investment"):
        close(base[key]["nominal"]["v"], base[key]["real"]["v"], 0.05, f"4.1 {key} base year")
    checks.append(f"Table 4.1 real-terms figures equal cash figures in {BASE_YEAR}")

    totals = [r for r in detail_rows if r["label"].startswith("Total ")]
    for t in totals:
        name = t["label"][len("Total "):].lower()
        match = next((n for n in names if n.split(". ", 1)[-1].lower() == name), None)
        if match is None:
            continue
        for y, v in t["values"].items():
            if y in years:
                close(v, find(nominal, match)["values"][y], 0.06, f"5.2 total {name} matches 4.2, {y}")
    checks.append("Table 5.2 area totals match Table 4.2 for 2021-22 to 2025-26")
    return checks


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

    checks = []
    for y, t in totals.items():
        if all(t[k]["raw"] is not None for k in ("spending", "receipts", "borrowing")):
            close(t["spending"]["raw"] - t["receipts"]["raw"], t["borrowing"]["raw"], 0.01, f"OBR borrowing, {y}")
    checks.append(f"OBR databank: borrowing equals spending minus income in every year from {min(totals)} to {max(totals)}")
    for y, a in areas.items():
        raw = {k: v["raw"] for k, v in a.items()}
        if None not in (raw["total"], raw["current"], raw["investment"]):
            close(raw["current"] + raw["investment"], raw["total"], 0.01, f"OBR history current + investment, {y}")
        named = [raw[k] for k, _, _ in LONG_AREAS]
        if None not in named + [raw["total"], raw["other"]]:
            close(sum(named) + raw["other"], raw["total"], 0.01, f"OBR history areas add up, {y}")
    checks.append("OBR historical database: the five areas plus 'other' add up to total spending in every year that has all of them")
    pesa = next(e for e in agg if e["year"] == LAST_OUTTURN)["tme"]["gdp"]["v"]
    close(totals[LAST_OUTTURN]["spending"]["v"], pesa, 0.5, "OBR and PESA total spending share")
    checks.append(f"OBR total spending as a share of GDP in {LAST_OUTTURN} is within 0.5 points of the Treasury figure "
                  "(they differ slightly because the OBR file is newer)")

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

    agg = aggregates(grid(ch4, "4_1"))
    nominal, years = function_table(grid(ch4, "4_2"), "4_2")
    real, _ = function_table(grid(ch4, "4_3"), "4_3")
    gdp, _ = function_table(grid(ch4, "4_4"), "4_4")
    detail, _ = function_table(grid(ch5, "5_2"), "5_2", scale=0.001)  # £ million to £ billion

    checks = reconcile(nominal, real, years, agg, detail)

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
    close(sum(p["v"] for p in debt_parts), debt_total["values"][LAST_OUTTURN], 0.3, "5.2 debt parts")
    close(debt_total["values"][LAST_OUTTURN], interest["values"][LAST_OUTTURN], 0.06, "5.2 debt = 4.2 interest")
    checks.append("Table 5.2 debt items add up to the Table 4.2 debt interest line for 2025-26")

    history, more = long_run(sources, agg)
    checks += more

    out = {
        "sources": sources,
        "base_year": BASE_YEAR,
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
        "obr_databank": "October 2026 vintage. This port does not classify each historical cell as actual or estimate; consult the workbook notes.",
        "obr_hist": "Older joined historical series; not National Statistics. Missing cells remain null.",
        "missing": "Blank cells and dash markers remain missing; required missing operands stop the build.",
    }
    return out

