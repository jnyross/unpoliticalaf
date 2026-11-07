"""The UK beside other OECD countries: tax and government spending as a share of GDP.

Three OECD tables, downloaded byte for byte by scripts/fetch_sources.py:

- Revenue Statistics (comparative tables): total tax revenue and five main kinds of tax,
  % of GDP, 1965 onwards. Taxes include social security contributions (National
  Insurance in the UK) and exclude receipts that are not taxes.
- Government at a Glance, yearly updates: general government expenditure, % of GDP,
  2007 onwards.
- Government at a Glance, yearly updates: general government expenditure by function
  (COFOG), % of GDP, 2015 onwards.

All figures are calendar years and cover general government (central, devolved and
local government, not public corporations), so they differ from the UK financial-year
public sector figures on the other money pages. They are shown separately and never
joined. Every figure keeps its CSV line as its locator, so check.py can re-read it.
"""

import csv
import io

from .data import Fact, num
from .readers import ROOT

TAX_FILE = "data/fetched/oecd/revenue-statistics-tax-gdp.csv"
SPEND_FILE = "data/fetched/oecd/gov-at-a-glance-expenditure-revenue-gdp.csv"
COFOG_FILE = "data/fetched/oecd/gov-at-a-glance-expenditure-by-function-gdp.csv"
PIT_FILE = "data/fetched/oecd/pit-top-rates.csv"
TAX_SRC, SPEND_SRC, COFOG_SRC = "oecd-rs-tax", "oecd-gov-pf", "oecd-gov-cofog"
PIT_SRC = "oecd-pit-top-rates"

UK, AVG = "GBR", "OECD_REP"  # OECD_REP: the OECD's "OECD average country" (unweighted)
G7 = ["CAN", "FRA", "DEU", "ITA", "JPN", "GBR", "USA"]
DEFENCE = "GF02"

# Kinds of tax in the OECD's classification, with a plain name and the nearest UK taxes.
TAX_KINDS = [
    ("T_1100", "Taxes on people's income", "Income Tax, Capital Gains Tax"),
    ("T_2000", "Social security contributions", "National Insurance"),
    ("T_5000", "Taxes on goods and services", "VAT, fuel, alcohol and tobacco duties"),
    ("T_1200", "Taxes on company profits", "Corporation Tax"),
    ("T_4000", "Taxes on property", "Council Tax, business rates, Stamp Duty, Inheritance Tax"),
]

# COFOG functions, plain names as on the UK spending page.
FUNCTIONS = [
    ("GF10", "Social protection"),
    ("GF07", "Health"),
    ("GF09", "Education"),
    ("GF01", "General public services"),
    ("GF04", "Economic affairs"),
    ("GF03", "Public order and safety"),
    ("GF02", "Defence"),
    ("GF08", "Recreation, culture and religion"),
    ("GF06", "Housing and community amenities"),
    ("GF05", "Environmental protection"),
]

# Short English names, where the OECD's own label is long.
NAMES = {
    "Korea": "South Korea",
    "Slovak Republic": "Slovakia",
    "Türkiye": "Turkey",
    "OECD average country": "OECD average",
}


def _rows(path):
    """CSV rows with their line number in the file (header = line 1), as check.py counts them."""
    lines = list(csv.reader(io.StringIO((ROOT / path).read_text(encoding="utf-8-sig"))))
    head = lines[0]
    return [(i + 1, dict(zip(head, r))) for i, r in enumerate(lines) if i > 0]


def _add(facts, fid, row, line, src, what):
    v = num(row["OBS_VALUE"])
    facts.add(
        Fact(
            fid,
            v,
            "% of GDP",
            row["TIME_PERIOD"],
            src,
            f"{row['REF_AREA']} {what} line {line}",
            note=row.get("Reference area", ""),
        )
    )
    return v


def _add_rate(facts, fid, row, line):
    v = num(row["OBS_VALUE"])
    facts.add(
        Fact(
            fid,
            v,
            "% statutory rate",
            row["TIME_PERIOD"],
            PIT_SRC,
            f"{row['REF_AREA']} top statutory personal income tax rate line {line}",
            note=row.get("Reference area", ""),
        )
    )
    return v


def _latest(found, *areas):
    """Latest year with a figure for every one of these areas."""
    years = [
        y for y in {y for (a, y) in found} if all(found.get((a, y)) is not None for a in areas)
    ]
    return max(years)


def build(facts):
    out = {"names": {}}

    # Tax: totals for every OECD member and the average, every year.
    tax, kinds = {}, {}
    for line, r in _rows(TAX_FILE):
        a, y, k = r["REF_AREA"], r["TIME_PERIOD"], r["STANDARD_REVENUE"]
        if len(a) == 3 or a == AVG:
            out["names"][a] = NAMES.get(r["Reference area"], r["Reference area"])
            if k == "_T":
                tax[(a, y)] = _add(
                    facts, f"intl.tax.{a}.{y}", r, line, TAX_SRC, "total tax revenue % GDP"
                )
            elif a in (UK, AVG):
                kinds[(a, k, y)] = num(r["OBS_VALUE"])
                if kinds[(a, k, y)] is not None:
                    _add(
                        facts,
                        f"intl.taxkind.{k}.{a}.{y}",
                        r,
                        line,
                        TAX_SRC,
                        f"{r['Revenue category']} % GDP",
                    )
    members = sorted(a for a in out["names"] if len(a) == 3)
    out["members"] = members
    out["tax_year"] = ty = _latest(tax, UK, AVG)
    out["tax_years"] = sorted({y for (a, y) in tax if a == UK and tax[(a, y)] is not None})
    out["tax_missing"] = [a for a in members if tax.get((a, ty)) is None]
    kind_years = [
        y
        for y in {y for (_, _, y) in kinds}
        if all(kinds.get((a, k, y)) is not None for a in (UK, AVG) for k, _, _ in TAX_KINDS)
    ]
    out["kind_year"] = max(kind_years)

    # Spending: general government expenditure, % of GDP.
    spend = {}
    for line, r in _rows(SPEND_FILE):
        a, y = r["REF_AREA"], r["TIME_PERIOD"]
        if r["MEASURE"] == "GE" and r["UNIT_MEASURE"] == "PT_B1GQ" and (a in members or a == AVG):
            spend[(a, y)] = _add(
                facts,
                f"intl.spend.{a}.{y}",
                r,
                line,
                SPEND_SRC,
                "general government expenditure % GDP",
            )
    out["spend_year"] = sy = _latest(spend, UK, AVG)
    out["spend_years"] = sorted(
        y for (a, y) in spend if a == UK and spend[(a, y)] is not None and y <= sy
    )
    out["spend_missing"] = [a for a in members if spend.get((a, sy)) is None]

    # Spending by function: UK and the average, % of GDP. Defence is also kept for the
    # other G7 countries, for the defence page (builder/pages_defence.py).
    fn = {}
    for line, r in _rows(COFOG_FILE):
        a, y, g = r["REF_AREA"], r["TIME_PERIOD"], r["EXPENDITURE"]
        if (
            (a in (UK, AVG) or (g == DEFENCE and a in G7))
            and r["UNIT_MEASURE"] == "PT_B1GQ"
            and g in dict(FUNCTIONS)
        ):
            fn[(a, g, y)] = _add(
                facts,
                f"intl.fn.{g}.{a}.{y}",
                r,
                line,
                COFOG_SRC,
                f"{r['Expenditure']} expenditure % GDP",
            )
    fyears = [
        y
        for y in {y for (_, _, y) in fn}
        if all(fn.get((a, g, y)) is not None for a in (UK, AVG) for g, _ in FUNCTIONS)
    ]
    out["fn_year"] = max(fyears)
    # Defence for the G7 countries that have a figure (Canada has none in this table).
    out["defence_years"] = {
        a: sorted(y for (b, g, y) in fn if b == a and g == DEFENCE) for a in G7 + [AVG]
    }
    out["functions"], out["tax_kinds"] = FUNCTIONS, TAX_KINDS

    # Top statutory personal income tax rate on earnings, G7 countries (the rate on the highest band).
    # Only the latest year with every G7 country is kept as a fact: older years are not shown.
    pit, rows = {}, {}
    for line, r in _rows(PIT_FILE):
        a, y = r["REF_AREA"], r["TIME_PERIOD"]
        if r["MEASURE"] == "TS_PIT" and a in G7 and num(r["OBS_VALUE"]) is not None:
            pit[(a, y)] = num(r["OBS_VALUE"])
            rows[(a, y)] = (r, line)
    out["pit_year"] = py = _latest(pit, *G7)
    for a in G7:
        r, line = rows[(a, py)]
        _add_rate(facts, f"intl.pit.{a}.{py}", r, line)
    return out
