"""Facts for the generations page (John's question J12, "did our parents have it easier?").

State Pension age comes from the DWP timetable, saved as data/fetched/dwp/spa-timetable.pdf.
Each quoted row is searched for in that file, and the build stops if the wording has
changed, so a changed file cannot silently change a figure.
"""
import re

from pypdf import PdfReader

from .data import Fact
from .readers import ROOT

SPA_SOURCE = "dwp-spa-timetable"
SPA_FILE = "data/fetched/dwp/spa-timetable.pdf"


def _pages(path):
    return [re.sub(r"\s+", " ", p.extract_text() or "") for p in PdfReader(ROOT / path).pages]


def _page_of(pages, phrase):
    for i, text in enumerate(pages):
        if phrase in text:
            return i + 1
    raise SystemExit(f"DWP State Pension age timetable changed: '{phrase}' not found in {SPA_FILE}")


def build(facts):
    pages = _pages(SPA_FILE)
    # Born 6 October 1954 to 5 April 1960: State Pension age is reached on the 66th birthday.
    p_66 = _page_of(pages, "6 October 1954 – 5 April 1960 66th birthday")
    # Born 6 December 1960 to 5 January 1961: 66 years and 9 months (the latest 1960 birthdays).
    p_9m = _page_of(pages, "6 December 1960 – 5 January 1961 66 years and 9 months")
    # Born from 6 April 1978 onwards: 68th birthday under current law (Pensions Act 2007).
    p_68 = _page_of(pages, "6 April 1978 onwards 68th birthday")
    facts.add(Fact("spa.months.1960.min", 0, "months after age 66", "people born in 1960", SPA_SOURCE,
                   f"page {p_66} row '6 October 1954 – 5 April 1960' '66th birthday'",
                   note="Born 1 January to 5 April 1960: State Pension age is the 66th birthday."))
    facts.add(Fact("spa.months.1960.max", 9, "months after age 66", "people born in 1960", SPA_SOURCE,
                   f"page {p_9m} row '6 December 1960 – 5 January 1961' '66 years and 9 months'",
                   note="Latest 1960 birthdays: 66 years and 9 months."))
    facts.add(Fact("spa.years.1990", 68, "years", "people born in 1990", SPA_SOURCE,
                   f"page {p_68} row '6 April 1978 onwards' '68th birthday'",
                   note="Current law: the rise from 67 to 68 is set for 2044 to 2046 (Pensions Act 2007), and a review could change it."))
    return {"spa_months_1960": ("spa.months.1960.min", "spa.months.1960.max"), "spa_years_1990": "spa.years.1990"}
