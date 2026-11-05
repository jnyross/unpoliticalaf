"""Household taxes as a share of gross income over time, 1977 to the latest year.

Two ONS methods are kept apart and never joined:

- "households": ONS historical tables, 1977 to 2017/18. Households are ranked by their
  size-adjusted disposable income and split into fifths with equal numbers of households.
  Shares are calculated here as (total direct taxes + total indirect taxes) ÷ gross income.
- "people": ONS yearly reference tables, Table 8. People are ranked by their household's
  size-adjusted disposable income and split into fifths with equal numbers of people.
  2017/18 is published both ways, so the effect of the ranking change can be seen.
  From 2018/19 the tables adjust for top earners being under-recorded in the survey.
"""

from .data import Fact, num
from .readers import ref, xlsx

QS = ("q1", "q2", "q3", "q4", "q5", "all")
HIST = "data/fetched/etb/hist-quintile-all.xlsx"
# (period label, source id, file) for ONS Table 8, all individuals. 2023/24 is read from the
# file the rest of the site already uses (source "etb").
YEARLY = [
    ("2017/18", "etb-fye2018", "data/fetched/etb/fye2018.xlsx"),
    ("2018/19", "etb-fye2019", "data/fetched/etb/fye2019.xlsx"),
    ("2019/20", "etb-fye2020", "data/fetched/etb/fye2020.xlsx"),
    ("2020/21", "etb-fye2021", "data/fetched/etb/fye2021.xlsx"),
    ("2021/22", "etb-fye2022", "data/fetched/etb/fye2022.xlsx"),
    ("2022/23", "etb-fye2023", "data/fetched/etb/fye2023.xlsx"),
    ("2023/24", "etb", "data/payers/raw/ons-etb-fye2024.xlsx"),
]
TOP_ADJUSTED_FROM = "2018/19"  # first yearly tables with ONS's top-earner adjustment
LUMP_SUMS_FROM = "2019/20"  # first yearly tables whose direct taxes include deferred lump sums


def label(sheet):
    """'1977' stays; '1994-95' -> '1994/95'; '1999-2000' -> '1999/00'."""
    if "-" not in sheet:
        return sheet
    a, b = sheet.split("-")
    return f"{a}/{b[-2:]}"


def key(period):
    return period.replace("/", "-")


def _strip(v):
    return " ".join(str(v).split()) if v is not None else ""


def _households(facts):
    wb = xlsx(HIST)
    periods = []
    for sheet in wb.sheetnames:
        rows = [[c.value for c in r] for r in wb[sheet].iter_rows()]
        hi = next(i for i, r in enumerate(rows) if len(r) > 5 and _strip(r[1]) == "Bottom")
        if [_strip(v) for v in rows[hi][1:6]] != ["Bottom", "2nd", "3rd", "4th", "Top"]:
            raise ValueError(f"{sheet}: unexpected quintile header")
        # the all-households column follows the five fifths; its heading sits on the header row or above it
        if not any(
            _strip(rows[k][6]).lower().startswith(("all", "holds")) for k in range(hi - 2, hi + 1)
        ):
            raise ValueError(f"{sheet}: no all-households column")
        cols = dict(zip(QS, range(1, 7)))

        def row(lab, start=0):
            return next(i for i in range(start, len(rows)) if _strip(rows[i][0]) == lab)

        gi = row("Gross income")
        di = next(i for i, r in enumerate(rows) if _strip(r[0]).startswith("Direct taxes"))
        lines = {
            "gross": gi,
            "direct": row("Total", di + 1),
            "indirect": row("Total indirect taxes"),
        }
        p = label(sheet)
        k = key(p)
        sid = (
            "etb-hist-quintile-all" if int(p[:4]) < 1997 else "etb-hist-quintile-all-2"
        )  # two record pages
        for q, j in cols.items():
            for m, i in lines.items():
                facts.add(
                    Fact(
                        f"etbh.{m}.{k}.{q}",
                        num(rows[i][j]),
                        "£ a year per household",
                        p,
                        sid,
                        f"{sheet}!{ref(i, j)}",
                        "outturn",
                    )
                )
            g, d, ind = (f"etbh.{m}.{k}.{q}" for m in ("gross", "direct", "indirect"))
            shares = [("pall", [d, ind, g], f"100 × ({d} + {ind}) ÷ {g}")]
            if q == "all":  # the direct/indirect split is shown for everyone only
                shares += [
                    ("pdirect", [d, g], f"100 × {d} ÷ {g}"),
                    ("pindirect", [ind, g], f"100 × {ind} ÷ {g}"),
                ]
            for m, ids, formula in shares:
                top = sum(facts[x].value for x in ids[:-1])
                facts.add(
                    Fact(
                        f"etbh.{m}.{k}.{q}",
                        100 * top / facts[g].value,
                        "% of gross household income",
                        p,
                        sid,
                        facts[ids[0]].locator,
                        "calculated",
                        formula=formula,
                        inputs=ids,
                    )
                )
        periods.append(p)
    return periods


def _people(facts):
    periods = []
    for p, sid, path in YEARLY:
        k = key(p)
        if sid == "etb":  # already read for the household tax page; give it the series' ids
            for m, src in (("direct", "direct"), ("indirect", "indirect"), ("all", "all")):
                for q in QS:
                    f = facts[f"etb.t8.gross.{src}.{q}"]
                    facts.add(
                        Fact(f"etbp.{m}.{k}.{q}", f.value, f.unit, p, "etb", f.locator, "outturn")
                    )
            periods.append(p)
            continue
        rows = [[c.value for c in r] for r in xlsx(path)["Table 8"].iter_rows()]
        hi = next(i for i, r in enumerate(rows) if any(_strip(v) == "Bottom" for v in r))
        hdr = [_strip(v) for v in rows[hi]]
        cols = {
            q: next(j for j, v in enumerate(hdr) if v.startswith(lab))
            for q, lab in zip(QS, ("Bottom", "2nd", "3rd", "4th", "Top", "All individuals"))
        }
        found, section = {}, False
        for i, r in enumerate(rows):
            head = " ".join(_strip(v) for v in r[:2])
            if "ercentages of gross" in head:
                section = True
            elif "ercentages of" in head:
                section = False
            if not section:
                continue
            lab = next(
                (_strip(v) for v in r[:3] if isinstance(v, str) and "ercentages" not in v), ""
            )
            m = {
                "All direct taxes": "direct",
                "Direct taxes": "direct",
                "All indirect taxes": "indirect",
                "Indirect taxes": "indirect",
                "All taxes": "all",
            }.get(lab)
            if m and num(r[cols["q1"]]) is not None:
                found[m] = i
        if set(found) != {"direct", "indirect", "all"}:
            raise ValueError(f"{path}: Table 8 rows not found ({found})")
        for m, i in found.items():
            for q, j in cols.items():
                facts.add(
                    Fact(
                        f"etbp.{m}.{k}.{q}",
                        num(rows[i][j]),
                        "% of gross household income",
                        p,
                        sid,
                        f"Table 8!{ref(i, j)}",
                        "outturn",
                    )
                )
        periods.append(p)
    return periods


def build(facts):
    hh = _households(facts)
    pp = _people(facts)
    if hh[-1] != pp[0]:
        raise ValueError("the two methods should overlap in one year")
    return {
        "households": hh,
        "people": pp,
        "overlap": pp[0],
        "top_adjusted_from": TOP_ADJUSTED_FROM,
        "lump_sums_from": LUMP_SUMS_FROM,
    }
