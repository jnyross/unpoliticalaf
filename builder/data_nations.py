"""Housing tenure and class sizes for Wales, Scotland and Northern Ireland.

Each nation runs housing and education separately and measures them its own
way, so every figure keeps its own definition. Nothing here is combined into a
UK total, and nothing is filled in where a nation publishes no figure.
"""

import re

from .data import Fact, YEARS, num
from .readers import xlsx, ods, ref, csv_rows

WALES_STOCK = "data/fetched/nations/wales-dwelling-stock-by-tenure.csv"
SCOT_STOCK = "data/fetched/nations/scot-stock-by-tenure-2025.xlsx"
NI_HOUSING = "data/fetched/nations/ni-housing-stats-25-26-tables1.ods"
SCOT_PUPILS = "data/fetched/nations/scot-pupil-census-supplementary-2025.xlsx"


def _share(facts, fid, part, whole, period, source):
    a, b = facts[part], facts[whole]
    v = None if a.value is None or b.value is None else 100 * a.value / b.value
    facts.add(
        Fact(
            fid,
            v,
            "% of homes",
            period,
            source,
            a.locator,
            "calculated",
            formula=f"100 × {a.id} ÷ {b.id}",
            inputs=[a.id, b.id],
        )
    )


def housing_wales(facts):
    """Dwellings by tenure in Wales at 31 March (Welsh Government dwelling stock estimates, StatsWales)."""
    tenures = {
        "All tenures": "all",
        "Owner occupied": "owner",
        "Privately rented": "private",
        "Total social Housing": "social",
    }
    out = {}
    for line, r in enumerate(csv_rows(WALES_STOCK), start=2):
        if r["Area"] != "Wales" or r["Data description"] != "Dwelling stock estimates (number)":
            continue
        m = re.fullmatch(r"31/03/(\d{4})", r["Period"])
        t = tenures.get(r["Tenure"].strip())
        if not m or not t or int(m.group(1)) not in YEARS:
            continue
        y = int(m.group(1))
        st = "provisional" if "Provisional" in r["Notes"] else "published"
        facts.add(
            Fact(
                f"house.nat.n.{t}.wales.{y}",
                num(r["Data values"]),
                "dwellings",
                f"31 March {y}",
                "wales-dwelling-stock",
                f"wales-dwelling-stock-by-tenure.csv line {line}",
                st,
                note=r["Notes"],
            )
        )
        out.setdefault(y, set()).add(t)
    years = sorted(y for y, ts in out.items() if ts == set(tenures.values()))
    for y in years:
        for t in ("owner", "private", "social"):
            _share(
                facts,
                f"house.nat.{t}.wales.{y}",
                f"house.nat.n.{t}.wales.{y}",
                f"house.nat.n.all.wales.{y}",
                f"31 March {y}",
                "wales-dwelling-stock",
            )
    return years


def housing_scotland(facts):
    """Dwellings by tenure in Scotland at 31 March (Scottish Government housing statistics: stock by tenure)."""
    sheet = "Tbl Stock by tenure"
    rows = [[c.value for c in r] for r in xlsx(SCOT_STOCK)[sheet].iter_rows()]
    hi = next(i for i, r in enumerate(rows) if r and r[0] == "Year")
    head = [str(h or "") for h in rows[hi]]

    def col(start):
        return next(j for j, h in enumerate(head) if h.startswith(start))

    cols = {
        "owner": col("Proportion of total dwellings which are owner occupied"),
        "private": col("Proportion of total dwellings which are Rented privately"),
        "vacant": col("Proportion of total dwellings which are vacant private"),
        "ha": col("Proportion of total dwellings which are from housing associations"),
        "council": col("Proportion of total dwellings which are from local authorities"),
    }
    years = []
    for i in range(hi + 1, len(rows)):
        m = re.fullmatch(r"March (\d{4})", str(rows[i][0] or "").strip())
        if not m or int(m.group(1)) not in YEARS:
            continue
        y = int(m.group(1))
        for t, j in cols.items():
            facts.add(
                Fact(
                    f"house.nat.{t}.scotland.{y}",
                    None if num(rows[i][j]) is None else 100 * num(rows[i][j]),
                    "% of homes",
                    f"31 March {y}",
                    "scot-stock-by-tenure",
                    f"{sheet}!{ref(i, j)}",
                    "published",
                    scale=100,
                )
            )
        a, b = facts[f"house.nat.council.scotland.{y}"], facts[f"house.nat.ha.scotland.{y}"]
        facts.add(
            Fact(
                f"house.nat.social.scotland.{y}",
                a.value + b.value,
                "% of homes",
                f"31 March {y}",
                "scot-stock-by-tenure",
                a.locator,
                "calculated",
                formula=f"{a.id} + {b.id}",
                inputs=[a.id, b.id],
            )
        )
        years.append(y)
    return years


def housing_ni(facts):
    """Household tenure in Northern Ireland, Family Resources Survey (NI housing statistics 2025-26, table 1.3)."""
    sheet = "T1_3"
    rows = ods(NI_HOUSING)[sheet]
    hi = next(i for i, r in enumerate(rows) if r and r[0] == "Tenure")
    labels = {
        "Owned outright": "outright",
        "Buying with a mortgage": "mortgage",
        "Social rented sector3": "social",
        "Private rented sector": "private",
    }
    years = []
    for j, h in enumerate(rows[hi]):
        m = re.fullmatch(r"(\d{4})-\d{2}", str(h or "").strip())
        if not m or int(m.group(1)) not in YEARS:
            continue
        y = int(m.group(1))
        for i in range(hi + 1, len(rows)):
            t = labels.get(str(rows[i][0] or "").strip()) if rows[i] else None
            if t:
                facts.add(
                    Fact(
                        f"house.nat.{t}.ni.{y}",
                        num(rows[i][j]) if j < len(rows[i]) else None,
                        "% of households",
                        f"{y}-{str(y + 1)[2:]} survey year",
                        "ni-housing-2025-26",
                        f"{sheet}!{ref(i, j)}",
                        "published",
                        note="Rounded to whole numbers in the source.",
                    )
                )
        a, b = facts[f"house.nat.outright.ni.{y}"], facts[f"house.nat.mortgage.ni.{y}"]
        facts.add(
            Fact(
                f"house.nat.owner.ni.{y}",
                None if None in (a.value, b.value) else a.value + b.value,
                "% of households",
                a.period,
                "ni-housing-2025-26",
                a.locator,
                "calculated",
                formula=f"{a.id} + {b.id}",
                inputs=[a.id, b.id],
            )
        )
        years.append(y)
    return years


def schools_scotland(facts):
    """Average primary class size in Scotland, all stages, September pupil census (table 2.10)."""
    sheet = "Table 2.10 "
    rows = [[c.value for c in r] for r in xlsx(SCOT_PUPILS)[sheet].iter_rows()]
    hi = next(i for i, r in enumerate(rows) if r and r[0] == "Year")
    j = next(k for k, h in enumerate(rows[hi]) if str(h or "").strip() == "All stages")
    out = {}
    for i in range(hi + 1, len(rows)):
        if not rows[i] or not re.fullmatch(r"\d{4}", str(rows[i][0] or "").strip()):
            continue
        y = int(str(rows[i][0]).strip())
        if y not in YEARS:
            continue
        fid = f"school.scotland.primary.{y}"
        facts.add(
            Fact(
                fid,
                num(rows[i][j]),
                "pupils per class",
                f"September {y} census ({y}/{str(y + 1)[2:]} school year)",
                "scot-pupil-census-2025",
                f"{sheet}!{ref(i, j)}",
                "published",
                note="Unrounded in the source for most years; shown to 1 decimal place.",
            )
        )
        out[y] = fid
    return out


def build(facts):
    return {
        "wales": housing_wales(facts),
        "scotland": housing_scotland(facts),
        "ni": housing_ni(facts),
        "school_scotland": schools_scotland(facts),
    }
