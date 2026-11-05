"""Welfare by benefit, from the DWP's benefit expenditure tables (Spring Forecast 2026).

The welfare page's long series (OBR, from 1955-56) does not split social security by benefit.
The DWP's tables do, so this module reads one year, 2021-22 (the last year the OBR measured),
and the first year of the long series, 1955-56, for the State Pension's share.

Two tables are used, and their figures are added together for the 2021-22 split:
- "Table 1a" (£ million, nominal): expenditure by benefit for benefits the DWP administers.
  Its "Total benefit expenditure" row is the DWP total.
- "Non-DWP Welfare" (£ million, nominal, Great Britain): personal tax credits, Child Benefit
  and other welfare, which the DWP reports separately. Its "Total" row is that total.

Each benefit is read from its own row, never from a row that adds other rows together, so no
benefit is counted twice. Whatever the rows do not cover is shown as "other", calculated as the
DWP total minus the named benefits. The 1955-56 share uses Table 1a alone, because the DWP tables
report tax credits and Child Benefit separately only from later years.

Amounts are nominal (cash) in the source. The page uses shares, which do not need adjusting for
inflation, so no deflator is applied here.
"""

from .data import Fact
from .readers import xlsx, ref

SOURCE = "dwp-benefit-exp-sf2026"
FILE = "data/fetched/dwp/outturn-and-forecast-tables-spring-forecast-2026.xlsx"
YEAR = "2021-22"
DWP_COLUMN = "2021/22"
FIRST = "1955-56"
FIRST_COLUMN = "1955/56"

# key, name on the page, sheet, the row's label (as it starts in the sheet), and whether the row
# is in Table 1a (True) or in Non-DWP Welfare (False). Each label is matched exactly once.
BENEFITS = [
    ("sp", "State Pension", "Table 1a", "State Pension", True),
    ("uc", "Universal Credit", "Table 1a", "Universal Credit", True),
    (
        "hb",
        "Housing benefit (not Universal Credit)",
        "Table 1a",
        "Housing benefits (exc. Universal Credit)",
        True,
    ),
    (
        "esa",
        "Employment and Support Allowance",
        "Table 1a",
        "Employment and Support Allowance",
        True,
    ),
    ("pc", "Pension Credit", "Table 1a", "Pension Credit", True),
    ("disab_dla", "Disability Living Allowance", "Table 1a", "Disability Living Allowance", True),
    (
        "disab_pip",
        "Personal Independence Payment",
        "Table 1a",
        "Personal Independence Payment",
        True,
    ),
    ("disab_aa", "Attendance Allowance", "Table 1a", "Attendance Allowance", True),
    ("carers", "Carer's Allowance", "Table 1a", "Carer's Allowance", True),
    ("tc", "Tax credits", "Non-DWP Welfare", "Personal tax credits", False),
    (
        "cb",
        "Child Benefit",
        "Non-DWP Welfare",
        "Child Benefit, One Parent Benefit & Guardian's Allowance",
        False,
    ),
]
# The DWP-coverage total used as the denominator: Table 1a's total plus the Non-DWP total.
TOTAL_T1A = ("Table 1a", "Total benefit expenditure")
TOTAL_NON = ("Non-DWP Welfare", "Total")
DISABILITY = ["disab_dla", "disab_pip", "disab_aa", "carers"]


def _find(rows, label):
    """Row index of a label in a sheet's first three columns (0-based, as in the file).

    Only the nominal block is searched: the sheets repeat their rows in real terms below a
    "real terms" heading, and those figures must not be read as cash amounts.
    """
    hits = []
    for i, r in enumerate(rows):
        text = " / ".join(str(c).strip() for c in r[:3] if isinstance(c, str) and c.strip())
        if "real terms" in text.lower():
            break
        if text == label or text.startswith(
            label + " /"
        ):  # Table 1a adds a category, e.g. "/ (NC / NIR)"
            hits.append(i)
    if len(hits) != 1:
        raise ValueError(f"expected one row for {label!r}, found {len(hits)}")
    return hits[0]


def _column(rows, header):
    for r in rows[:6]:
        if r and header in r:
            return list(r).index(header)
    raise ValueError(f"no column {header}")


def build(facts):
    wb = xlsx(FILE)
    sheets = {}
    for name in ("Table 1a", "Non-DWP Welfare"):
        rows = [list(r) for r in wb[name].iter_rows(values_only=True)]
        sheets[name] = rows

    def cash(sheet, label, year_col):
        rows = sheets[sheet]
        i = _find(rows, label)
        j = _column(rows, year_col)
        return i, j, rows[i][j]

    out = {"year": YEAR, "parts": {}}
    t1a_total = cash(*TOTAL_T1A, DWP_COLUMN)
    non_total = cash(*TOTAL_NON, DWP_COLUMN)
    total_m = t1a_total[2] + non_total[2]
    t1a_id = facts.add(
        Fact(
            f"dwp.cash.t1a.{YEAR}",
            t1a_total[2] / 1000,
            "£bn",
            YEAR,
            SOURCE,
            f"Table 1a!{ref(t1a_total[0], t1a_total[1])}",
            "published",
            note="DWP benefits, Table 1a total",
            scale=0.001,
        )
    )
    non_id = facts.add(
        Fact(
            f"dwp.cash.nondwp.{YEAR}",
            non_total[2] / 1000,
            "£bn",
            YEAR,
            SOURCE,
            f"Non-DWP Welfare!{ref(non_total[0], non_total[1])}",
            "published",
            note="Tax credits, Child Benefit and other welfare (Great Britain), total",
            scale=0.001,
        )
    )
    dwp_total = facts.add(
        Fact(
            f"dwp.cash.dwptotal.{YEAR}",
            total_m / 1000,
            "£bn",
            YEAR,
            SOURCE,
            "calculated",
            "calculated",
            note="DWP benefits plus Non-DWP welfare",
            formula=f"{t1a_id.id} + {non_id.id}",
            inputs=[t1a_id.id, non_id.id],
        )
    )
    out["total"] = dwp_total.id
    named = []
    for key, name, sheet, label, in_t1a in BENEFITS:
        i, j, raw = cash(sheet, label, DWP_COLUMN)
        val = 0 if raw in (None, "") else float(raw)
        f = facts.add(
            Fact(
                f"dwp.cash.{key}.{YEAR}",
                val / 1000,
                "£bn",
                YEAR,
                SOURCE,
                f"{sheet}!{ref(i, j)}",
                "published",
                note=name,
                scale=0.001,
            )
        )
        named.append(f)
        out["parts"][key] = f.id
    # Disability and carers' benefits: four separate rows, each counted once.
    dis = [facts[f"dwp.cash.{k}.{YEAR}"] for k in DISABILITY]
    dis_fact = facts.add(
        Fact(
            f"dwp.cash.disability.{YEAR}",
            sum(f.value for f in dis),
            "£bn",
            YEAR,
            SOURCE,
            "calculated",
            "calculated",
            note="Disability and carers' benefits",
            formula=" + ".join(f.id for f in dis),
            inputs=[f.id for f in dis],
        )
    )
    out["parts"]["disability"] = dis_fact.id
    # Other: what the named rows do not cover, from the DWP total.
    rest = [facts[f"dwp.cash.{k}.{YEAR}"] for k in ("sp", "uc", "hb", "esa", "pc", "tc", "cb")] + [
        dis_fact
    ]
    other_val = dwp_total.value - sum(f.value for f in rest)
    other = facts.add(
        Fact(
            f"dwp.cash.other.{YEAR}",
            other_val,
            "£bn",
            YEAR,
            SOURCE,
            "calculated",
            "calculated",
            note="Other benefits: the DWP total minus the named benefits",
            formula=f"{dwp_total.id} - (" + " + ".join(f.id for f in rest) + ")",
            inputs=[dwp_total.id] + [f.id for f in rest],
        )
    )
    out["parts"]["other"] = other.id
    for key in ["sp", "uc", "hb", "esa", "pc", "tc", "cb", "disability", "other"]:
        p = facts[out["parts"][key]]
        facts.add(
            Fact(
                f"dwp.share.{key}.{YEAR}",
                p.value * 100 / dwp_total.value,
                "% of DWP benefit spending",
                YEAR,
                SOURCE,
                "calculated",
                "calculated",
                note=p.note,
                formula=f"{p.id} × 100 ÷ {dwp_total.id}",
                inputs=[p.id, dwp_total.id],
            )
        )
    # The State Pension's share in 1955-56, on Table 1a alone.
    t_first = cash("Table 1a", "State Pension", FIRST_COLUMN)
    t_first_total = cash(*TOTAL_T1A, FIRST_COLUMN)
    sp_first = facts.add(
        Fact(
            f"dwp.cash.sp.{FIRST}",
            float(t_first[2]) / 1000,
            "£bn",
            FIRST,
            SOURCE,
            f"Table 1a!{ref(t_first[0], t_first[1])}",
            "published",
            note="State Pension",
            scale=0.001,
        )
    )
    tot_first = facts.add(
        Fact(
            f"dwp.cash.t1a.{FIRST}",
            float(t_first_total[2]) / 1000,
            "£bn",
            FIRST,
            SOURCE,
            f"Table 1a!{ref(t_first_total[0], t_first_total[1])}",
            "published",
            note="DWP benefits, Table 1a total",
            scale=0.001,
        )
    )
    facts.add(
        Fact(
            f"dwp.share.sp.{FIRST}",
            sp_first.value * 100 / tot_first.value,
            "% of Table 1a benefit spending",
            FIRST,
            SOURCE,
            "calculated",
            "calculated",
            note="State Pension",
            formula=f"{sp_first.id} × 100 ÷ {tot_first.id}",
            inputs=[sp_first.id, tot_first.id],
        )
    )
    return out
