"""Spending by purpose over the long run, from the OBR's historical public finances database.

The database joins several published series (Bank of England, IFS, HM Treasury PESA
and ONS) into one run per purpose. Its purposes are not HM Treasury's COFOG areas
used on the main spending page, and its last update was July 2023, so its figures
are kept separate and never joined to PESA.

Figures stop at 2021-22: for 2022-23 the OBR grew health, education, defence and
social security from the previous year's growth rate instead of measuring them.
Real terms use the GDP deflator from the OBR's October 2026 databank, which starts
in 1955-56.
"""
import re

from .data import Fact, num
from .readers import xlsx, ref

SOURCE = "obrhist"
SOURCE_AMOUNTS = "obrhist-amounts"  # the same file; a second record page, as one would be too long
FILE = "data/raw/OBR_Historical_public_finances_database.xlsx"
LAST = "2021-22"  # 2022-23 is grown by the OBR from 2021-22, not measured
FIRST_SHARE = "1900-01"  # the first year total public sector spending is published
FIRST_REAL = "1955-56"  # the first year of the GDP deflator in the OBR databank

# key, plain name, column header (before its footnote number)
PURPOSES = [
    ("social", "Social security (benefits and State Pension)", "Social Security"),
    ("health", "Health", "Health"),
    ("education", "Education", "Education"),
    ("defence", "Defence", "Defence"),
    ("debt", "Debt interest", "Debt Interest"),
]
TOTAL = ("total", "Total public sector spending", "Total Public Sector Spending")

# Where the OBR changes from one underlying source to the next (its notes 2 to 9).
# Drawn as markers on the charts; the OBR joined these runs, so the site says where.
SOURCE_CHANGES = [("1955-56", "Source changes to IFS"), ("2020-21", "Source changes to PESA")]
GEOGRAPHY_CHANGE = ("1922-23", "Ireland leaves the UK")


def _sheet(wb, name):
    rows = [[c.value for c in r] for r in wb[name].iter_rows()]
    head = [re.sub(r"\d+\s*$", "", str(v)).strip() if v else "" for v in rows[3]]
    years = {str(r[1]): i for i, r in enumerate(rows) if len(r) > 1 and r[1] and re.fullmatch(r"\d{4}-\d{2}", str(r[1]))}
    return rows, head, years


def build(facts):
    wb = xlsx(FILE)
    pct_rows, pct_head, pct_years = _sheet(wb, "Spending (per cent of GDP)")
    cash_rows, cash_head, cash_years = _sheet(wb, "Spending (£m)")
    all_years = [y for y in pct_years if FIRST_SHARE <= y <= LAST]
    real_years = [y for y in all_years if y >= FIRST_REAL]
    out = {"years": all_years, "real_years": real_years, "purposes": [(k, n) for k, n, _ in PURPOSES], "total": TOTAL[1], "first": {}}
    for key, name, label in PURPOSES + [TOTAL]:
        jp, jc = pct_head.index(label), cash_head.index(label)
        first = None
        for y in all_years:
            i = pct_years[y]
            v = num(pct_rows[i][jp])
            facts.add(Fact(f"hist.gdp.{key}.{y}", v, "% of GDP", y, SOURCE, f"Spending (per cent of GDP)!{ref(i, jp)}",
                           "published" if v is not None else "missing", note=name))
            if v is not None and first is None:
                first = y
        out["first"][key] = first
        for y in real_years:
            i = cash_years[y]
            v = num(cash_rows[i][jc])
            cash = facts.add(Fact(f"hist.cash.{key}.{y}", None if v is None else v / 1000, "£bn", y, SOURCE_AMOUNTS, f"Spending (£m)!{ref(i, jc)}",
                                  "published" if v is not None else "missing", scale=0.001))
            dfl = facts[f"agg.deflator.{y}"]
            if cash.value is not None and dfl.value is not None:
                facts.add(Fact(f"hist.real.{key}.{y}", cash.value * 100 / dfl.value, "£bn (2025-26 prices)", y, SOURCE_AMOUNTS, cash.locator, "calculated",
                               formula=f"{cash.id} × 100 ÷ {dfl.id}", inputs=[cash.id, dfl.id]))
    return out
