"""UK public sector net debt and net borrowing over 125 years, from the OBR's historical public finances database.

One sheet of the database, "Aggregates (per cent of GDP)", gives for each financial year
from 1900-01 to 2022-23:

- public sector net debt (PSND): what the public sector owes, less its financial assets, at
  the end of the year, as a share of GDP;
- public sector net borrowing (PSNB): the amount borrowed in the year, as a share of GDP.

The database's contents sheet says the OBR took these from its own 2023 compilation for
1900-01 onwards, so the series is one source throughout. Figures before 1900-01 come from a
different source and are not used here. The database is not a set of national statistics,
and its contents sheet says judgements were made to keep years consistent.
"""

import re

from .data import Fact
from .readers import xlsx, ref

SOURCE = "obrhist-aggregates"
FILE = "data/raw/OBR_Historical_public_finances_database.xlsx"
SHEET = "Aggregates (per cent of GDP)"
FIRST = "1900-01"  # the first year from the OBR's own 2023 compilation (its note 1 and note 2)
COL_PSNB, COL_PSND = 2, 3


def build(facts):
    wb = xlsx(FILE)
    rows = [[c.value for c in r] for r in wb[SHEET].iter_rows()]
    years = {}
    for i, r in enumerate(rows):
        if len(r) > 1 and r[1] and re.fullmatch(r"\d{4}-\d{2}", str(r[1])):
            years[str(r[1])] = i
    ys = [y for y in sorted(years) if y >= FIRST]
    for y in ys:
        i = years[y]
        for key, col in (("psnd", COL_PSND), ("psnb", COL_PSNB)):
            v = rows[i][col]
            if not isinstance(v, (int, float)):
                raise ValueError(f"{SHEET} {y} {key} is not a number: {v!r}")
            facts.add(
                Fact(
                    f"debt.{key}.{y}",
                    float(v),
                    "% of GDP",
                    y,
                    SOURCE,
                    f"{SHEET}!{ref(i, col)}",
                    "published",
                    note=(
                        "public sector net debt" if key == "psnd" else "public sector net borrowing"
                    ),
                )
            )
    return {"years": ys, "first": ys[0], "last": ys[-1]}
