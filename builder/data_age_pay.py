"""Facts for pay around the age of 30 and job security at 25 to 34 (John's J12.7 and J12.12).

Pay is ONS's Annual Survey of Hours and Earnings (ASHE) Table 6: median gross weekly pay of
full-time employee jobs in the age group 30 to 39, which is the narrowest group that holds
age 30. The only ONS single-year-of-age figures the site holds stop at 25, so no figure is for
people aged exactly 30. ASHE changed its methods in 2004, 2006 and 2011 and recoded jobs in 2021, so a change
after inflation is worked out only between two Aprils on the same basis (RUNS), never from
2002 to 2025.

No official table here measures job security by age since 1992. The redundancy rate for
ages 25 to 34 (RED02) starts in 2009 and is a different measure; the temporary employees
table (EMP07) has no age split. Each table's title, headings and notes are checked, and the
build stops if they change, so a changed file cannot silently change what a figure means.
"""

import re
import zipfile
from functools import lru_cache

import xlrd

from .data import Fact
from .data_life_extra import SPREAD_BREAKS
from .readers import ROOT, ons_series, xlsx, zip_sheet

PAY_GROUP = "30-39"
PAY_SHEET = "Full-Time"
BASE_YEAR = 2025
# April -> (source id, file, Table 6.1a member, basis). Editions on one basis share a label.
TABLE6 = {
    2002: (
        "ashe-2002-table6",
        "data/fetched/ons/ashe-table6-2002.zip",
        "Age Group Table 6.1a   Weekly pay - Gross 2002.xls",
        "2002 and 2003 methods",
    ),
    2006: (
        "ashe-2006-table6-2007-methods",
        "data/fetched/ons/ashe-table6-2006-2007-methods.zip",
        "Age Group Table 6.1a   Weekly pay - Gross 2006.xls",
        "2006 to 2010 methods",
    ),
    2010: (
        "ashe-2010-table6-revised",
        "data/fetched/ons/ashe-table6-2010-revised.zip",
        "REVISED - Age Group Table 6.1a   Weekly pay - Gross 2010.xls",
        "2006 to 2010 methods",
    ),
    2011: (
        "ashe-2011-table6-soc2010",
        "data/fetched/ons/ashe-table6-2011-soc2010.zip",
        "REVISED - Age Group Table 6.1a   Weekly pay - Gross 2011.xls",
        "2011 to 2020, jobs coded to SOC 2010",
    ),
    2020: (
        "ashe-2020-table6-revised",
        "data/fetched/ons/ashe-table6-2020-revised.zip",
        "Age Group Table 6.1a   Weekly pay - Gross 2020.xls",
        "2011 to 2020, jobs coded to SOC 2010",
    ),
    2021: (
        "ashe-2021-table6-revised",
        "data/fetched/ons/ashe-table6-2021-revised.zip",
        "Age Group Table 6.1a   Weekly pay - Gross 2021.xls",
        "2021 onwards, jobs coded to SOC 2020",
    ),
    2025: (
        "ashe-2025-table6-revised",
        "data/fetched/ons/ashe-table6-2025-revised.zip",
        "Age Group Table 6.1a   Weekly pay - Gross 2025.xlsx",
        "2021 onwards, jobs coded to SOC 2020",
    ),
}
# Pairs of Aprils measured the same way; a real change is worked out only within one pair.
RUNS = [(2006, 2010), (2011, 2020), (2021, 2025)]
CPI_FILE = "data/fetched/ons/l522.csv"
COVERAGE_NOTE = (
    "Employees on adult rates whose pay for the survey pay-period was not affected by absence"
)
# Editions from April 2020 carry this footnote; the page repeats it for 2020 and 2021.
FURLOUGH_NOTE = "Estimates for 2020 and 2021 include employees who have been furloughed"

RED02_SOURCE = "ons-red02"
RED02_FILE = "data/fetched/ons/red02oct2026.xlsx"
RED02_SHEET = "Age - rates"
RED02_QUARTER = f"Apr-Jun {BASE_YEAR}"
RED02_FIRST = "Jan-Mar 2009"
RED02_TITLE = "Table RED02: Redundancy rates1 by age"
RED02_UNIT = "(rate per thousand) not seasonally adjusted"
RED02_NOTES = (
    "The redundancy rate is the ratio of the redundancy level for the given quarter to the number of employees in the previous quarter, multiplied by 1,000.",
    "Data from January to March 2019 onward has been reweighted, causing a step change discontinuity.",
)
EMP07_FILE = "data/fetched/ons/emp07aug2026.xls"
EMP07_SHEETS = ["Note", "People", "Men", "Women"]


def pay_fid(y):
    return f"pay.age.30_39.ft.{y}"


def real_fid(y):
    return f"pay.age.30_39.ft.{y}.real"


def change_fid(a, b):
    return f"pay.age.30_39.ft.real_change.{a}_{b}"


@lru_cache(maxsize=None)
def _zip_xls(path, member):
    """A legacy .xls workbook inside a retained zip pack (ASHE editions before 2022)."""
    with zipfile.ZipFile(ROOT / path) as archive:
        return xlrd.open_workbook(file_contents=archive.read(member))


def _sheet_cells(path, member, sheet):
    """Cell lookup by spreadsheet reference, for either workbook format in an ASHE pack."""
    if member.endswith(".xls"):
        sh = _zip_xls(path, member).sheet_by_name(sheet)

        def get(col, row):
            c = 0
            for ch in col:
                c = c * 26 + ord(ch) - 64
            return sh.cell_value(row - 1, c - 1) if row <= sh.nrows and c <= sh.ncols else None

        return get
    ws = zip_sheet(path, member, sheet)
    return lambda col, row: ws[f"{col}{row}"].value


def table6_cell(y):
    """(value, locator) of the full-time 30 to 39 median for April y, after checking the
    sheet's title, the median heading and the row label."""
    _, path, member, _ = TABLE6[y]
    get = _sheet_cells(path, member, PAY_SHEET)
    title = re.sub(r"\s+", " ", str(get("A", 1))).strip()
    if not re.search(
        rf"Weekly pay - Gross .* For full-time employee jobsa?: United Kingdom,? {y}$", title
    ):
        raise ValueError(f"{member}: not UK full-time gross weekly pay for {y}: {title!r}")
    if get("D", 5) != "Median":
        raise ValueError(f"{member}: column D is not the median")
    rows = [r for r in range(6, 15) if str(get("A", r) or "").strip() == PAY_GROUP]
    if len(rows) != 1:
        raise ValueError(f"{member}: no single {PAY_GROUP} row")
    notes = " ".join(str(get("A", r) or "") for r in range(6, 30))
    if COVERAGE_NOTE not in notes or (y >= 2020 and FURLOUGH_NOTE not in notes):
        raise ValueError(f"{member}: coverage note changed")
    value = get("D", rows[0])
    # A suppressed or missing estimate is printed as a symbol; it must stop the build, not become 0.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{member}: the {PAY_GROUP} median is not a number: {value!r}")
    return float(value), f"{member}::{PAY_SHEET}!D{rows[0]}"


def _cpih(facts, cpi, y):
    fid = f"cpih.apr.{y}"
    if fid not in facts:
        facts.add(
            Fact(
                fid,
                cpi[f"{y} APR"],
                "index (2015=100)",
                f"April {y}",
                "ons-l522",
                f"L522 row '{y} APR'",
            )
        )
    return facts[fid].value


def build_pay(facts):
    _, cpi = ons_series(CPI_FILE)
    base = _cpih(facts, cpi, BASE_YEAR)
    for y, (sid, _, _, basis) in TABLE6.items():
        value, locator = table6_cell(y)
        facts.add(
            Fact(
                pay_fid(y),
                value,
                "£ a week",
                f"April {y}",
                sid,
                locator,
                "published",
                note=f"Median gross weekly pay of full-time employee jobs, age group 30 to 39, United Kingdom ({basis}). Not people aged exactly 30.",
            )
        )
        facts.add(
            Fact(
                real_fid(y),
                value * base / _cpih(facts, cpi, y),
                f"£ a week, April {BASE_YEAR} prices",
                f"April {y}, in April {BASE_YEAR} prices",
                sid,
                f"calculated from {pay_fid(y)} and CPIH (ons-l522)",
                "calculated",
                formula=f"{pay_fid(y)} × cpih.apr.{BASE_YEAR} ÷ cpih.apr.{y}",
                inputs=[pay_fid(y), f"cpih.apr.{BASE_YEAR}", f"cpih.apr.{y}"],
                note="Adjusted with CPIH, the index the site uses for real pay.",
            )
        )
    for a, b in RUNS:
        if TABLE6[a][3] != TABLE6[b][3] or any(a < y <= b for y in SPREAD_BREAKS):
            raise ValueError(f"April {a} and April {b} are not on the same ASHE basis")
        facts.add(
            Fact(
                change_fid(a, b),
                100 * facts[real_fid(b)].value / facts[real_fid(a)].value - 100,
                "%",
                f"April {a} to April {b}",
                TABLE6[b][0],
                f"calculated from {real_fid(a)} and {real_fid(b)}",
                "calculated",
                formula=f"100 × {real_fid(b)} ÷ {real_fid(a)} − 100",
                inputs=[real_fid(a), real_fid(b)],
                note=f"Change after inflation within one ASHE basis ({TABLE6[a][3]}).",
            )
        )


def _red02_rows(sheet):
    ws = xlsx(RED02_FILE)[sheet]
    return [[c.value for c in row] for row in ws.iter_rows()]


def build_redundancy(facts):
    note = " ".join(str(v) for r in _red02_rows("Note") for v in r if isinstance(v, str))
    if "These are official statistics in development." not in note:
        raise ValueError("RED02 Note: no longer official statistics in development")
    rows = _red02_rows(RED02_SHEET)
    text = " ".join(str(v) for r in rows for v in r if isinstance(v, str))
    title, unit = str(rows[0][0]), str(rows[3][0])
    if not title.startswith(RED02_TITLE) or RED02_UNIT not in unit:
        raise ValueError("RED02 Age - rates: title or unit changed")
    if rows[4][3] != "25-34":
        raise ValueError("RED02 Age - rates: column D is not ages 25 to 34")
    if rows[8][0] != RED02_FIRST:
        raise ValueError(f"RED02 Age - rates: first quarter is not {RED02_FIRST}")
    for phrase in RED02_NOTES:
        if phrase not in text:
            raise ValueError(f"RED02 Age - rates: note changed: {phrase!r}")
    hits = [i for i, r in enumerate(rows, 1) if r[0] == RED02_QUARTER]
    if len(hits) != 1:
        raise ValueError(f"RED02 Age - rates: no single {RED02_QUARTER} row")
    facts.add(
        Fact(
            f"redund.age.25_34.{BASE_YEAR}",
            float(rows[hits[0] - 1][3]),
            "per 1,000 employees",
            f"April to June {BASE_YEAR}",
            RED02_SOURCE,
            f"{RED02_SHEET}!D{hits[0]}",
            "published",
            note="Redundancies in the quarter for every 1,000 employees aged 25 to 34 in the previous quarter, Labour Force Survey, not seasonally adjusted. Official statistics in development.",
        )
    )


def check_temporary_table():
    """EMP07 is split by sex and by full-time or part-time work only, with no age group."""
    book = xlrd.open_workbook(str(ROOT / EMP07_FILE))
    if book.sheet_names() != EMP07_SHEETS:
        raise ValueError(f"EMP07 sheets changed: {book.sheet_names()}")
    people = book.sheet_by_name("People")
    if not str(people.cell_value(0, 0)).startswith(
        "EMP07: Temporary employees (all and part-time): People"
    ):
        raise ValueError("EMP07 People: title changed")
    heads = [people.cell_value(r, c) for r in range(4, 9) for c in range(people.ncols)]
    if any(re.search(r"\b\d{2}\s*(-|to)\s*\d{2}\b|\baged?\b", str(h), re.I) for h in heads):
        raise ValueError("EMP07 now has an age split: review the job security section")


def build(facts):
    build_pay(facts)
    build_redundancy(facts)
    check_temporary_table()
    return {"pay_years": sorted(TABLE6), "runs": RUNS, "redundancy_first": RED02_FIRST}
