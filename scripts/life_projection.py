"""Deterministic public life preview derived from the retained school foundation.

Importing this module reads and writes nothing. The controller owns output.
"""
from decimal import Decimal, ROUND_HALF_UP, localcontext
import json
from pathlib import Path

from school_projection import project as school_project

ROOT = Path(__file__).resolve().parents[1]
YEARS = tuple(range(2008, 2027))
PHASES = ("5kyxd", "tfHTE", "TaWMP", "cDwC3")
FORMULA = "right pupils / right classes - left pupils / left classes"
MISSING = "No retained school observation for one or both anchors."


def _round(value, signed=False):
    return format(value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP),
                  "+.1f" if signed else ".1f")


def _mean(row):
    return Decimal(row["published"]["QtxWw"]["raw"]) / Decimal(row["published"]["EAicq"]["raw"])


def project(root=ROOT):
    schools = school_project(root)
    totals = {(r["anchor"], r["filters"]["5cGdi"]): r for r in schools["rows"]
              if r["filters"]["cAd31"] == "XdTUf"}
    observed = sorted({year for year, _ in totals})
    anchors = []
    for year in YEARS:
        row = totals.get((year, PHASES[0]))
        anchors.append({
            "year": year, "available": row is not None,
            "period": row["timePeriod"]["period"] if row else None,
            "census": row["census"] if row else None,
            "previous": year - 1 if year > YEARS[0] else None,
            "next": year + 1 if year < YEARS[-1] else None,
            "nearest": None if row else min(observed, key=lambda value: (abs(value - year), value)),
        })
    comparisons = []
    with localcontext() as context:
        context.prec = 50
        for left_year in YEARS:
            for right_year in YEARS:
                for phase in PHASES:
                    left = totals.get((left_year, phase))
                    right = totals.get((right_year, phase))
                    available = left is not None and right is not None
                    operands = []
                    if available:
                        for row in (right, left):
                            for indicator in ("QtxWw", "EAicq"):
                                value = row["published"][indicator]
                                operands.append({
                                    "raw": value["raw"], "indicator": indicator,
                                    "anchor": row["anchor"], "phase": phase,
                                    "source": dict(value["source"]),
                                })
                    comparisons.append({
                        "id": f"{left_year}:{right_year}:{phase}",
                        "from": left_year, "to": right_year, "phase": phase,
                        "available": available, "reason": None if available else MISSING,
                        "from_period": left["timePeriod"]["period"] if left else None,
                        "to_period": right["timePeriod"]["period"] if right else None,
                        "left": _round(_mean(left)) if available else None,
                        "right": _round(_mean(right)) if available else None,
                        "display": _round(_mean(right) - _mean(left), signed=True) if available else None,
                        "unit": "pupils per class", "formula": FORMULA, "operands": operands,
                    })
    return {
        "schema_version": 1, "domain": "life", "private": False,
        "default_anchor": 2026,
        "topics": {"schools": "available", "work": "not yet built",
                   "earnings": "not yet built", "housing": "not yet built",
                   "holidays": "not yet built"},
        "schools": schools, "anchors": anchors, "comparisons": comparisons,
    }


def encode(data):
    """The controller writes identical UTF-8 bytes to both reviewed data paths."""
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            + "\n").encode("utf-8")
