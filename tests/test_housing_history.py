"""Home ownership by age since 1991 and mortgage rates since 2008: lineage, scope and no splicing."""

import csv
import json
import re
import xml.etree.ElementTree as ET

import pytest
from pypdf import PdfReader

from builder import data_buyers as buyers
from builder import pages_generations, uncertainty
from builder.build import render
from builder.check import as_number, cell_value
from builder.data import Facts
from builder.html import fmt
from builder.pages_life_extra import _owners_by_age, _quoted_block
from builder.readers import ROOT

RECEIPTS = json.loads((ROOT / "data/fetched/receipts.json").read_text())
MANIFEST = {s["id"]: s for s in json.loads((ROOT / "sources/manifest.json").read_text())["sources"]}
NEW_SOURCES = {
    "ehs-0809-annex-ch1",
    "ehs-0809-report",
    "ons-lfs-guide-household",
    "boe-quoted-2yr-75ltv",
    "boe-quoted-rates-notes",
    "boe-effective-rates-notes",
    "boe-rate-series-titles",
    "boe-form-er-definitions",
}
# Method details from the Bank's retired HTML notes pages that no retained source supports.
UNSUPPORTED_RATE_CLAIMS = (
    "advertis",
    "most competitive",
    "first-time buyer",
    "internet",
    "broker",
    "February 2019",
    "whole market",
    "sample of lenders",
    "weighted by how much each lends",
    "unincorporated",
    "changed its definitions",
    "APR",
    "taken out",
    "all new mortgages",
)


@pytest.fixture(scope="module")
def built():
    facts = Facts()
    out = buyers.build(facts)
    return facts, out


def _text(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def _src(source_id):
    return "data/fetched/" + RECEIPTS[source_id]["file"]


def _pdf_text(source_id, page):
    reader = PdfReader(ROOT / "data/fetched" / RECEIPTS[source_id]["file"])
    return re.sub(r"\s+", " ", reader.pages[page - 1].extract_text())


def _series_metadata(source_id):
    """The Bank of England Database XML for one series: attributes, categories and notes."""
    root = ET.parse(ROOT / "data/fetched" / RECEIPTS[source_id]["file"]).getroot()
    cubes = [el for el in root.iter() if el.tag.endswith("Cube")]
    categories = {c.get("CAT_NAME"): c.get("VAL_DESC") for c in cubes if c.get("CAT_NAME")}
    span = next(c for c in cubes if c.get("FIRST_OBS"))
    notes = [" ".join(el.text.split()) for el in root.iter() if el.tag.endswith("SERIES_COM")]
    return cubes[0].attrib, categories, (span.get("FIRST_OBS"), span.get("LAST_OBS")), notes


@pytest.fixture(scope="module")
def site_pages():
    # render() refills the shared margin table from its own facts; later tests rely on its
    # earlier state, so put it back.
    saved_margins = dict(uncertainty.MARGINS)
    saved_info = dict(uncertainty.INFO)
    try:
        _, _, pages, _ = render()
    finally:
        uncertainty.MARGINS.clear()
        uncertainty.MARGINS.update(saved_margins)
        uncertainty.INFO.clear()
        uncertainty.INFO.update(saved_info)
    return pages


def test_new_sources_are_retained_with_receipts():
    for sid in NEW_SOURCES:
        assert MANIFEST[sid]["file"] == RECEIPTS[sid]["file"]
        size = (ROOT / "data/fetched" / RECEIPTS[sid]["file"]).stat().st_size
        assert size == RECEIPTS[sid]["bytes"]


@pytest.mark.parametrize(
    "fid,source,locator,value",
    [
        ("own.hrp.16-24.1991", "ehs-0809-annex-ch1", "AT1.4 Ten x age, 4 yrs!K16", 36.1255),
        ("own.hrp.25-34.1991", "ehs-0809-annex-ch1", "AT1.4 Ten x age, 4 yrs!K17", 66.5278),
        ("own.hrp.35-44.1991", "ehs-0809-annex-ch1", "AT1.4 Ten x age, 4 yrs!K18", 77.9841),
        ("own.hrp.65+.1991", "ehs-0809-annex-ch1", "AT1.4 Ten x age, 4 yrs!K21", 57.9819),
        ("own.hrp.25-34.2008", "ehs-annex-ch1", "AT1_4!H74", 51.4779),
        ("own.hrp.25-34.2024", "ehs-annex-ch1", "AT1_4!X74", 47.6530),
        ("own.hrp.35-44.2024", "ehs-annex-ch1", "AT1_4!X83", 56.4275),
        ("own.hrp.65+.2024", "ehs-annex-ch1", "AT1_4!X110", 78.8539),
        ("rate.quoted.2008-01", "boe-quoted-2yr-75ltv", "IUMBV34 line 2", 5.97),
        ("rate.quoted.2008-06", "boe-quoted-2yr-75ltv", "IUMBV34 line 7", 6.6),
        ("rate.quoted.2021-09", "boe-quoted-2yr-75ltv", "IUMBV34 line 166", 1.2),
    ],
)
def test_exact_cells_reread_independently(built, fid, source, locator, value):
    facts, _ = built
    f = facts[fid]
    assert (f.source, f.locator, f.status) == (source, locator, "published")
    assert f.value == pytest.approx(value, abs=1e-4)
    assert as_number(cell_value(_src(source), locator)) == pytest.approx(f.value)


def test_1991_lineage_is_the_labour_force_survey_by_head_of_household(built):
    facts, _ = built
    sheet = "AT1.4 Ten x age, 4 yrs"
    src = _src("ehs-0809-annex-ch1")
    lfs_note = "Sources: 1981, 1991, 2001 ONS Labour Force Survey"
    assert cell_value(src, f"{sheet}!A44").startswith(lfs_note)
    assert cell_value(src, f"{sheet}!A16") == "1991"
    assert "1981–1991 ONS Labour Force Survey" in _pdf_text("ehs-0809-report", 15)
    glossary = _pdf_text("ehs-0809-report", 97)
    assert "a person in whose name the accommodation is owned or rented" in glossary
    assert "it is the person with the highest income" in glossary
    guide = _pdf_text("ons-lfs-guide-household", 11)
    switch = "From spring 2001 the LFS is switching from using Head of Household (HOH) to"
    assert switch + " Household Reference Person (HRP)" in guide
    assert "HRPs tend to be slightly younger than HOHs" in guide
    for g in buyers.HRP_GROUPS:
        note = facts[f"own.hrp.{g}.1991"].note
        assert "head of household" in note and "Labour Force Survey" in note


def test_fc2101_1991_row_is_the_same_lfs_row(built):
    """FC2101 repeats 1991 without a source; it matches the annex that names one, in the bands both share."""
    facts, _ = built
    fc = _src("ehs-fc2101")
    for g, cell in (("16-24", "W9"), ("25-34", "X9"), ("35-44", "Y9")):
        assert str(cell_value(fc, "2021-22!V9")).startswith("1991")
        fc_value = as_number(cell_value(fc, f"2021-22!{cell}"))
        assert fc_value == pytest.approx(facts[f"own.hrp.{g}.1991"].value)
    # 1991 is read from the annex that names its source, not from FC2101
    assert "own.25-34.1991" not in facts


def test_fc2101_is_by_household_reference_person_not_people(built):
    facts, out = built
    for g in buyers.AGE_GROUPS:
        for y in out["own_years"]:
            note = facts[f"own.{g}.{y}"].note
            assert "household reference person" in note and "not people" in note
    # FC2101 and the 2024-25 annex give the same 2008-09 and 2021-22 values for the shared bands
    for g in ("16-24", "25-34", "35-44"):
        hrp_value = facts[f"own.hrp.{g}.2008"].value
        assert facts[f"own.{g}.2008"].value == pytest.approx(hrp_value, abs=1e-6)
    assert as_number(cell_value(_src("ehs-annex-ch1"), "AT1_4!U74")) == pytest.approx(
        facts["own.25-34.2021"].value, abs=1e-6
    )


def test_no_exact_age_or_person_level_fact(built):
    facts, _ = built
    assert not [fid for fid in facts if re.search(r"(^|\.)30(\.|$)|age30|people", fid)]
    assert buyers.HRP_GROUPS == ["16-24", "25-34", "35-44", "45-54", "55-64", "65+"]


def test_quoted_and_effective_rates_are_separate_series(built):
    facts, out = built
    quoted, effective = out["quoted_months"], out["rate_months"]
    assert quoted[0] == "2008-01" and effective[0] == "2016-01"
    assert all(facts[f"rate.quoted.{m}"].source == "boe-quoted-2yr-75ltv" for m in quoted)
    assert all(facts[f"rate.new.{m}"].source == "boe-mortgage-rates" for m in effective)
    assert not [m for m in effective if m < "2016-01"]
    assert all("not joined" in facts[f"rate.quoted.{m}"].note for m in quoted)
    quoted_csv = ROOT / "data/fetched" / RECEIPTS["boe-quoted-2yr-75ltv"]["file"]
    head = quoted_csv.read_text().splitlines()[0]
    assert head == "DATE,IUMBV34"


def test_mortgage_share_has_no_take_home_or_2008_figure(built):
    facts, out = built
    assert out["share_years"][0] == 2010
    assert "mortshare.2008" not in facts and "mortshare.2009" not in facts
    assert not [fid for fid in facts if re.search(r"net|take.?home|disposable", fid)]
    assert "not take-home pay" in facts["mortshare.2010"].note


def test_rendered_limits_are_prominent(built):
    facts, out = built

    def num(fid, kind):
        return fmt(facts[fid].value, kind)

    first, last = out["own_years"][0], out["own_years"][-1]
    owners = _text("".join(_owners_by_age(num, out, first, last)))
    assert "Households, not people, and age groups, not single ages" in owners
    assert "cannot give a figure for people aged exactly 30" in owners
    assert "head of household" in owners and "slightly younger" in owners
    assert "1991 (Labour Force Survey, head of household)" in owners
    assert "same in both reports" not in owners
    assert "67% owned their home in 1991, 51% in 2008-09 and 48% in 2024-25" in owners
    rates = _text("".join(_quoted_block(facts, num, out["quoted_months"])))
    assert "was 5.97% in January 2008" in rates
    assert "the two are not joined" in rates
    assert "75% loan to value only" in rates


def test_quoted_rate_wording_comes_from_the_series_metadata(built):
    head, categories, span, notes = _series_metadata("boe-quoted-rates-notes")
    assert head["SCODE"] == "IUMBV34"
    assert head["DESC"] == (
        "Monthly interest rate of UK monetary financial institutions (excl. Central Bank) sterling "
        "2 year (75% LTV) fixed rate mortgage to households (in percent) not seasonally adjusted"
    )
    assert categories["OF SECTOR"] == "Households"
    assert categories["INSTRUMENT CURRENCY"] == "Sterling"
    assert categories["INSTRUMENTS"] == "Fixed rate mortgage, 2 year"
    assert categories["SEASONAL ADJUSTMENT"] == "Not seasonally adjusted"
    assert span[0] <= "2008-01-31"
    assert len(notes) == 2
    assert "methodology used to calculate these series has changed from January 2008" in notes[0]
    assert "applied historically, dating back to January 2005" in notes[0]
    assert "Changes to quoted household interest rates series" in notes[0]
    assert "methodology used to calculate these series has changed from January 2016" in notes[1]
    facts, out = built

    def num(fid, kind):
        return fmt(facts[fid].value, kind)

    rates = _text("".join(_quoted_block(facts, num, out["quoted_months"])))
    assert "two-year fixed-rate mortgage to households at 75% loan to value" in rates
    assert "excluding the Bank of England" in rates and "not seasonally adjusted" in rates
    assert "from January 2008, applying the change back to January 2005" in rates
    assert "changed it again from January 2016" in rates


def test_effective_rate_wording_comes_from_the_metadata_and_form_er(built):
    head, categories, span, notes = _series_metadata("boe-effective-rates-notes")
    assert head["SCODE"] == "CFMZ6JM"
    assert "sterling weighted average interest rate, loans secured on dwellings" in head["DESC"]
    assert "new advances to Individuals and individual trusts" in head["DESC"]
    assert categories["OF SECTOR"] == "Individuals and individual trusts"
    assert span[0] == "2016-01-31" and notes == []
    _, out = built
    assert out["rate_months"][0] == "2016-01"
    form = {p: _pdf_text("boe-form-er-definitions", p) for p in (1, 2, 3, 6, 17)}
    assert "aggregated as weighted averages to calculate effective interest rates" in form[1]
    assert (
        "new business covers all accounts opened for the first time during that reporting month "
        "and existing accounts where there has been an adjustment to the terms and conditions"
    ) in form[2]
    assert "automatically revert to a SVR once a fixation period has ended" in form[3]
    assert "should not be included in new business" in form[3]
    assert "including buy-to-let mortgages to individuals" in form[6]
    assert (
        "multiplying each new deposit (loan) by the (annualised) interest rate applicable on the "
        "transaction date, and dividing by the sum of new deposits (loans) during the month"
    ) in form[17]


def test_series_titles_csv_matches_the_xml_and_the_monthly_files():
    text = (ROOT / "data/fetched" / RECEIPTS["boe-rate-series-titles"]["file"]).read_text()
    titles_part, values_part = text.strip().split("\n\n")
    titles = {r["SERIES"]: r["DESCRIPTION"] for r in csv.DictReader(titles_part.splitlines())}
    assert titles["IUMBV34"] == _series_metadata("boe-quoted-rates-notes")[0]["DESC"]
    assert (
        titles["CFMZ6JM"].replace(" - ", ", ")
        == _series_metadata("boe-effective-rates-notes")[0]["DESC"]
    )
    values = {r["SERIES"]: r["VALUE"] for r in csv.DictReader(values_part.splitlines())}
    # Only January 2016 is kept from this request, so it adds no figures and cannot mix vintages.
    assert {r["DATE"] for r in csv.DictReader(values_part.splitlines())} == {"31 Jan 2016"}
    for series, source in (("IUMBV34", "boe-quoted-2yr-75ltv"), ("CFMZ6JM", "boe-mortgage-rates")):
        monthly = (ROOT / "data/fetched" / RECEIPTS[source]["file"]).read_text().splitlines()
        row = next(line for line in monthly if line.startswith("31 Jan 2016,"))
        assert row.split(",")[1] == values[series]


def test_rendered_rates_drop_unsupported_method_details(site_pages):
    page = site_pages["life/house-prices.html"]
    start = page.index("id='rates'") if "id='rates'" in page else page.index('id="rates"')
    # Month labels in the every-month tables are data, not method claims.
    rates = _text(re.sub(r"<table.*?</table>", " ", page[start:], flags=re.S))
    rates = rates[: rates.index("not joined to the quoted rate above") + 40]
    for claim in UNSUPPORTED_RATE_CLAIMS:
        assert claim not in rates, claim
    assert "include buy-to-let mortgages to individuals" in rates
    assert "changed or renegotiated in the month" in rates
    assert "start in January 2016" in rates


def test_rate_notes_and_probe_drop_unsupported_method_details(built):
    facts, out = built
    questions = json.loads((ROOT / "docs/johns-questions/questions.json").read_text())
    probe = next(p for q in questions["questions"] for p in q["probes"] if p["id"] == "J11.8")
    texts = [probe["why"], *probe["options"].values()]
    texts += [facts[f"rate.quoted.{m}"].note for m in out["quoted_months"]]
    texts += [facts[f"rate.new.{m}"].note for m in out["rate_months"]]
    for text in texts:
        for claim in UNSUPPORTED_RATE_CLAIMS:
            assert claim not in text, (claim, text)


def test_generations_page_defines_the_household_reference_person(site_pages):
    page = site_pages[pages_generations.PAGE]
    start = page.index("owning-at-30")
    section = _text(page[start : page.index("</div>", start)])
    assert "Not people aged exactly 30" in section
    assert "the person in whose name the home is owned or rented" in section
    assert "where two people share that, the one with the higher income" in section
