"""Nationality of NHS and adult social care staff in England, from two official producers.

The sectors are counted differently, so their figures are kept apart and never added:

- NHS England, NHS Workforce Statistics, Table 14 (31 August 2026). Staff directly employed
  by NHS trusts and other core organisations, counted both as headcount (people) and as full
  time equivalent. Nationality is self-reported; staff who gave none are in an "Unknown" group,
  which the non-UK share leaves out of both the top and the bottom of the fraction.
- Skills for Care, adult social care workforce estimates 2025/26 (statistical appendix,
  Table 4.7.1). Modelled filled posts (one person can hold several posts), with shares
  published rounded to whole per cent. Unknown nationalities are left out by Skills for Care
  before the shares are made, and no count of them is published.

Rows and columns are found by their published labels, so a re-laid-out table stops the
build instead of reading a neighbouring cell.
"""

from datetime import datetime

import openpyxl

from .data import Fact, num
from .readers import ROOT, ref

NHS_SOURCE = "nhs-hchs-workforce-aug26"
NHS_FILE = "data/fetched/nhs/nhs-hchs-workforce-statistics-trusts-and-core-organisations-data-tables-august-2026.xlsx"
NHS_SHEET = "14"
NHS_MONTH = datetime(2026, 8, 31)
NHS_PERIOD = "31 August 2026"
NHS_SUFFIX = "aug2026"
NHS_SCOPE = "Staff in NHS trusts and other core organisations, England"
NHS_ALL_COLUMN = "All staff groups"
# key, Table 14 "Nationality group" label, "Nationality" label of that group's total row
NHS_GROUPS = [
    ("all", "All nationality groups", "All nationalities"),
    ("uk", "United Kingdom", "All nationalities"),
    ("eu", "European Union", "All nationalities"),
    ("eea", "European Economic Area", "All nationalities"),
    ("row", "Rest of World", "All nationalities"),
    ("unknown", "Unknown", "Unknown"),
]
NHS_KNOWN = ("uk", "eu", "eea", "row")
NHS_NON_UK = ("eu", "eea", "row")
NHS_MEASURES = {
    "hc": ("Headcount", "people (headcount)"),
    "fte": ("FTE", "full time equivalent staff"),
}

ASC_SOURCE = "sfc-asc-appendix-2026"
ASC_FILE = "data/fetched/sfc/ASC-Workforce-Statistical-Appendix-2026.xlsx"
ASC_SHEET = "4.7"
ASC_TABLE = "Table 4.7.1. Nationality by sector"
ASC_SOURCE_LINE = "Source: Skills for Care's workforce estimates, 2025/26"
ASC_PERIOD = "2025/26"
ASC_SUFFIX = "2025-26"
# key, column heading in Table 4.7.1
ASC_SECTORS = [
    ("all", "All sectors"),
    ("la", "Local authority"),
    ("ind", "Independent"),
    ("dpr", "Direct payment recipients"),
]
# key, row label; the table repeats "British" lower down, and the first one is used
ASC_GROUPS = [
    ("british", "British"),
    ("eu", "EU (non British)"),
    ("noneu", "Non-EU"),
    ("nonbritish", "Non-British"),
]


def sheet_rows(path, sheet, columns):
    """Cell values of one sheet from row 1 and column A, so list indexes match cell references."""
    workbook = openpyxl.load_workbook(ROOT / path, read_only=True, data_only=True)
    try:
        return [
            list(row)
            for row in workbook[sheet].iter_rows(
                min_row=1, min_col=1, max_col=columns, values_only=True
            )
        ]
    finally:
        workbook.close()


def _nhs_header(rows):
    """(header row index, column index of all staff groups) for Table 14."""
    if (
        not str(rows[0][0] or "").startswith("Table 14: ")
        or "by nationality group" not in rows[0][0]
    ):
        raise ValueError("NHS Table 14 title changed")
    if rows[1][0] != NHS_SCOPE:
        raise ValueError("NHS Table 14 scope changed")
    head = next(
        (
            i
            for i, r in enumerate(rows)
            if r[:4] == ["Data \nmonth", "Data type", "Nationality group", "Nationality"]
        ),
        None,
    )
    if head is None or NHS_ALL_COLUMN not in rows[head]:
        raise ValueError("NHS Table 14 header row not found")
    return head, rows[head].index(NHS_ALL_COLUMN)


def _check_nhs_totals(out):
    missing = [(m, k) for m in NHS_MEASURES for k, _, _ in NHS_GROUPS if (m, k) not in out]
    if missing:
        raise ValueError(f"NHS Table 14 is missing group totals {missing}")
    for m, (label, _) in NHS_MEASURES.items():
        groups = sum(out[(m, k)][2] for k in NHS_KNOWN + ("unknown",))
        total = out[(m, "all")][2]
        # FTE adds up exactly. NHS England's note 1 says headcount totals are unlikely to
        # equal the sum of components because some staff work in more than one role:
        # the groups exceeded the total by 304 of 1.5 million in August 2026.
        slack = 0.01 if m == "fte" else 0.001 * total
        if not -0.01 <= groups - total <= slack:
            raise ValueError(f"NHS Table 14 {label} groups do not add up to the total")


def nhs_cells(rows):
    """{(measure, group): (row index, column index, value)} for Table 14's group totals."""
    head, j = _nhs_header(rows)
    wanted = {
        (label, group_label, total_label): (m, key)
        for m, (label, _) in NHS_MEASURES.items()
        for key, group_label, total_label in NHS_GROUPS
    }
    out = {}
    for i in range(head + 1, len(rows)):
        month, measure, group, nationality = rows[i][:4]
        if (measure, group, nationality) not in wanted:
            continue
        m, key = wanted[(measure, group, nationality)]
        if month != NHS_MONTH:
            raise ValueError(f"NHS Table 14 row {i + 1} is not for {NHS_PERIOD}")
        if (m, key) in out:
            raise ValueError(f"NHS Table 14 repeats {measure} {group}")
        value = num(rows[i][j])
        if value is None or value < 0:
            raise ValueError(f"NHS Table 14 {measure} {group} is not a count")
        out[(m, key)] = (i, j, value)
    _check_nhs_totals(out)
    return out


def _asc_layout(rows):
    """(label column, heading row, {sector: column}) for Table 4.7.1."""
    top = next((i for i, r in enumerate(rows) if ASC_TABLE in r), None)
    if top is None:
        raise ValueError("Skills for Care Table 4.7.1 not found")
    lab = rows[top].index(ASC_TABLE)
    if rows[top + 1][lab] != ASC_SOURCE_LINE:
        raise ValueError("Skills for Care Table 4.7.1 period changed")
    head = next((i for i in range(top + 2, top + 6) if "All sectors" in rows[i]), None)
    if head is None:
        raise ValueError("Skills for Care Table 4.7.1 heading row not found")
    cols = {}
    for key, label in ASC_SECTORS:
        if label not in rows[head]:
            raise ValueError(f"Skills for Care Table 4.7.1 has no {label} column")
        cols[key] = rows[head].index(label)
    return lab, head, cols


def _check_asc_shares(out, cols):
    for sector in cols:
        parts = sum(out[(k, sector)][2] for k in ("british", "eu", "noneu"))
        non_british = out[("eu", sector)][2] + out[("noneu", sector)][2]
        # Shares are rounded to whole per cent, so parts can miss 100% by a point.
        if abs(parts - 1) > 0.011 or abs(non_british - out[("nonbritish", sector)][2]) > 0.011:
            raise ValueError(f"Skills for Care Table 4.7.1 {sector} shares do not add up")


def asc_cells(rows):
    """{(group or 'posts', sector): (row index, column index, value)} from Table 4.7.1."""
    lab, head, cols = _asc_layout(rows)
    labels = {}
    for i in range(head + 1, head + 8):
        labels.setdefault(rows[i][lab], i)
    out = {}
    for key, label in [("posts", "Total filled posts")] + ASC_GROUPS:
        if label not in labels:
            raise ValueError(f"Skills for Care Table 4.7.1 has no {label} row")
        i = labels[label]
        for sector, j in cols.items():
            value = num(rows[i][j])
            if value is None or value < 0 or (key != "posts" and value > 1):
                raise ValueError(f"Skills for Care Table 4.7.1 {label} {sector} is not valid")
            out[(key, sector)] = (i, j, value)
    _check_asc_shares(out, cols)
    return out


def _nhs_facts(facts, rows):
    cells = nhs_cells(rows)
    for m, (label, unit) in NHS_MEASURES.items():
        ids = {}
        for key, group_label, _ in NHS_GROUPS:
            i, j, value = cells[(m, key)]
            ids[key] = facts.add(
                Fact(
                    f"nhs.nat.{m}.{key}.{NHS_SUFFIX}",
                    value,
                    unit,
                    NHS_PERIOD,
                    NHS_SOURCE,
                    f"{NHS_SHEET}!{ref(i, j)}",
                    "published",
                    note=f"NHS trusts and core organisations, England, {label}, nationality group: {group_label}",
                )
            ).id
        known = [ids[k] for k in NHS_KNOWN]
        non_uk = [ids[k] for k in NHS_NON_UK]
        known_value = sum(facts[f].value for f in known)
        non_uk_value = sum(facts[f].value for f in non_uk)
        facts.add(
            Fact(
                f"nhs.nat.{m}.known.{NHS_SUFFIX}",
                known_value,
                unit,
                NHS_PERIOD,
                NHS_SOURCE,
                "calculated",
                "calculated",
                note=(
                    f"{label} with a recorded nationality: sum of the United Kingdom, EU, other EEA "
                    "and rest of world groups (Unknown left out). This is a sum of group counts, "
                    "not the published total"
                ),
                formula=" + ".join(known),
                inputs=known,
            )
        )
        facts.add(
            Fact(
                f"nhs.nat.{m}.nonuk.{NHS_SUFFIX}",
                non_uk_value,
                unit,
                NHS_PERIOD,
                NHS_SOURCE,
                "calculated",
                "calculated",
                note=f"{label} with a recorded nationality other than the United Kingdom",
                formula=" + ".join(non_uk),
                inputs=non_uk,
            )
        )
        facts.add(
            Fact(
                f"nhs.nat.{m}.nonuk.share.{NHS_SUFFIX}",
                100 * non_uk_value / known_value,
                f"% of {unit} with a recorded nationality",
                NHS_PERIOD,
                NHS_SOURCE,
                "calculated",
                "calculated",
                note="Non-UK nationality groups as a share of staff with a recorded nationality; staff with no recorded nationality are left out of both parts",
                formula=f"100 × ({' + '.join(non_uk)}) ÷ ({' + '.join(known)})",
                inputs=known,
            )
        )
        unknown, total = ids["unknown"], ids["all"]
        facts.add(
            Fact(
                f"nhs.nat.{m}.unknown.share.{NHS_SUFFIX}",
                100 * facts[unknown].value / facts[total].value,
                f"% of all {unit}",
                NHS_PERIOD,
                NHS_SOURCE,
                "calculated",
                "calculated",
                note="Staff with no recorded nationality as a share of all staff",
                formula=f"100 × {unknown} ÷ {total}",
                inputs=[unknown, total],
            )
        )


def _asc_facts(facts, rows):
    names = dict(ASC_GROUPS, posts="Total filled posts")
    sectors = dict(ASC_SECTORS)
    for (key, sector), (i, j, value) in asc_cells(rows).items():
        posts = key == "posts"
        facts.add(
            Fact(
                f"asc.nat.{key}.{sector}.{ASC_SUFFIX}",
                value if posts else round(100 * value, 6),
                "filled posts" if posts else "% of filled posts (known nationality, rounded)",
                ASC_PERIOD,
                ASC_SOURCE,
                f"{ASC_SHEET}!{ref(i, j)}",
                "published",
                note=f"Adult social care, England, {sectors[sector]}: {names[key]}",
                scale=1 if posts else 100,
            )
        )


def build(facts, nhs_file=NHS_FILE, asc_file=ASC_FILE):
    _nhs_facts(facts, sheet_rows(nhs_file, NHS_SHEET, 8))
    _asc_facts(facts, sheet_rows(asc_file, ASC_SHEET, 10))
