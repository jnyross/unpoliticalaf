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


# ---------------------------------------------------------------- schools: large classes, infant and key stage 2

CLASS_API_FILE = "data/life/sources/schools/dfe-national-class-sizes-1.0.json"
CLASS_BANDS = {"zeoRF": "le30", "kxKDh": "31to35", "u2cKo": "36plus", "XdTUf": "total"}
CLASS_TYPES = {"TaWMP": "infant", "cDwC3": "ks2", "5kyxd": "primary", "tfHTE": "secondary"}


def class_detail(facts):
    """Large classes (more than 30 pupils) and infant / key stage 2 averages, England.

    January 2006 to 2015: DfE SFR16/2015 Table 6b, percentage of pupils in classes of
    31-35 and of 36 or more (primary and secondary only). January 2016 onwards: the DfE
    class sizes API, pupils in each class-size band for infant, key stage 2, primary
    and secondary classes. Both count classes taught by one teacher in state-funded schools."""
    out = {"large": {}, "infant": {}, "ks2": {}}
    rows = [[c.value for c in r] for r in xlsx("data/fetched/dfe/spc-2015-national-tables.xlsx")["Table 6b"].iter_rows()]
    yr_i = next(i for i, r in enumerate(rows) if any(str(v).strip() == "2006" for v in r if v))
    ycols = {int(str(v).strip()): j for j, v in enumerate(rows[yr_i]) if v and re.fullmatch(r"\d{4}", str(v).strip())}

    def find(label, start):
        return next(i for i in range(start, len(rows)) if any(str(v).strip() == label for v in rows[i] if v))
    for phase, head in (("primary", "STATE-FUNDED PRIMARY SCHOOLS (1)(2)"), ("secondary", "STATE-FUNDED SECONDARY SCHOOLS (1)(3)")):
        start = find(head, 0)
        pupils = find("Percentage of pupils in classes with", start)
        r31, r36 = find("31-35 pupils", pupils), find("36 or more pupils", pupils)
        for y, j in ycols.items():
            ids = []
            for band, i in (("31to35", r31), ("36plus", r36)):
                fid = f"school.pctpupils.{phase}.{band}.{y}"
                facts.add(Fact(fid, num(rows[i][j]), "% of pupils", f"January {y} census", "dfe-spc-2015-tables", f"Table 6b!{ref(i, j)}", "published"))
                ids.append(fid)
            facts.add(Fact(f"school.large.{phase}.{y}", facts[ids[0]].value + facts[ids[1]].value, "% of pupils in classes of more than 30",
                           f"January {y} census ({y - 1}/{str(y)[2:]} school year)", "dfe-spc-2015-tables", facts[ids[0]].locator, "calculated",
                           formula=f"{ids[0]} + {ids[1]}", inputs=ids, note="Sum of two percentages each rounded by DfE to 1 decimal place."))
            out["large"].setdefault(phase, {})[y] = f"school.large.{phase}.{y}"
    import json
    data = json.loads((ROOT / CLASS_API_FILE).read_text())
    cells = {}
    for k, r in enumerate(data["results"]):
        band, kind = CLASS_BANDS.get(r["filters"].get("cAd31")), CLASS_TYPES.get(r["filters"].get("5cGdi"))
        if band and kind:
            cells[(kind, band, int(r["timePeriod"]["period"][-4:]))] = k
    for (kind, band, y), k in sorted(cells.items(), key=lambda kv: (kv[0][2], kv[0][0], kv[0][1])):
        period = data["results"][k]["timePeriod"]["period"]
        facts.add(Fact(f"school.pupils.{kind}.{band}.{y}", float(data["results"][k]["values"]["QtxWw"]), "pupils",
                       f"January {y} census ({period[:4]}/{period[-2:]} school year)", "dfe_api", f"results[{k}] values.QtxWw", "published"))
        if band == "total" and kind in ("infant", "ks2"):
            v = round(float(data["results"][k]["values"]["Wc9V2"]), 1)
            facts.add(Fact(f"school.{kind}.{y}", v, "pupils per class", f"January {y} census ({period[:4]}/{period[-2:]} school year)", "dfe_api",
                           f"results[{k}] values.Wc9V2", "published", note="API gives unrounded value; rounded to 1 decimal place as in DfE publications."))
            out[kind][y] = f"school.{kind}.{y}"
    for kind in CLASS_TYPES.values():
        for y in sorted({yy for (kk, _, yy) in cells if kk == kind}):
            ids = [f"school.pupils.{kind}.{b}.{y}" for b in ("31to35", "36plus", "total")]
            if not all(i in facts for i in ids):
                continue
            big = f"school.pupils.{kind}.over30.{y}"
            facts.add(Fact(big, facts[ids[0]].value + facts[ids[1]].value, "pupils in classes of more than 30", facts[ids[2]].period, "dfe_api",
                           facts[ids[0]].locator, "calculated", formula=f"{ids[0]} + {ids[1]}", inputs=ids[:2]))
            fid = f"school.large.{kind}.{y}"
            facts.add(Fact(fid, 100 * facts[big].value / facts[ids[2]].value, "% of pupils in classes of more than 30", facts[ids[2]].period, "dfe_api",
                           facts[ids[2]].locator, "calculated", formula=f"100 × {big} ÷ {ids[2]}", inputs=[big, ids[2]]))
            out["large"].setdefault(kind, {})[y] = fid
    return {k: ({p: dict(sorted(v.items())) for p, v in d.items()} if k == "large" else dict(sorted(d.items()))) for k, d in out.items()}


# ---------------------------------------------------------------- holidays: spending and nights abroad

def _ott_years_table(path, sheet, source, header_col, scale):
    """Region heading rows then purpose rows, one column per year; the first column for each year
    wins (table 3.05 repeats the years for average length of stay)."""
    rows = [[c.value for c in r] for r in xlsx(path)[sheet].iter_rows()]
    hdr_i = next(i for i, r in enumerate(rows) if len(r) > header_col and str(r[header_col]).strip() == "2009")
    years = {}
    for j, v in enumerate(rows[hdr_i]):
        if v is not None and re.fullmatch(r"\d{4}", str(v).strip()) and int(str(v).strip()) not in years:
            years[int(str(v).strip())] = j
    region, out = None, {}
    for i in range(hdr_i + 1, len(rows)):
        a = str(rows[i][0]).strip() if rows[i][0] else ""
        if a and all(v is None for v in rows[i][2:13]):
            region = a
            continue
        if a and region:
            for y, j in years.items():
                out[(region, a, y)] = (num(rows[i][j]), f"{sheet}!{ref(i, j)}", source, scale)
    return out


def _ott_new_table(path, sheet, source, col_for_year, scale):
    """2019 to 2023 layout: region, purpose, then a column per year (headers like '2019' or 'Nights\n2019')."""
    rows = [[c.value for c in r] for r in xlsx(path)[sheet].iter_rows()]
    hdr_i = next(i for i, r in enumerate(rows) if r[0] and str(r[0]).strip() == "Region of Visit")
    years = {}
    for j, v in enumerate(rows[hdr_i]):
        m = re.fullmatch(col_for_year, str(v).strip()) if v is not None else None
        if m:
            years[int(m.group(1))] = j
    out = {}
    for i in range(hdr_i + 1, len(rows)):
        if rows[i][0] and rows[i][1]:
            for y, j in years.items():
                out[(str(rows[i][0]).strip(), str(rows[i][1]).strip(), y)] = (num(rows[i][j]), f"{sheet}!{ref(i, j)}", source, scale)
    return out


def _ott_annual_cols(path, source, year):
    """2024 onwards: table 2 with Visits, Spending and Nights columns for one year."""
    rows = [[c.value for c in r] for r in xlsx(path)["2"].iter_rows()]
    hdr_i = next(i for i, r in enumerate(rows) if r[0] and str(r[0]).strip() == "Region of Visit")
    head = [str(v).strip() if v else "" for v in rows[hdr_i]]
    js, jn = head.index("Spending"), head.index("Nights")
    spend, nights = {}, {}
    for i in range(hdr_i + 1, len(rows)):
        if rows[i][0] and rows[i][1]:
            key = (str(rows[i][0]).strip(), str(rows[i][1]).strip(), year)
            spend[key] = (num(rows[i][js]), f"2!{ref(i, js)}", source, 1)
            nights[key] = (num(rows[i][jn]), f"2!{ref(i, jn)}", source, 0.001)
    return spend, nights


def holiday_spend(facts):
    """ONS Travel trends: spending on and nights of holiday visits abroad, with spending
    per visit (also in 2025 prices, using annual CPIH) and average nights per visit."""
    old_s = _ott_years_table("data/fetched/ott/section3-2009to2019.xlsx", "3.04", "ott-2009to2019", 2, 1)
    old_n = _ott_years_table("data/fetched/ott/section3-2009to2019.xlsx", "3.05", "ott-2009to2019", 2, 1)
    # 2019 appears in both files: the later publication (2019 to 2023) is used, as for visits
    old_s.update(_ott_new_table("data/fetched/ott/section3-2019to2023.xlsx", "3", "ott-2019to2023", r"(\d{4})", 1))
    old_n.update(_ott_new_table("data/fetched/ott/section3-2019to2023.xlsx", "4", "ott-2019to2023", r"Nights\s+(\d{4})", 0.001))
    for y, path, sid in ((2024, "data/fetched/ott/ukresidents2024annual.xlsx", "ott-2024"), (2025, "data/fetched/ott/ukresidents2025annual.xlsx", "ott-2025")):
        if (ROOT / path).exists():
            s, n = _ott_annual_cols(path, sid, y)
            old_s.update(s)
            old_n.update(n)
    _, cpih = ons_series("data/fetched/ons/l522.csv")
    years = sorted({y for (r, p, y) in old_s if r == "Total World" and p in ("Holiday", "Holiday - All")})
    base_year = years[-1]

    def cpih_fact(y):
        fid = f"cpih.cal.{y}"
        if fid not in facts:
            facts.add(Fact(fid, cpih.get(str(y)), "index (2015=100)", f"{y} (calendar year average)", "ons-l522", f"L522 row '{y}'"))
        return fid
    out = {"years": [], "base": base_year}
    for y in years:
        basis = "UK residents" if y <= 2023 else "Great Britain residents"
        for key, cells, unit in (("spend", old_s, "£ million"), ("nights", old_n, "thousand nights")):
            cand = next((c for c in (("Total World", "Holiday - All", y), ("Total World", "Holiday", y)) if c in cells), None)
            fid = f"hol.{key}.holiday.{y}"
            if cand is None or cells[cand][0] is None:
                facts.add(Fact(fid, None, unit, str(y), (cells[cand][2] if cand else "ott-2019to2023"), "not published", "missing",
                               note="Not available in the source for this year (survey suspended in 2020)."))
                continue
            v, loc, sid, scale = cells[cand]
            facts.add(Fact(fid, v * scale, unit, str(y), sid, loc, "published", note=f"{basis}; Total World, holiday visits", scale=scale))
        sp, ni, vi = f"hol.spend.holiday.{y}", f"hol.nights.holiday.{y}", f"hol.world.holiday.{y}"
        if facts[sp].value is None or vi not in facts or facts[vi].value is None:
            continue
        out["years"].append(y)
        facts.add(Fact(f"hol.spendbn.holiday.{y}", facts[sp].value / 1000, "£ billion", str(y), facts[sp].source, facts[sp].locator,
                       "calculated", formula=f"{sp} ÷ 1000", inputs=[sp]))
        facts.add(Fact(f"hol.spendper.{y}", 1000 * facts[sp].value / facts[vi].value, "£ per holiday visit (cash)", str(y), facts[sp].source, facts[sp].locator,
                       "calculated", formula=f"1000 × {sp} ÷ {vi}", inputs=[sp, vi], note="Spending in £ million divided by visits in thousands."))
        facts.add(Fact(f"hol.spendper.real.{y}", facts[f"hol.spendper.{y}"].value * cpih[str(base_year)] / cpih[str(y)], f"£ per holiday visit, {base_year} prices",
                       str(y), facts[sp].source, facts[sp].locator, "calculated", formula=f"hol.spendper.{y} × {cpih_fact(base_year)} ÷ {cpih_fact(y)}",
                       inputs=[f"hol.spendper.{y}", f"cpih.cal.{base_year}", f"cpih.cal.{y}"]))
        if facts[ni].value is not None:
            facts.add(Fact(f"hol.stay.{y}", facts[ni].value / facts[vi].value, "nights per holiday visit", str(y), facts[ni].source, facts[ni].locator,
                           "calculated", formula=f"{ni} ÷ {vi}", inputs=[ni, vi]))
    return out


def build(facts):
    return {"spread": pay_spread(facts), "afford": affordability(facts), "jobs": jobs_by_industry(facts),
            "holafford": holiday_afford(facts), "classes": class_detail(facts), "holspend": holiday_spend(facts)}
