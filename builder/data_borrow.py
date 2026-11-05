"""UK government debt and borrowing costs beside the other G7 countries.

Three downloads, kept byte for byte by scripts/fetch_sources.py:

- OECD Government at a Glance, yearly updates (all measures, G7 and the OECD
  average): general government gross debt, net interest spending and revenue, % of
  GDP, 2007 onwards. Debt here follows the System of National Accounts, which counts
  government bonds at their market price.
- OECD Financial market statistics: long-term interest rates, which for every G7
  country are the yields on 10-year government bonds, yearly and monthly averages.
- IMF DataMapper, general government gross debt (% of GDP, GG_DEBT_GDP), the IMF's
  historical series, 1950 to 2024.

All are calendar years (or months) and general government, so they differ from the
UK financial-year public sector figures on other pages. They are never joined.
Every figure keeps its CSV line (or JSON path) as its locator, so check.py can
re-read it.
"""

import csv
import io
import json

from .data import Fact, num
from .readers import ROOT

PF_FILE = "data/fetched/oecd/gov-at-a-glance-all-measures-g7.csv"
YIELD_FILE = "data/fetched/oecd/finmark-long-term-rates-g7.csv"
IMF_FILE = "data/fetched/imf/weo-gg-debt-gdp.json"
PF_SRC, YIELD_SRC, IMF_SRC = "oecd-gov-pf-g7", "oecd-finmark-irlt", "imf-weo-debt"

UK, AVG = "GBR", "OECD_REP"
G7 = ["CAN", "FRA", "DEU", "ITA", "JPN", "GBR", "USA"]
NAMES = {
    "CAN": "Canada",
    "FRA": "France",
    "DEU": "Germany",
    "ITA": "Italy",
    "JPN": "Japan",
    "GBR": "United Kingdom",
    "USA": "United States",
    AVG: "OECD average",
}
# Government at a Glance measures used, all as % of GDP.
PF_MEASURES = {"GGD": "debt", "GGINTN": "int", "GR": "rev"}
MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def _rows(path):
    lines = list(csv.reader(io.StringIO((ROOT / path).read_text(encoding="utf-8-sig"))))
    head = lines[0]
    return [(i + 1, dict(zip(head, r))) for i, r in enumerate(lines) if i > 0]


def _latest(have, areas):
    """Latest period with a figure for every one of these areas."""
    periods = {p for (_, p) in have}
    ok = [p for p in periods if all(have.get((a, p)) is not None for a in areas)]
    return max(ok) if ok else None


def month_name(ym):
    y, m = ym.split("-")
    return f"{MONTHS[int(m) - 1]} {y}"


def build(facts):
    out = {"g7": G7, "names": NAMES}

    # Government at a Glance: debt, net interest and revenue, % of GDP.
    pf = {k: {} for k in PF_MEASURES.values()}
    for line, r in _rows(PF_FILE):
        k = PF_MEASURES.get(r["MEASURE"])
        a, y = r["REF_AREA"], r["TIME_PERIOD"]
        if not k or r["UNIT_MEASURE"] != "PT_B1GQ" or a not in NAMES:
            continue
        v = num(r["OBS_VALUE"])
        if v is None:
            continue
        status = "provisional" if r["OBS_STATUS"] == "P" else "published"
        facts.add(
            Fact(
                f"borrow.{k}.{a}.{y}",
                v,
                "% of GDP",
                y,
                PF_SRC,
                f"{a} {r['Measure']} % GDP line {line}",
                status,
                note="Provisional figure" if status == "provisional" else "",
            )
        )
        pf[k][(a, y)] = v
    for k in pf:
        out[f"{k}_year"] = _latest(pf[k], G7)
        out[f"{k}_years"] = sorted({y for (a, y) in pf[k] if a == UK and y <= out[f"{k}_year"]})

    # Net interest as a share of revenue, calculated: interest ÷ revenue × 100.
    for (a, y), v in pf["int"].items():
        rv = pf["rev"].get((a, y))
        if rv:
            i, rr = f"borrow.int.{a}.{y}", f"borrow.rev.{a}.{y}"
            facts.add(
                Fact(
                    f"borrow.intrev.{a}.{y}",
                    v / rv * 100,
                    "% of revenue",
                    y,
                    PF_SRC,
                    facts[i].locator,
                    "calculated",
                    formula=f"{i} ÷ {rr} × 100",
                    inputs=[i, rr],
                )
            )

    # 10-year government bond yields: yearly averages and the latest month.
    yearly, monthly = {}, {}
    for line, r in _rows(YIELD_FILE):
        a, p, f = r["REF_AREA"], r["TIME_PERIOD"], r["FREQ"]
        v = num(r["OBS_VALUE"])
        if a not in G7 or r["MEASURE"] != "IRLT" or v is None:
            continue
        if f == "A":
            yearly[(a, p)] = v
            facts.add(
                Fact(
                    f"borrow.yield.{a}.{p}",
                    v,
                    "% a year",
                    p,
                    YIELD_SRC,
                    f"{a} long-term interest rate, yearly average line {line}",
                )
            )
        elif f == "M":
            monthly[(a, p)] = (v, line)
    out["yield_year"] = _latest(yearly, G7)
    out["yield_years"] = sorted({y for (a, y) in yearly if y <= out["yield_year"]})
    ym = _latest({k: v[0] for k, v in monthly.items()}, G7)
    out["yield_month"] = ym
    for a in G7:
        v, line = monthly[(a, ym)]
        facts.add(
            Fact(
                f"borrow.yieldm.{a}.{ym}",
                v,
                "% a year",
                ym,
                YIELD_SRC,
                f"{a} long-term interest rate, monthly average line {line}",
            )
        )
    out["yield_month_name"] = month_name(ym)

    # IMF: general government gross debt, % of GDP, the IMF's historical series.
    imf = json.loads((ROOT / IMF_FILE).read_text())["values"]["GG_DEBT_GDP"]
    have = {}
    for a in G7:
        for y, v in imf.get(a, {}).items():
            if v is None:
                continue
            facts.add(
                Fact(
                    f"borrow.imf.{a}.{y}",
                    float(v),
                    "% of GDP",
                    y,
                    IMF_SRC,
                    f"values.GG_DEBT_GDP.{a}.{y}",
                )
            )
            have[(a, y)] = v
    out["imf_year"] = _latest(have, G7)
    out["imf_from"] = "1990"
    out["imf_years"] = [str(y) for y in range(int(out["imf_from"]), int(out["imf_year"]) + 1)]
    return out
