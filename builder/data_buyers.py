"""Buying a home: who buys, at what age, who owns by age, and what new mortgages cost.

Four downloads, kept byte for byte by scripts/fetch_sources.py:

- English Housing Survey 2024-25 Annex Table 3.3: mean age of recent first-time
  buyers (bought in the last three years), 2003-04 to 2024-25. 2003-04 to 2007-08
  come from the Survey of English Housing; 2008-09 onwards from the English Housing
  Survey, so the two are not joined.
- English Housing Survey live table FC2101 (2021-22 sheet): percentage of each age
  group that are owner occupiers, 2008-09 to 2021-22.
- English Housing Survey 2024-25 Annex Table 2.5: mortgage payments as a proportion of
  gross household income (including housing support) for owner occupiers making
  mortgage payments, 2010-11 to 2024-25. Take-home pay is not in this table.
- Bank of England effective interest rate on new mortgages (CFMZ6JM, total), monthly,
  from January 2016, the first month in the series fetched.

Every figure keeps its cell (or CSV line) as its locator, so check.py can re-read it.
"""

import csv
import re

from .data import Fact, num
from .readers import ROOT, ods, ref

AGE_FILE = "data/fetched/ehs/annex-2024-25-ch3-history.ods"
OWN_FILE = "data/fetched/ehs/FC2101_owner_occupiers_by_age.ods"
INCOME_FILE = "data/fetched/ehs/annex-2024-25-ch2-costs.ods"
BOE_FILE = "data/fetched/boe/mortgage-rates-new-lending.csv"
AGE_SRC, OWN_SRC, INCOME_SRC, BOE_SRC = (
    "ehs-annex-ch3",
    "ehs-fc2101",
    "ehs-annex-ch2",
    "boe-mortgage-rates",
)
AGE_GROUPS = ["16-24", "25-34", "35-44", "45-64", "65-74", "75+"]
MONTHS = {
    m: i + 1
    for i, m in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    )
}


def _cell_col(rows, text, start=0):
    """Column index of the first cell in the first rows that equals text (ODS sheets start at different columns)."""
    for r in rows[:8]:
        for j, c in enumerate(r):
            if isinstance(c, str) and c.strip() == text:
                return j
    raise KeyError(text)


def _label_cells(rows):
    """(row index, column, label) for every row with a year label in some column."""
    for i, r in enumerate(rows):
        for j, c in enumerate(r):
            if isinstance(c, str) and re.fullmatch(r"\d{4}(-\d{2}|/\d{2})", c.strip()):
                yield i, j, c.strip()
                break


def _first_time_buyer_age(facts):
    """Mean age of all recent first-time buyers in England, 2003-04 to 2024-25 (Annex Table 3.3, the means block only)."""
    rows = ods(AGE_FILE)["AT3_3"]
    col = _cell_col(rows, "all first time buyers")
    stop = next(
        i for i, r in enumerate(rows) if "sample size" in r
    )  # the sample sizes repeat the labels below this
    years = []
    for i in range(stop):
        lab = next(
            (
                str(c).strip()
                for c in rows[i]
                if isinstance(c, str) and re.fullmatch(r"\d{4}-\d{2}", c.strip())
            ),
            None,
        )
        if not lab:
            continue
        y = int(lab[:4])
        note = (
            " 2003-04 to 2007-08 come from the Survey of English Housing; 2008-09 onwards from the English Housing Survey."
            if y < 2008
            else ""
        )
        facts.add(
            Fact(
                f"ftb.age.{y}",
                num(rows[i][col]),
                "years (mean age)",
                f"{lab} survey year",
                AGE_SRC,
                f"AT3_3!{ref(i, col)}",
                "published",
                note="Mean age of recent first-time buyers in England (bought in the last three years)."
                + note,
            )
        )
        years.append(y)
    return years


def _owner_by_age(facts):
    """Percentage of each age group that owns its home, 2008-09 to 2021-22, from the 2021-22 sheet (which holds every year's row).
    The 1981 and 1991 rows in that sheet are not used: their source is not documented on the sheet.
    """
    rows = ods(OWN_FILE)["2021-22"]
    head = next(
        i for i, r in enumerate(rows) if "16-24" in [str(c).strip() for c in r if c is not None]
    )
    cols = {
        str(c).strip(): j
        for j, c in enumerate(rows[head])
        if c is not None and str(c).strip() in AGE_GROUPS
    }
    years = []
    for i in range(head + 1, len(rows)):
        lab = next(
            (
                (j, str(c).strip())
                for j, c in enumerate(rows[i])
                if isinstance(c, str) and re.fullmatch(r"\d{4}/\d{2}", c.strip())
            ),
            None,
        )
        if not lab:
            continue
        j0, label = lab
        y = int(label[:4])
        for g in AGE_GROUPS:
            j = cols[g]
            facts.add(
                Fact(
                    f"own.{g}.{y}",
                    num(rows[i][j]),
                    "% of the age group",
                    f"{label} survey year",
                    OWN_SRC,
                    f"2021-22!{ref(i, j)}",
                    "published",
                    note=f"Percentage of people aged {g} who are owner occupiers, England",
                )
            )
        years.append(y)
    return years


def _mortgage_share(facts):
    """Owner occupiers' mortgage payments as a % of gross household income (including housing support), first block only."""
    rows = ods(INCOME_FILE)["AT2_5"]
    head = next(
        i
        for i, r in enumerate(rows)
        if any(
            isinstance(c, str) and c.startswith("all households making mortgage or rent") for c in r
        )
    )
    hdr = next(i for i in range(head, len(rows)) if "owner occupiers" in [c for c in rows[i]])
    col = rows[hdr].index("owner occupiers")
    lab_col = col - 1
    years = []
    for i in range(hdr + 1, len(rows)):
        if rows[i] and "percentages" in rows[i] and years:
            break  # the second block (joint income of the household reference person and partner) starts here
        label = rows[i][lab_col] if len(rows[i]) > lab_col else None
        if not isinstance(label, str) or not re.fullmatch(r"\d{4}-\d{2}", label.strip()):
            continue
        y = int(label[:4])
        facts.add(
            Fact(
                f"mortshare.{y}",
                num(rows[i][col]),
                "% of gross household income",
                f"{label} survey year",
                INCOME_SRC,
                f"AT2_5!{ref(i, col)}",
                "published",
                note="Owner occupiers' mortgage payments as a share of gross household income including housing support (before tax, not take-home pay)",
            )
        )
        years.append(y)
    return years


def _new_mortgage_rates(facts):
    """Effective rate on new mortgages (CFMZ6JM), monthly, January 2016 onwards."""
    with open(ROOT / BOE_FILE, encoding="utf-8") as f:
        lines = list(csv.reader(f))
    head = lines[0]
    col = head.index("CFMZ6JM")
    months = []
    for n, r in enumerate(lines[1:], start=2):
        if len(r) < len(head) or not r[0]:
            continue
        day, mon, yr = r[0].split()
        key = f"{yr}-{MONTHS[mon]:02d}"
        facts.add(
            Fact(
                f"rate.new.{key}",
                num(r[col]),
                "% a year",
                f"{mon} {yr}",
                BOE_SRC,
                f"CFMZ6JM line {n}",
                "published",
                note="Effective interest rate on new mortgages, total (Bank of England series CFMZ6JM): the average rate on loans taken out in the month",
            )
        )
        months.append(key)
    return months


def build(facts):
    out = {
        "age_years": _first_time_buyer_age(facts),
        "own_years": _owner_by_age(facts),
        "share_years": _mortgage_share(facts),
        "rate_months": _new_mortgage_rates(facts),
    }
    return out
