"""Buying a home: who buys, at what age, who owns by age, and what new mortgages cost.

Downloads kept byte for byte by scripts/fetch_sources.py:

- English Housing Survey 2024-25 Annex Table 3.3: mean age of recent first-time
  buyers (bought in the last three years), 2003-04 to 2024-25. 2003-04 to 2007-08
  come from the Survey of English Housing; 2008-09 onwards from the English Housing
  Survey, so the two are not joined.
- English Housing Survey live table FC2101 (2021-22 sheet): percentage of households
  in each age group of the household reference person that are owner occupiers,
  2008-09 to 2021-22.
- English Housing Survey 2008-09 Annex Table 1.4: the same measure for 1991 from the
  Labour Force Survey, which then grouped households by the head of household (the
  man, in a couple), not the household reference person. FC2101 repeats these 1991
  figures without naming their source; this table names it.
- English Housing Survey 2024-25 Annex Table 1.4: the same measure, in the same age
  groups as the 1991 table, for 2008-09 and 2024-25.
- English Housing Survey 2024-25 Annex Table 2.5: mortgage payments as a proportion of
  gross household income (including housing support) for owner occupiers making
  mortgage payments, 2010-11 to 2024-25. Take-home pay is not in this table.
- Bank of England effective interest rate on new mortgages (CFMZ6JM, total), monthly,
  from January 2016, the first month in the series fetched.
- Bank of England quoted rate on a two-year fixed mortgage at 75% loan to value
  (IUMBV34), monthly from January 2008. It is a quoted rate for one product, a
  different series from CFMZ6JM, so it is kept apart and never joined to it.

Every figure keeps its cell (or CSV line) as its locator, so check.py can re-read it.
"""

import csv
import re

import xlrd

from .data import Fact, num
from .readers import ROOT, ods, ref

AGE_FILE = "data/fetched/ehs/annex-2024-25-ch3-history.ods"
OWN_FILE = "data/fetched/ehs/FC2101_owner_occupiers_by_age.ods"
INCOME_FILE = "data/fetched/ehs/annex-2024-25-ch2-costs.ods"
BOE_FILE = "data/fetched/boe/mortgage-rates-new-lending.csv"
OWN_1991_FILE = "data/fetched/ehs/2008-09-household-report-ch1-annex.xls"
OWN_1991_SHEET = "AT1.4 Ten x age, 4 yrs"
OWN_NOW_FILE = "data/fetched/ehs/annex-2024-25-ch1-profile.ods"
QUOTED_FILE = "data/fetched/boe/quoted-rate-2yr-fixed-75ltv.csv"
AGE_SRC, OWN_SRC, INCOME_SRC, BOE_SRC = (
    "ehs-annex-ch3",
    "ehs-fc2101",
    "ehs-annex-ch2",
    "boe-mortgage-rates",
)
OWN_1991_SRC, OWN_NOW_SRC, QUOTED_SRC = (
    "ehs-0809-annex-ch1",
    "ehs-annex-ch1",
    "boe-quoted-2yr-75ltv",
)
AGE_GROUPS = ["16-24", "25-34", "35-44", "45-64", "65-74", "75+"]
# The age groups of the two Annex Tables 1.4, which differ from FC2101's above 44.
HRP_GROUPS = ["16-24", "25-34", "35-44", "45-54", "55-64", "65+"]
# 1991 is from the Labour Force Survey; 2008-09 and 2024-25 from the English Housing Survey.
HRP_YEARS = [1991, 2008, 2024]
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
    """Percentage of households in each age group of the household reference person that own their home,
    2008-09 to 2021-22, from the 2021-22 sheet (which holds every year's row).
    The sheet's 1981 and 1991 rows name no source, so 1991 is read from the table that does (_owner_1991).
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
                    "% of households in the age group",
                    f"{label} survey year",
                    OWN_SRC,
                    f"2021-22!{ref(i, j)}",
                    "published",
                    note=f"Percentage of households whose household reference person is aged {g} that are owner occupiers, England (households, not people of that age)",
                )
            )
        years.append(y)
    return years


def _hrp_group(label):
    """'16 - 24', 'all 16 to 24' or 'all 65 or over' -> '16-24' or '65+'."""
    text = re.sub(r"^all ", "", label.strip())
    if text == "65 or over":
        return "65+"
    m = re.fullmatch(r"(\d+)\s*(?:-|to)\s*(\d+)", text)
    return f"{m.group(1)}-{m.group(2)}" if m else None


def _owner_1991(facts):
    """1991 owner occupation by age, from the 2008-09 English Housing Survey Annex Table 1.4.
    The sheet labels every year by the household reference person, but its footnote names the
    Labour Force Survey for 1991, which used the head of household until spring 2001."""
    sh = xlrd.open_workbook(str(ROOT / OWN_1991_FILE)).sheet_by_name(OWN_1991_SHEET)
    lfs_note = "Sources: 1981, 1991, 2001 ONS Labour Force Survey"
    if not str(sh.cell_value(43, 0)).startswith(lfs_note):
        raise ValueError("Annex Table 1.4 no longer names the Labour Force Survey for 1991")
    col = 10  # column K: owner occupiers, percentages
    if re.sub(r"\s+", " ", str(sh.cell_value(3, col))).strip() != "owner occupiers":
        raise ValueError("Annex Table 1.4 column K is no longer owner occupiers")
    start = next(i for i in range(sh.nrows) if str(sh.cell_value(i, 0)).strip() == "1991")
    if sh.cell_value(start - 1, 16) != "percentages":
        raise ValueError("Annex Table 1.4 1991 block is no longer in percentages")
    for k, g in enumerate(HRP_GROUPS):
        i = start + k
        if _hrp_group(str(sh.cell_value(i, 1))) != g:
            raise ValueError(f"Annex Table 1.4 row {i + 1} is not age {g}")
        facts.add(
            Fact(
                f"own.hrp.{g}.1991",
                num(sh.cell_value(i, col)),
                "% of households in the age group",
                "1991",
                OWN_1991_SRC,
                f"{OWN_1991_SHEET}!K{i + 1}",
                "published",
                note=f"Percentage of households whose head of household was aged {g} that were owner occupiers, England, 1991. "
                "Labour Force Survey, which grouped households by the head of household (the man, in a couple), not the household reference person used from 2001.",
            )
        )


def _owner_now(facts):
    """2008-09 and 2024-25 owner occupation by age of the household reference person, in the 1991 table's
    age groups (2024-25 Annex Table 1.4, percentages block only)."""
    rows = ods(OWN_NOW_FILE)["AT1_4"]
    head = next(i for i, r in enumerate(rows) if "2008-09" in r and "2024-25" in r)
    cols = {y: rows[head].index(f"{y}-{str(y + 1)[2:]}") for y in HRP_YEARS[1:]}
    start = next(i for i, r in enumerate(rows) if "percentages" in r)
    found, owner_row = [], None
    for i in range(start + 1, len(rows)):
        label = next((c.strip() for c in rows[i] if isinstance(c, str) and c.strip()), "")
        if label == "sample sizes":
            break
        if label == "all owner occupiers":
            owner_row = i
        elif label.startswith("all ") and _hrp_group(label) and owner_row is not None:
            g = _hrp_group(label)
            for y, j in cols.items():
                facts.add(
                    Fact(
                        f"own.hrp.{g}.{y}",
                        num(rows[owner_row][j]),
                        "% of households in the age group",
                        f"{y}-{str(y + 1)[2:]} survey year",
                        OWN_NOW_SRC,
                        f"AT1_4!{ref(owner_row, j)}",
                        "published",
                        note=f"Percentage of households whose household reference person is aged {g} that are owner occupiers, England (English Housing Survey)",
                    )
                )
            found.append(g)
            owner_row = None
    if found != HRP_GROUPS:
        raise ValueError(f"Annex Table 1.4 (2024-25) age groups changed: {found}")


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
                note="Effective interest rate on new mortgages, total (Bank of England series CFMZ6JM): the weighted average rate on new loans secured on dwellings to individuals and individual trusts in the month",
            )
        )
        months.append(key)
    return months


def _quoted_rates(facts):
    """Quoted two-year fixed rate at 75% loan to value (IUMBV34), monthly from January 2008."""
    with open(ROOT / QUOTED_FILE, encoding="utf-8") as f:
        lines = list(csv.reader(f))
    head = lines[0]
    col = head.index("IUMBV34")
    months = []
    for n, r in enumerate(lines[1:], start=2):
        if len(r) < len(head) or not r[0]:
            continue
        day, mon, yr = r[0].split()
        key = f"{yr}-{MONTHS[mon]:02d}"
        facts.add(
            Fact(
                f"rate.quoted.{key}",
                num(r[col]),
                "% a year",
                f"{mon} {yr}",
                QUOTED_SRC,
                f"IUMBV34 line {n}",
                "published",
                note="Quoted rate on a two-year fixed mortgage at 75% loan to value (Bank of England series IUMBV34): "
                "a quoted rate for one product, a different series from the effective rate CFMZ6JM, and not joined to it. "
                "The Bank changed its method from January 2016",
            )
        )
        months.append(key)
    return months


def build(facts):
    _owner_1991(facts)
    _owner_now(facts)
    out = {
        "age_years": _first_time_buyer_age(facts),
        "own_years": _owner_by_age(facts),
        "hrp_years": list(HRP_YEARS),
        "share_years": _mortgage_share(facts),
        "rate_months": _new_mortgage_rates(facts),
        "quoted_months": _quoted_rates(facts),
    }
    return out
