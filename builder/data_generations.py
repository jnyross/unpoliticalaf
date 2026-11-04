"""Facts for the generations page (John's question J12, "did our parents have it easier?").

State Pension age comes from the DWP timetable, saved as data/fetched/dwp/spa-timetable.pdf.
Each quoted row is searched for in that file, and the build stops if the wording has
changed, so a changed file cannot silently change a figure.
"""
import re

from pypdf import PdfReader

from .data import Fact
from .readers import ROOT, ons_series

SPA_SOURCE = "dwp-spa-timetable"
SPA_FILE = "data/fetched/dwp/spa-timetable.pdf"
FEE_SOURCE = "parl-cbp-tuition-fees"
FEE_FILE = "data/fetched/parl/CBP-10155.pdf"
HANSARD_SOURCE = "parl-hansard-1998-tuition-fees"
HANSARD_FILE = "data/fetched/parl/hansard-1998-12-07-tuition-fees.html"
CPI_FILE = "data/fetched/ons/l522.csv"
LIFE_SOURCE = "ons-single-year-life-tables-uk"
LIFE_FILE = "data/fetched/ons/single-year-life-tables-uk.xlsx"
LIFE_YEARS = (1994, 2024)  # 30 years apart: the same question, asked of the two ends of the period


def _pages(path):
    return [re.sub(r"\s+", " ", p.extract_text() or "") for p in PdfReader(ROOT / path).pages]


def _page_of(pages, phrase):
    for i, text in enumerate(pages):
        if phrase in text:
            return i + 1
    raise SystemExit(f"DWP State Pension age timetable changed: '{phrase}' not found in {SPA_FILE}")


def _html_text(path):
    import html as _h
    t = (ROOT / path).read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", t, flags=re.S)
    return re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", " ", t)))


def build_fees(facts):
    pages = _pages(FEE_FILE)
    p_1998 = _page_of(pages, "introduced means- tested tuition fees of up to £1,000 across the UK")
    p_2025 = _page_of(pages, "increase by £285 to £9,535 for the 2025-26 academic year")
    if "new £1,000 flat rate fee" not in _html_text(HANSARD_FILE):
        raise SystemExit("Hansard 7 December 1998 no longer says 'new £1,000 flat rate fee'")
    facts.add(Fact("fee.ft.1998", 1000, "£ a year", "1998-99 academic year", FEE_SOURCE,
                   f"page {p_1998} 'introduced means- tested tuition fees of up to £1,000 across the UK'",
                   note="Maximum fee for full-time undergraduates across the UK, paid up front rather than through a loan."))
    facts.add(Fact("fee.ft.2025", 9535, "£ a year", "2025-26 academic year", FEE_SOURCE,
                   f"page {p_2025} 'increase by £285 to £9,535 for the 2025-26 academic year'",
                   note="Cap for home undergraduates in England, as announced in November 2024."))
    _, cpi = ons_series(CPI_FILE)
    for y in (1998, 2025):
        if f"cpih.apr.{y}" not in facts:
            facts.add(Fact(f"cpih.apr.{y}", cpi[f"{y} APR"], "index (2015=100)", f"April {y}", "ons-l522", f"L522 row '{y} APR'"))
    base = facts["cpih.apr.2025"].value
    fee98 = facts["fee.ft.1998"].value
    real = fee98 * base / facts["cpih.apr.1998"].value
    facts.add(Fact("fee.ft.1998.2025", real, "£ a year, April 2025 prices", "1998-99 academic year, in 2025 prices", FEE_SOURCE,
                   "calculated from fee.ft.1998 and CPIH (ons-l522)", "calculated",
                   formula="fee.ft.1998 × cpih.apr.2025 ÷ cpih.apr.1998", inputs=["fee.ft.1998", "cpih.apr.2025", "cpih.apr.1998"],
                   note="April 1998 index used for the 1998-99 academic year. CPIH, the index the site uses for real pay."))


def build_life(facts):
    """Period life expectancy at exact age 30, from the single year life tables (UK edition)."""
    import openpyxl
    from openpyxl.utils import get_column_letter
    wb = openpyxl.load_workbook(ROOT / LIFE_FILE, data_only=True)
    for y in LIFE_YEARS:
        rows = [[c.value for c in r] for r in wb[str(y)].iter_rows()]
        hdr = next((r for r in rows if r and r[0] == "age"), None)
        if not hdr or hdr[5] != "ex" or hdr[7] != "age" or hdr[12] != "ex":
            raise SystemExit(f"ONS single year life tables changed: header layout on sheet {y} is not as expected")
        row_no = next((i for i, r in enumerate(rows) if len(r) > 12 and r[0] == 30 and r[7] == 30), None)
        if row_no is None:
            raise SystemExit(f"ONS single year life tables changed: no age 30 row on sheet {y}")
        for sex, col in (("male", 5), ("female", 12)):
            cell = f"{get_column_letter(col + 1)}{row_no + 1}"
            facts.add(Fact(f"life.ex30.{sex}.{y}", wb[str(y)][cell].value, "years of life expected", f"{y} (period life table)",
                           LIFE_SOURCE, f"{y}!{cell}",
                           note="Period expectation of life at exact age 30, UK. Single-year tables are more volatile than the 3-year tables; 2020 and 2021 reflect the pandemic."))


def build(facts):
    build_fees(facts)
    build_life(facts)
    pages = _pages(SPA_FILE)
    # Born 6 October 1954 to 5 April 1960: State Pension age is reached on the 66th birthday.
    p_66 = _page_of(pages, "6 October 1954 – 5 April 1960 66th birthday")
    # Born 6 December 1960 to 5 January 1961: 66 years and 9 months (the latest 1960 birthdays).
    p_9m = _page_of(pages, "6 December 1960 – 5 January 1961 66 years and 9 months")
    # Born from 6 April 1978 onwards: 68th birthday under current law (Pensions Act 2007).
    p_68 = _page_of(pages, "6 April 1978 onwards 68th birthday")
    # State Pension age in months (66 years = 792 months), as the timetable states it.
    facts.add(Fact("spa.months.1960.min", 66 * 12, "months of age", "people born in 1960", SPA_SOURCE,
                   f"page {p_66} row '6 October 1954 – 5 April 1960' '66th birthday'",
                   note="Born 1 January to 5 April 1960: State Pension age is the 66th birthday."))
    facts.add(Fact("spa.months.1960.max", 66 * 12 + 9, "months of age", "people born in 1960", SPA_SOURCE,
                   f"page {p_9m} row '6 December 1960 – 5 January 1961' '66 years and 9 months'",
                   note="Latest 1960 birthdays: 66 years and 9 months."))
    facts.add(Fact("spa.months.1990", 68 * 12, "months of age", "people born in 1990", SPA_SOURCE,
                   f"page {p_68} row '6 April 1978 onwards' '68th birthday'",
                   note="Current law: the rise from 67 to 68 is set for 2044 to 2046 (Pensions Act 2007), and a review could change it."))
    return {"fee_1998": "fee.ft.1998", "fee_2025": "fee.ft.2025", "fee_1998_real": "fee.ft.1998.2025"}
