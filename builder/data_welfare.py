"""Welfare (social security) spending over the long run, from the OBR's historical public finances database.

Social security is benefits and the State Pension, as the OBR measures it. The OBR
splits it into pensioners and non-pensioners from 1978-79 (from IFS data), which
gives the two definitions the welfare page shows: with and without pensions.

The same database and file as the spending-by-purpose page, so the two agree, but
the series are read here on their own. The series stop at 2021-22, because the OBR
grew 2022-23 from the previous year instead of measuring it. Amounts after inflation
use the GDP deflator (2025-26 = 100) and per-person figures the ONS mid-year population.
"""
from .data import Fact, num
from .readers import xlsx, ref
from .data_spendhist import _sheet, FILE, LAST

SOURCE = "obrhist-welfare-gdp"  # the same sheets as the spending-by-purpose page, one record page per kind of figure
SOURCE_AMOUNTS = "obrhist-welfare-amounts"
SOURCE_CALC = "obrhist-welfare-calc"

FIRST = "1955-56"  # the first year of social security figures (IFS)
FIRST_PENSIONERS = "1978-79"  # the first year of the pensioner split

# key, plain name, column header (before its footnote number)
MEASURES = [
    ("social", "All social security", "Social Security"),
    ("pensioners", "Pensioners", "o/w pensioners"),
    ("nonpensioners", "Non-pensioners", "o/w non-pensioners"),
]
TOTAL = ("total", "Total public sector spending", "Total Public Sector Spending")


def build(facts):
    wb = xlsx(FILE)
    pct_rows, pct_head, pct_years = _sheet(wb, "Spending (per cent of GDP)")
    cash_rows, cash_head, cash_years = _sheet(wb, "Spending (£m)")
    years = [y for y in pct_years if FIRST <= y <= LAST]
    out = {"years": years, "first": {}, "pensioner_years": [y for y in years if y >= FIRST_PENSIONERS]}
    tot = {}  # year -> total public sector spending, cash
    for key, name, label in [TOTAL] + MEASURES:  # total first: shares are taken of it
        jp, jc = pct_head.index(label), cash_head.index(label)
        out["first"][key] = None
        for y in years:
            i = pct_years[y]
            v = num(pct_rows[i][jp])
            facts.add(Fact(f"wel.gdp.{key}.{y}", v, "% of GDP", y, SOURCE, f"Spending (per cent of GDP)!{ref(i, jp)}",
                           "published" if v is not None else "missing", note=name))
            if v is not None and out["first"][key] is None:
                out["first"][key] = y
            c = cash_years[y]
            cv = num(cash_rows[c][jc])
            cash = facts.add(Fact(f"wel.cash.{key}.{y}", None if cv is None else cv / 1000, "£bn", y, SOURCE_AMOUNTS, f"Spending (£m)!{ref(c, jc)}",
                                  "published" if cv is not None else "missing", note=name, scale=0.001))
            if key == "total":
                tot[y] = cash
                continue
            if cash.value is not None and tot[y].value:
                facts.add(Fact(f"wel.share.{key}.{y}", cash.value * 100 / tot[y].value, "% of total public sector spending", y, SOURCE_CALC,
                               cash.locator, "calculated", note=name,
                               formula=f"{cash.id} × 100 ÷ {tot[y].id}", inputs=[cash.id, tot[y].id]))
            soc = facts.get(f"wel.cash.social.{y}")
            if key == "pensioners" and cash.value is not None and soc is not None and soc.value:
                facts.add(Fact(f"wel.penssh.{y}", cash.value * 100 / soc.value, "% of all social security", y, SOURCE_CALC, cash.locator,
                               "calculated", note=name, formula=f"{cash.id} × 100 ÷ {soc.id}", inputs=[cash.id, soc.id]))
            dfl = facts.get(f"agg.deflator.{y}")
            if cash.value is not None and dfl is not None and dfl.value is not None:
                real = facts.add(Fact(f"wel.real.{key}.{y}", cash.value * 100 / dfl.value, "£bn (2025-26 prices)", y, SOURCE_CALC, cash.locator,
                                      "calculated", note=name, formula=f"{cash.id} × 100 ÷ {dfl.id}", inputs=[cash.id, dfl.id]))
                pop = facts.get(f"pop.uk.{y[:4]}")
                if pop is not None and pop.value:
                    facts.add(Fact(f"wel.pp.{key}.{y}", real.value * 1e9 / pop.value, "£ per person (2025-26 prices)", y, SOURCE_CALC, cash.locator,
                                   "calculated", note=name, formula=f"{real.id} × 1,000,000,000 ÷ {pop.id}", inputs=[real.id, pop.id]))
    return out
