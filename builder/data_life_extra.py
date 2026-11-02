"""Three longer-run life measures: how far apart pay is, house prices against
earnings, and jobs by industry.

Each keeps its own run of years, set by its source, rather than the year
explorer's range, so nothing is cut short or stretched.

- Pay spread: ASHE resident analysis (via Nomis), gross weekly pay of full-time
  employees at the 10th, 50th and 90th percentiles, April 2002 onwards.
- House prices against earnings: ONS ratio of median house price to median
  full-time workplace-based annual earnings, England and Wales, 1997 onwards.
- Jobs by industry: ONS JOBS02 workforce jobs by industry (SIC 2007),
  seasonally adjusted, United Kingdom, June each year from 1978.
"""
import re

import xlrd

from .data import Fact, REGIONS, num
from .readers import ROOT, csv_rows, ons_series, ref, xlsx

# ---------------------------------------------------------------- pay spread

SPREAD_FILE = "data/fetched/nomis/ashe-resident-uk-weekly-percentiles.csv"
SPREAD_ITEMS = {"6": "p10", "2": "p50", "15": "p90"}
# ONS: ASHE has breaks in 2004, 2006 and 2011 (ASHE QMI) and 2021 (SOC2020 coding).
SPREAD_BREAKS = {2004: "Method change", 2006: "Method change", 2011: "Coding change", 2021: "Coding change"}


def pay_spread(facts):
    rows = csv_rows(SPREAD_FILE)
    _, cpih = ons_series("data/fetched/ons/l522.csv")
    years = sorted({int(r["DATE_NAME"]) for r in rows})
    base_year = years[-1]
    base_id = f"cpih.apr.{base_year}"
    if base_id not in facts:
        facts.add(Fact(base_id, cpih[f"{base_year} APR"], "index (2015=100)", f"April {base_year}", "ons-l522", f"L522 row '{base_year} APR'"))
    out = {"years": years, "base_year": base_year, "breaks": SPREAD_BREAKS}
    for line, r in enumerate(rows, start=2):
        key = SPREAD_ITEMS.get(r["ITEM"])
        if r["SEX"] != "8" or key is None or r["MEASURES_NAME"] != "Value":
            continue
        y = int(r["DATE_NAME"])
        fid = f"spread.{key}.{y}"
        st = "provisional" if y == base_year else "published"
        facts.add(Fact(fid, num(r["OBS_VALUE"]), "£ a week", f"April {y}", "nomis-ashe-percentiles", f"{SPREAD_FILE.split('/')[-1]} line {line}", st,
                       note=f"Full-time employees, gross weekly pay, {r['ITEM_NAME']}"))
        cid = f"cpih.apr.{y}"
        if cid not in facts:
            facts.add(Fact(cid, cpih.get(f"{y} APR"), "index (2015=100)", f"April {y}", "ons-l522", f"L522 row '{y} APR'"))
        v, idx = facts[fid].value, facts[cid].value
        facts.add(Fact(f"spread.real.{key}.{y}", None if v is None or idx is None else v * facts[base_id].value / idx,
                       f"£ a week, April {base_year} prices", f"April {y}", "nomis-ashe-percentiles", facts[fid].locator, "calculated",
                       formula=f"{fid} × {base_id} ÷ {cid}", inputs=[fid, base_id, cid]))
    for y in years:
        hi, lo = facts[f"spread.p90.{y}"], facts[f"spread.p10.{y}"]
        facts.add(Fact(f"spread.ratio.{y}", None if hi.value is None or lo.value is None else hi.value / lo.value, "times", f"April {y}",
                       "nomis-ashe-percentiles", hi.locator, "calculated", formula=f"{hi.id} ÷ {lo.id}", inputs=[hi.id, lo.id]))
        facts.add(Fact(f"spread.gap.real.{y}", facts[f"spread.real.p90.{y}"].value - facts[f"spread.real.p10.{y}"].value
                       if None not in (facts[f"spread.real.p90.{y}"].value, facts[f"spread.real.p10.{y}"].value) else None,
                       f"£ a week, April {base_year} prices", f"April {y}", "nomis-ashe-percentiles", hi.locator, "calculated",
                       formula=f"spread.real.p90.{y} − spread.real.p10.{y}", inputs=[f"spread.real.p90.{y}", f"spread.real.p10.{y}"]))
    return out


# ---------------------------------------------------------------- house prices against earnings

AFFORD_FILE = "data/fetched/ons/affordability-workplace.xlsx"
AFFORD_PLACES = [("ew", "England and Wales", "K04000001"), ("england", "England", "E92000001"), ("wales", "Wales", "W92000004")] + list(REGIONS)
AFFORD_TABLES = {"1a": ("price", "£", "Median price paid for a home, year ending September"),
                 "1b": ("earn", "£ a year", "Median gross annual earnings of full-time employees working there"),
                 "1c": ("ratio", "times", "Median house price ÷ median full-time annual earnings")}


def _afford_year(head):
    m = re.search(r"(\d{4})$", str(head or "").strip())
    return int(m.group(1)) if m else None


def affordability(facts):
    wb = xlsx(AFFORD_FILE)
    codes = {code: key for key, _, code in AFFORD_PLACES}
    out = {"places": [(k, n) for k, n, _ in AFFORD_PLACES], "years": []}
    for sheet, (kind, unit, note) in AFFORD_TABLES.items():
        rows = [[c.value for c in row] for row in wb[sheet].iter_rows()]
        head_i = next(i for i, r in enumerate(rows) if r and r[0] == "Code")
        head = rows[head_i]
        cols = [(j, _afford_year(h)) for j, h in enumerate(head) if j >= 2 and _afford_year(h)]
        years = [y for _, y in cols]
        if kind == "ratio":
            out["years"] = years
        for i in range(head_i + 1, len(rows)):
            key = codes.get(rows[i][0])
            if not key:
                continue
            for j, y in cols:
                period = f"year ending September {y}" if kind == "price" else f"April {y}" if kind == "earn" else f"{y} (prices for the year ending September; earnings in April)"
                v = num(rows[i][j])
                facts.add(Fact(f"afford.{kind}.{key}.{y}", v, unit, period, "ons-affordability", f"{sheet}!{ref(i, j)}", "published",
                               note=f"{rows[i][1]}: {note}" + (" (annualised weekly earnings)" if y <= 1998 and kind != "price" else "")))
    return out


# ---------------------------------------------------------------- jobs by industry

JOBS_FILE = "data/fetched/ons/jobs02.xls"
JOBS_SHEET = "WFJ SA"
# Section letter -> short plain-English name
INDUSTRY_NAMES = {
    "A": "Farming, forestry and fishing", "B": "Mining and quarrying", "C": "Manufacturing", "D": "Electricity and gas supply",
    "E": "Water, sewerage and rubbish collection", "F": "Construction", "G": "Shops, wholesale and vehicle repair", "H": "Transport and storage",
    "I": "Hotels, restaurants and pubs", "J": "Information and communication", "K": "Finance and insurance", "L": "Property (real estate)",
    "M": "Professional, scientific and technical", "N": "Administrative and support services", "O": "Public administration and defence",
    "P": "Education", "Q": "Health and social work", "R": "Arts, entertainment and recreation", "S": "Other services",
    "T": "Private households as employers",
}


def jobs_by_industry(facts):
    sh = xlrd.open_workbook(str(ROOT / JOBS_FILE)).sheet_by_name(JOBS_SHEET)
    letters = sh.row_values(4)
    col = {str(v).strip(): j for j, v in enumerate(letters) if str(v).strip()}
    total_j = col["A-T"]
    out = {"years": [], "sections": [s for s in INDUSTRY_NAMES if s in col], "names": INDUSTRY_NAMES, "provisional": None}
    for i in range(5, sh.nrows):
        label = str(sh.cell_value(i, 0)).strip()
        m = re.fullmatch(r"Jun (\d\d)\s*(\(p\))?", label)
        if not m:
            continue
        y = 1900 + int(m.group(1)) if int(m.group(1)) >= 50 else 2000 + int(m.group(1))
        st = "provisional" if m.group(2) else "published"
        if m.group(2):
            out["provisional"] = y
        out["years"].append(y)
        total = facts.add(Fact(f"jobs.total.{y}", num(sh.cell_value(i, total_j)), "thousand jobs", f"June {y}", "ons-jobs02",
                               f"{JOBS_SHEET}!{ref(i, total_j)}", st, note="All workforce jobs (sections A to T), seasonally adjusted"))
        for s in out["sections"]:
            j = col[s]
            part = facts.add(Fact(f"jobs.ind.{s}.{y}", num(sh.cell_value(i, j)), "thousand jobs", f"June {y}", "ons-jobs02",
                                  f"{JOBS_SHEET}!{ref(i, j)}", st, note=f"Section {s}: {INDUSTRY_NAMES[s]}, seasonally adjusted"))
            facts.add(Fact(f"jobs.share.{s}.{y}", None if part.value is None or not total.value else 100 * part.value / total.value,
                           "% of all workforce jobs", f"June {y}", "ons-jobs02", part.locator, "calculated",
                           formula=f"100 × {part.id} ÷ {total.id}", inputs=[part.id, total.id]))
    return out


# ---------------------------------------------------------------- holidays: who could afford a week away?

HOLIDAY_AFFORD_FILE = "data/fetched/eurostat/ilc-mdes02-uk.json"
# (fact key, Eurostat household composition code, poverty-threshold code, label)
HOLIDAY_AFFORD_GROUPS = [
    ("all", "TOTAL", "TOTAL", "Everyone"),
    ("low", "TOTAL", "B_60", "People in households with low income (below 60% of the middle income)"),
    ("notlow", "TOTAL", "A_60", "People in other households"),
    ("kids", "DCH", "TOTAL", "People in households with dependent children"),
    ("nokids", "NDCH", "TOTAL", "People in households without dependent children"),
]


def holiday_afford(facts):
    """Eurostat EU-SILC table ilc_mdes02 (JSON-stat): share of people in the UK whose
    household could not afford a week's annual holiday away from home. The UK sent
    EU-SILC data up to the 2018 survey only. Flag 'b' marks Eurostat's series breaks."""
    if not (ROOT / HOLIDAY_AFFORD_FILE).exists():
        return {"years": [], "breaks": [], "groups": HOLIDAY_AFFORD_GROUPS}
    import json
    data = json.loads((ROOT / HOLIDAY_AFFORD_FILE).read_text())
    dims, sizes = data["id"], data["size"]
    index = {d: data["dimension"][d]["category"]["index"] for d in dims}
    years_all = sorted(index["time"], key=lambda t: index["time"][t])
    flags = data.get("status", {})

    def key(**want):
        k = 0
        for d, n in zip(dims, sizes):
            code = want.get(d)
            pos = index[d][code] if code is not None else 0
            k = k * n + pos
        return k

    years, breaks = set(), set()
    for gk, hh, pov, _ in HOLIDAY_AFFORD_GROUPS:
        for t in years_all:
            k = key(freq="A", hhcomp=hh, rskpovth=pov, unit="PC", geo="UK", time=t)
            v = data["value"].get(str(k))
            if v is None:
                continue
            y = int(t)
            years.add(y)
            flag = flags.get(str(k), "")
            if "b" in flag:
                breaks.add(y)
            facts.add(Fact(f"holafford.{gk}.{y}", float(v), "% of people", f"EU-SILC {y} survey", "eurostat-ilc-mdes02-uk",
                           f"value[{k}]", "published",
                           note=f"Household composition {hh}, income group {pov}" + ("; Eurostat marks a break in series this year" if "b" in flag else "")))
    return {"years": sorted(years), "breaks": sorted(breaks), "groups": HOLIDAY_AFFORD_GROUPS}


def build(facts):
    return {"spread": pay_spread(facts), "afford": affordability(facts), "jobs": jobs_by_industry(facts),
            "holafford": holiday_afford(facts)}
