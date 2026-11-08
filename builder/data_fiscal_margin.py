"""The room under the fiscal rules in the OBR's central forecast, October 2026.

The OBR calls the amount by which a target is met its "margin". The figures are read from the
published Economic and fiscal outlook (retained in data/fetched/explain), by the words that come
before each figure, so a changed page stops the build instead of changing the figure silently.
"""

import re

from .data import Fact
from .explain import norm, page_text

SOURCE = "explain-obr-efo-oct-2026"
FILE = "data/fetched/explain/obr-efo-oct-2026.html"
MANDATE = (
    "In the central forecast, the fiscal mandate for the current budget to be in surplus in 2029-30 is met by a margin of",
    "Margin against the fiscal mandate (the current budget in surplus in 2029-30)",
)
PSNFL = (
    "The supplementary target for public sector net financial liabilities (PSNFL) to be falling as a share of GDP in 2029-30 is met by a margin of",
    "Margin against the supplementary target (PSNFL falling as a share of GDP in 2029-30)",
)


def _read(anchor):
    """The first number after the anchor words, which must appear once in the page."""
    text = page_text(FILE)
    words = norm(anchor)
    assert text.count(words) == 1, anchor
    tail = text[text.index(words) + len(words) :]
    return float(re.findall(r"\d[\d,]*", tail)[0].replace(",", ""))


def build(facts):
    for fid, (anchor, note) in (
        ("obr.margin.mandate.2029-30", MANDATE),
        ("obr.margin.psnfl.2029-30", PSNFL),
    ):
        facts.add(
            Fact(
                fid,
                _read(anchor),
                "£bn",
                "2029-30",
                SOURCE,
                f"after '{anchor}' number 1",
                "published",
                note=note,
            )
        )
