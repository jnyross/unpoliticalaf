"""UK productivity beside the other G7 countries (ONS international comparisons, final estimates).

One workbook, downloaded byte for byte by scripts/fetch_sources.py
(data/fetched/ons/icproductivityupdated.xlsx). It holds output per hour worked and
output per worker for the G7, in two forms:

- levels in pounds at current prices, converted with purchasing power parities
  (Tables 9 and 13), for 1997 to 2021;
- volume indexes, after inflation, 2019 = 100 (Tables 7 and 12).

The ONS published this series until 2024 and then stopped, so 2021 is the latest
year. Japan has no 2021 figure. The workbook shows 0 in the index tables for it;
0 is not a value here, so it is read as no figure. Every figure keeps its cell
(sheet!cell) as its locator, so check.py can re-read it.

Trends are rebased to 2008 = 100 from the 2019 = 100 index, which keeps each
country's own movement and does not change any ratio between countries.
"""
from .data import Fact
from .readers import xlsx

FILE = "data/fetched/ons/icproductivityupdated.xlsx"
SOURCE = "ons-icp"

# Workbook column names to ISO codes, and the order they appear in the sheets.
COUNTRIES = {"UK": "GBR", "US": "USA", "France": "FRA", "Germany": "DEU", "Italy": "ITA", "Canada": "CAN", "Japan": "JPN"}
NAMES = {"GBR": "UK", "USA": "United States", "DEU": "Germany", "FRA": "France", "ITA": "Italy", "CAN": "Canada", "JPN": "Japan"}
G7 = ["GBR", "CAN", "FRA", "DEU", "ITA", "JPN", "USA"]
OTHERS = ["CAN", "FRA", "DEU", "ITA", "USA"]  # the other G7 countries with a figure in every year from 2008
BASE = 2008
TABLES = {
    # sheet: (fact prefix, unit, index table?)
    "Table_9": ("prod.oph", "£ per hour worked, current prices", False),
    "Table_13": ("prod.opw", "£ per worker, current prices", False),
    "Table_7": ("prod.ohv", "index, 2019 = 100 (after inflation)", True),
    "Table_12": ("prod.opv", "index, 2019 = 100 (after inflation)", True),
}


def _table(sheet):
    """{(iso, year): (value, cell)} for one sheet, reading the header row for country names."""
    ws = xlsx(FILE)[sheet]
    rows = list(ws.iter_rows())
    head_row = next(r for r in rows if r[0].value == "Year")
    cols = {c.value: c.column_letter for c in head_row[1:] if c.value in COUNTRIES}
    out = {}
    for r in rows[head_row[0].row:]:
        y = r[0].value
        if not isinstance(y, (int, float)):
            continue
        for name, letter in cols.items():
            v = ws[f"{letter}{r[0].row}"].value
            out[(COUNTRIES[name], int(y))] = (None if v is None else float(v), f"{letter}{r[0].row}")
    return out


def _add(facts, fid, value, unit, period, locator, status="published", formula="", inputs=()):
    facts.add(Fact(fid, value, unit, str(period), SOURCE, locator, status, formula=formula, inputs=list(inputs)))


def build(facts):
    years = set()
    series = {}
    for sheet, (prefix, unit, _index) in TABLES.items():
        t = _table(sheet)
        for (iso, y), (v, cell) in t.items():
            if v is None or v == 0:
                continue  # a blank, or the workbook's 0 placeholder for Japan in 2021: no figure
            fid = f"{prefix}.{iso}.{y}"
            _add(facts, fid, v, unit, y, f"{sheet}!{cell}")
            series[fid] = v
            if prefix == "prod.oph" or prefix == "prod.ohv":
                years.add(y)
    latest = max(y for y in years if all(f"prod.oph.{iso}.{y}" in series for iso in ["GBR", "USA", "FRA", "DEU"]))
    out = {"latest": latest, "names": NAMES, "years": sorted(years)}

    # Japan has no figure for the latest year; the chart and table say so.
    out["missing_latest"] = [iso for iso in G7 if f"prod.oph.{iso}.{latest}" not in series]

    # Rebased trends: 2008 = 100, from the 2019 = 100 volume index.
    base_ok = [iso for iso in G7 if f"prod.ohv.{iso}.{BASE}" in series]
    for iso in base_ok:
        for y in range(BASE, latest + 1):
            fid = f"prod.ohv.{iso}.{y}"
            if fid not in series:
                continue
            v = 100 * series[fid] / series[f"prod.ohv.{iso}.{BASE}"]
            tid = f"prod.trend.{iso}.{y}"
            _add(facts, tid, v, "index, 2008 = 100 (after inflation)", y, facts[fid].locator, "calculated",
                 formula=f"100 × {fid} ÷ {fid.rsplit('.', 1)[0]}.{BASE}", inputs=[fid, f"prod.ohv.{iso}.{BASE}"])
            series[tid] = v

    # Average of the other G7 countries, each counted equally, for the years all five have a figure.
    trend_years = []
    for y in range(BASE, latest + 1):
        ids = [f"prod.trend.{iso}.{y}" for iso in OTHERS]
        if all(i in series for i in ids):
            trend_years.append(y)
            v = sum(series[i] for i in ids) / len(ids)
            _add(facts, f"prod.trend.avg5.{y}", v, "index, 2008 = 100 (after inflation)", y, facts[ids[0]].locator, "calculated",
                 formula="mean of " + ", ".join(ids), inputs=ids)
            series[f"prod.trend.avg5.{y}"] = v
    out["trend_years"] = trend_years
    for fid in [k for k in list(series) if k.startswith("prod.trend.")]:
        y = int(fid.rsplit(".", 1)[1])
        _add(facts, "prod.change." + fid[len("prod.trend."):], series[fid] - 100, "% change since 2008", y, facts[fid].locator,
             "calculated", formula=f"{fid} − 100", inputs=[fid])

    # UK output per hour over the whole ONS series, from its first year to the latest (impartiality rule: first and latest year).
    uk_years = sorted(int(k.rsplit(".", 1)[1]) for k in series if k.startswith("prod.ohv.GBR.") and k.rsplit(".", 1)[1].isdigit())
    if uk_years and f"prod.ohv.GBR.{latest}" in series:
        first_uk = uk_years[0]
        out["uk_first"] = first_uk
        full = 100 * series[f"prod.ohv.GBR.{latest}"] / series[f"prod.ohv.GBR.{first_uk}"] - 100
        _add(facts, f"prod.fullchange.GBR.{latest}", full, f"% change since {first_uk}", latest,
             facts[f"prod.ohv.GBR.{latest}"].locator, "calculated",
             formula=f"100 × prod.ohv.GBR.{latest} ÷ prod.ohv.GBR.{first_uk} − 100",
             inputs=[f"prod.ohv.GBR.{latest}", f"prod.ohv.GBR.{first_uk}"])

    # How far UK output per hour is below each country, in the latest year (levels).
    uk = series.get(f"prod.oph.GBR.{latest}")
    for iso in G7:
        other = series.get(f"prod.oph.{iso}.{latest}")
        if iso != "GBR" and uk and other:
            _add(facts, f"prod.below.{iso}.{latest}", 100 * (1 - uk / other), "% lower", latest,
                 facts[f"prod.oph.GBR.{latest}"].locator, "calculated",
                 formula=f"100 × (1 − prod.oph.GBR.{latest} ÷ prod.oph.{iso}.{latest})",
                 inputs=[f"prod.oph.GBR.{latest}", f"prod.oph.{iso}.{latest}"])
    return out
