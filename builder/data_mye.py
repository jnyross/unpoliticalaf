"""UK births, deaths and migration in the year to mid-2025, from the ONS mid-year population estimates bulletin.

The bulletin is an HTML page, so each figure is read from the sentence that states it:
the anchor text is found once in the page's plain text and the figure is the first number
after it. The locator "after '<anchor>' number 1" lets the check script read it again.
"""
import html as _html
import re

from .data import Fact
from .readers import ROOT

SOURCE = "ons-mye-uk-mid2025"
PATH = ROOT / "data/fetched/ons/mye-uk-mid2025.html"

# fact id, anchor sentence text (unique in the bulletin), unit
FIGURES = [
    ("mye.change.2025", "The size of the population is estimated to have increased by ", "people"),
    ("mye.births.2025", "We estimate that: there were ", "people"),
    ("mye.deaths.2025", "at least 43 years there were ", "people"),
    ("mye.natural.2025", "contributed an increase in population of ", "people"),
    ("mye.netmig.2025", "net international migration to the UK was ", "people"),
]


def plain_text(path=PATH):
    t = path.read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    t = _html.unescape(re.sub(r"<[^>]+>", " ", t))
    return re.sub(r"\s+", " ", t)


def read(anchor, n=1):
    text = plain_text()
    assert text.count(anchor) == 1, f"anchor not unique: {anchor!r}"
    tail = text[text.index(anchor) + len(anchor):]
    return float(re.findall(r"\d[\d,]*", tail)[n - 1].replace(",", ""))


def build(facts):
    for fid, anchor, unit in FIGURES:
        facts.add(Fact(fid, read(anchor), unit, "year to mid-2025", SOURCE,
                       f"after '{anchor}' number 1", "published", note="UK, year to mid-2025"))
