"""Taxes by type since 1948-49, from the OBR's historical public finances database,
and the number of UK households, used to give money totals per household.

The historical database (July 2023) joins Bank of England and ONS series. It is a
different, older release from the OBR databank used on the main taxes page, which
starts in 1999-00, so the two are shown separately and never joined.

Receipts are on a cash basis until 1998-99 and an accruals basis from 1999-00
(the OBR's receipts note), and some taxes were replaced by others. Those changes
are listed in BREAKS and drawn on the charts.
"""
import re

from .data import Fact, num
from .readers import xlsx, ref

SOURCE = "obrhist-receipts"  # % of GDP, as published
SOURCE_AMOUNTS = "obrhist-receipts-amounts"  # £; a second record page for the same file
SOURCE_SHARES = "obrhist-receipts-shares"  # shares of all receipts; a third record page
FILE = "data/raw/OBR_Historical_public_finances_database.xlsx"
FIRST, LAST = "1948-49", "2022-23"

# key, plain name, column header in the OBR sheet (footnote number removed)
GROUPS = [
    ("income_tax", "Income Tax", "Income tax"),
    ("nics", "National Insurance", "National Insurance Contributions"),
    ("vat", "VAT (purchase tax before 1973)", "VAT (Purchase tax prior to 1973)"),
    ("duties", "Customs and excise duties", "Custom and excise duties"),
    ("corp", "Corporation Tax (profits taxes before 1966)", "Corporation tax (profits taxes prior to 1966-67)"),
    ("council", "Council Tax (poll tax and rates on homes before 1993)", "Council Tax (community charge and domestic rates prior to 1993)"),
]
TOTAL = ("total", "All public sector receipts", "Public Sector Current Receipts")
OTHER = ("other", "Everything else")

# (first year of the change, short label, plain explanation)
BREAKS = [
    ("1966-67", "Corporation Tax starts", "Corporation Tax replaced the earlier profits taxes and Income Tax paid by companies in 1965-66, so the Corporation Tax line before 1966-67 shows those earlier profits taxes."),
    ("1973-74", "VAT replaces purchase tax", "VAT replaced purchase tax and selective employment tax in April 1973. Before 1973-74 the VAT line shows purchase tax."),
    ("1990-91", "Poll tax and national business rates", "Domestic rates were replaced by the community charge (“poll tax”) in Scotland in 1989 and in England and Wales in 1990, and that by Council Tax in 1993. Business rates were set nationally from 1990."),
    ("1999-00", "Recording method changes", "Up to 1998-99 receipts are counted when the cash arrives; from 1999-00 they are counted for the period the tax relates to (accruals). Income Tax and National Insurance also switch from a Bank of England series to ONS figures."),
]


def _sheet(wb, name, year_col):
    rows = [[c.value for c in r] for r in wb[name].iter_rows(max_col=27)]
    head = [re.sub(r"\d+\s*$", "", str(v)).strip() if v else "" for v in rows[3]]
    years = {str(r[year_col]): i for i, r in enumerate(rows)
             if len(r) > year_col and r[year_col] and re.fullmatch(r"\d{4}-\d{2}", str(r[year_col]))}
    return rows, head, years


def build(facts):
    wb = xlsx(FILE)
    pct_rows, pct_head, pct_years = _sheet(wb, "Receipts (per cent of GDP)", 0)
    cash_rows, cash_head, cash_years = _sheet(wb, "Receipts (£m)", 0)
    years = [y for y in pct_years if FIRST <= y <= LAST]
    out = {"years": years, "groups": [(k, n) for k, n, _ in GROUPS] + [OTHER], "total": TOTAL[1], "breaks": BREAKS}
    for y in years:
        ip, ic = pct_years[y], cash_years[y]
        for key, name, col in GROUPS + [TOTAL]:
            jp, jc = pct_head.index(col), cash_head.index(col)
            g, c = num(pct_rows[ip][jp]), num(cash_rows[ic][jc])
            if g is None or c is None:
                raise ValueError(f"{col} {y}: no figure in the OBR sheets")
            facts.add(Fact(f"thist.gdp.{key}.{y}", g, "% of GDP", y, SOURCE, f"Receipts (per cent of GDP)!{ref(ip, jp)}", "published", note=name))
            facts.add(Fact(f"thist.cash.{key}.{y}", c / 1000, "£bn", y, SOURCE_AMOUNTS, f"Receipts (£m)!{ref(ic, jc)}", "published", note=name, scale=0.001))
        total = facts[f"thist.cash.total.{y}"]
        rest = total.value - sum(facts[f"thist.cash.{k}.{y}"].value for k, _, _ in GROUPS)
        ids = [f"thist.cash.{k}.{y}" for k, _, _ in GROUPS]
        facts.add(Fact(f"thist.cash.other.{y}", rest, "£bn", y, SOURCE_AMOUNTS, total.locator, "calculated",
                       note="All receipts minus the six named groups: business rates, oil and gas taxes, stamp duties, Capital Gains Tax, Inheritance Tax, the TV licence fee, other taxes, and non-tax receipts such as interest and dividends.",
                       formula=f"thist.cash.total.{y} − sum of the six named groups", inputs=[total.id] + ids))
        gtot = facts[f"thist.gdp.total.{y}"]
        facts.add(Fact(f"thist.gdp.other.{y}", gtot.value - sum(facts[f"thist.gdp.{k}.{y}"].value for k, _, _ in GROUPS), "% of GDP", y, SOURCE,
                       gtot.locator, "calculated", formula=f"thist.gdp.total.{y} − sum of the six named groups",
                       inputs=[gtot.id] + [f"thist.gdp.{k}.{y}" for k, _, _ in GROUPS]))
        for key, _ in out["groups"]:
            c = facts[f"thist.cash.{key}.{y}"]
            facts.add(Fact(f"thist.share.{key}.{y}", 100 * c.value / total.value, "% of all public sector receipts", y, SOURCE_SHARES, c.locator, "calculated",
                           formula=f"100 × {c.id} ÷ {total.id}", inputs=[c.id, total.id]))
    return out


def households(facts):
    """UK households (thousands), April to June each year: ONS Families and households, Table 5."""
    rows = [[c.value for c in r] for r in xlsx("data/fetched/ons/families-households.xlsx")["5"].iter_rows()]
    hi = next(i for i, r in enumerate(rows) if r and r[0] and str(r[0]).strip().startswith("Number of households"))
    head = rows[hi]
    tot = next(i for i, r in enumerate(rows) if r and r[0] and str(r[0]).strip() == "All households")
    years = []
    for j, h in enumerate(head):
        m = re.fullmatch(r"(\d{4}) Estimate", str(h or "").strip())
        if not m:
            continue
        y = int(m.group(1))
        ci = num(rows[tot][j + 2]) if str(head[j + 2] or "").strip() == f"{y} CI+/-" else None
        facts.add(Fact(f"hh.uk.{y}", num(rows[tot][j]) * 1000, "households", f"April to June {y}", "ons-families-households", f"5!{ref(tot, j)}",
                       "published", scale=1000,
                       note=f"Private households, UK, Labour Force Survey. 95% confidence interval ±{ci:,.0f} thousand." if ci else "Private households, UK, Labour Force Survey."))
        years.append(y)
    return sorted(years)
