"""Pay around the age of 30 since 2002 and job security at 25 to 34 since 1992 (J12.7, J12.12):
exact ASHE Table 6 and RED02 cells, the 30 to 39 age band, no change across an ASHE method
break, and no measure relabelled as job security."""

import html
import json
import re

import pytest

from builder import data_age_pay as age
from builder import pages_generations, uncertainty
from builder.build import render
from builder.check import as_number, cell_value
from builder.data import Facts
from builder.data_life_extra import SPREAD_BREAKS
from builder.html import fmt
from builder.readers import ROOT

RECEIPTS = json.loads((ROOT / "data/fetched/receipts.json").read_text())
MANIFEST = {s["id"]: s for s in json.loads((ROOT / "sources/manifest.json").read_text())["sources"]}
QUESTIONS = json.loads((ROOT / "docs/johns-questions/questions.json").read_text())
NEW_SOURCES = {sid for sid, _, _, _ in age.TABLE6.values()} | {"ons-red02", "ons-emp07"}
# Median gross weekly pay, full-time employee jobs aged 30 to 39, as printed in each edition.
PUBLISHED = {
    2002: (425.8, "D9"),
    2006: (496.1, "D10"),
    2010: (547.8, "D10"),
    2011: (550.4, "D10"),
    2020: (625.1, "D10"),
    2021: (646.4, "D10"),
    2025: (807.2, "D10"),
}
# Statements that would turn a nearby measure into a job security verdict.
SECURITY_CLAIMS = (
    "job security rose",
    "job security fell",
    "job security has risen",
    "job security has fallen",
    "more secure than",
    "less secure than",
    "redundancy rate in 1992",
    "temporary employees aged 25 to 34",
)


@pytest.fixture(scope="module")
def built():
    facts = Facts()
    age.build_pay(facts)
    age.build_redundancy(facts)
    return facts


@pytest.fixture(scope="module")
def site_pages():
    # render() refills the shared margin table from its own facts; later tests rely on its
    # earlier state, so put it back.
    saved = dict(uncertainty.MARGINS)
    try:
        _, _, pages, _ = render()
    finally:
        uncertainty.MARGINS.clear()
        uncertainty.MARGINS.update(saved)
    return pages


def _text(page):
    """Visible text as scripts/user_test.page_text sees it, which is what probe evidence must match."""
    page = re.sub(r"<(script|style)\b[\s\S]*?</\1>", " ", page)
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", page)))
    return re.sub(r" ([,.;:)])", r"\1", re.sub(r"\( ", "(", text))


def _section(page, start_id, end_id):
    start = re.search(rf"id=['\"]{start_id}['\"]", page).start()
    end = re.search(rf"id=['\"]{end_id}['\"]", page[start:]).start() + start
    return _text(page[start:end])


def _probe(pid):
    return next(p for q in QUESTIONS["questions"] for p in q["probes"] if p["id"] == pid)


def test_new_sources_are_retained_with_receipts():
    for sid in NEW_SOURCES:
        assert MANIFEST[sid]["file"] == RECEIPTS[sid]["file"]
        retained = ROOT / "data/fetched" / RECEIPTS[sid]["file"]
        assert retained.stat().st_size == RECEIPTS[sid]["bytes"]


@pytest.mark.parametrize("year", sorted(PUBLISHED))
def test_pay_cells_reread_independently(built, year):
    value, ref = PUBLISHED[year]
    sid, path, member, _ = age.TABLE6[year]
    f = built[age.pay_fid(year)]
    assert (f.source, f.locator, f.status, f.period) == (
        sid,
        f"{member}::Full-Time!{ref}",
        "published",
        f"April {year}",
    )
    assert f.value == pytest.approx(value)
    assert as_number(cell_value(path, f.locator)) == pytest.approx(value)
    # The row is the 30 to 39 band, not a single year of age, and the column is the median.
    assert str(cell_value(path, f"{member}::Full-Time!A{ref[1:]}")).strip() == "30-39"
    assert cell_value(path, f"{member}::Full-Time!D5") == "Median"
    assert "aged exactly 30" in f.note and "30 to 39" in f.note


def test_real_pay_uses_april_cpih(built):
    base = built["cpih.apr.2025"].value
    for y in PUBLISHED:
        real = built[age.real_fid(y)]
        assert real.status == "calculated"
        expected = built[age.pay_fid(y)].value * base / built[f"cpih.apr.{y}"].value
        assert real.value == pytest.approx(expected)


def test_changes_stay_within_one_ashe_basis(built):
    for a, b in age.RUNS:
        assert age.TABLE6[a][3] == age.TABLE6[b][3]
        assert not [y for y in SPREAD_BREAKS if a < y <= b], (a, b)
        expected = 100 * built[age.real_fid(b)].value / built[age.real_fid(a)].value - 100
        assert built[age.change_fid(a, b)].value == pytest.approx(expected)
    changes = [fid for fid in built if ".real_change." in fid]
    assert sorted(changes) == sorted(age.change_fid(a, b) for a, b in age.RUNS)
    assert age.change_fid(2002, 2025) not in built


def test_a_change_across_a_break_is_refused(monkeypatch):
    monkeypatch.setattr(age, "RUNS", [(2002, 2025)])
    with pytest.raises(ValueError, match="not on the same ASHE basis"):
        age.build_pay(Facts())


def test_a_changed_table6_title_stops_the_build(monkeypatch):
    real = age._sheet_cells
    title = "Table 6.1a Weekly pay - Gross (£) - For all employee jobsa: United Kingdom, 2002"

    def wrong(path, member, sheet):
        get = real(path, member, sheet)
        return lambda col, row: title if (col, row) == ("A", 1) else get(col, row)

    monkeypatch.setattr(age, "_sheet_cells", wrong)
    with pytest.raises(ValueError, match="not UK full-time"):
        age.table6_cell(2002)


def test_redundancy_rate_is_ages_25_to_34_in_april_to_june_2025(built):
    f = built["redund.age.25_34.2025"]
    assert (f.source, f.period, f.unit, f.status) == (
        "ons-red02",
        "April to June 2025",
        "per 1,000 employees",
        "published",
    )
    path = "data/fetched/" + RECEIPTS["ons-red02"]["file"]
    row = re.fullmatch(r"Age - rates!D(\d+)", f.locator).group(1)
    assert as_number(cell_value(path, f.locator)) == pytest.approx(f.value)
    assert cell_value(path, f"Age - rates!A{row}") == "Apr-Jun 2025"
    assert cell_value(path, "Age - rates!D5") == "25-34"
    assert cell_value(path, "Age - rates!A9") == age.RED02_FIRST == "Jan-Mar 2009"
    assert "official statistics in development" in f.note.lower()


def test_a_redundancy_table_with_a_new_column_order_stops_the_build(monkeypatch):
    real = age._red02_rows

    def moved(sheet):
        rows = [list(r) for r in real(sheet)]
        if sheet == age.RED02_SHEET:
            rows[4][3] = "35-49"
        return rows

    monkeypatch.setattr(age, "_red02_rows", moved)
    with pytest.raises(ValueError, match="not ages 25 to 34"):
        age.build_redundancy(Facts())


def test_temporary_employees_table_has_no_age_split():
    age.check_temporary_table()


def test_a_change_across_a_break_with_matching_labels_is_refused(monkeypatch):
    # Even if the basis labels were edited to match, the 2011 recoding still separates the pair.
    table = dict(age.TABLE6)
    table[2011] = table[2011][:3] + (table[2010][3],)
    monkeypatch.setattr(age, "TABLE6", table)
    monkeypatch.setattr(age, "RUNS", [(2010, 2011)])
    with pytest.raises(ValueError, match="not on the same ASHE basis"):
        age.build_pay(Facts())


@pytest.mark.parametrize(
    "cell",
    [("D", 10, "..", "not a number"), ("A", 15, f"a  {age.COVERAGE_NOTE}.", "coverage note")],
)
def test_a_suppressed_median_or_lost_furlough_note_stops_the_build(monkeypatch, cell):
    real = age._sheet_cells
    col, row, replacement, message = cell

    def changed(path, member, sheet):
        get = real(path, member, sheet)
        return lambda c, r: replacement if (c, r) == (col, row) else get(c, r)

    monkeypatch.setattr(age, "_sheet_cells", changed)
    with pytest.raises(ValueError, match=message):
        age.table6_cell(2020)


def test_a_redundancy_table_without_the_2025_quarter_stops_the_build(monkeypatch):
    real = age._red02_rows

    def dropped(sheet):
        rows = real(sheet)
        return [r for r in rows if r[0] != age.RED02_QUARTER] if sheet == age.RED02_SHEET else rows

    monkeypatch.setattr(age, "_red02_rows", dropped)
    with pytest.raises(ValueError, match="no single Apr-Jun 2025 row"):
        age.build_redundancy(Facts())


def test_a_temporary_employees_table_with_an_age_split_stops_the_build(monkeypatch):
    real_open = age.xlrd.open_workbook

    class AgedSheet:
        def __init__(self, sheet):
            self._sheet, self.ncols = sheet, sheet.ncols

        def cell_value(self, r, c):
            return "Aged 25 to 34" if (r, c) == (5, 1) else self._sheet.cell_value(r, c)

    class AgedBook:
        def __init__(self, book):
            self._book = book

        def sheet_names(self):
            return self._book.sheet_names()

        def sheet_by_name(self, name):
            sheet = self._book.sheet_by_name(name)
            return AgedSheet(sheet) if name == "People" else sheet

    monkeypatch.setattr(age.xlrd, "open_workbook", lambda *a, **k: AgedBook(real_open(*a, **k)))
    with pytest.raises(ValueError, match="age split"):
        age.check_temporary_table()


def test_pay_section_states_the_age_band_and_breaks(site_pages, built):
    page = site_pages[pages_generations.PAGE]
    section = _section(page, "pay-at-30", "housing-cost")
    assert "full-time employees aged 30 to 39, not people aged exactly 30" in section
    assert "Not people aged exactly 30." in section
    assert "No change from 2002 to 2025 is worked out." in section
    assert "2004, 2006 and 2011" in section and "job coding changed again in 2021" in section
    assert "cover ages 16 to 25" in section
    # The spliced 2002 to 2025 change after inflation must not appear anywhere on the page.
    spliced = 100 * built[age.real_fid(2025)].value / built[age.real_fid(2002)].value - 100
    assert fmt(spliced, "pct") not in _text(page)
    stripped = section.replace("aged exactly 30", "")
    assert not re.search(r"(people|employees) aged 30(?! to 39)", stripped)


def test_job_security_section_does_not_relabel_other_measures(site_pages):
    page = site_pages[pages_generations.PAGE]
    section = _section(page, "job-security", "pay-at-30")
    assert (
        "The site has no measure of job security for people aged 25 to 34 going back to 1992."
        in section
    )
    assert "Neither is job security on its own" in section
    assert "not how secure that work is" in section
    assert "start in January to March 2009, so there is no 1992 figure" in section
    assert "not by age, so it cannot show temporary work at 25 to 34" in section
    assert "official statistics in development" in section
    assert "step change" in section
    for claim in SECURITY_CLAIMS:
        assert claim not in section.lower(), claim


def test_short_answer_states_the_age_band_and_limits(site_pages):
    page = site_pages[pages_generations.PAGE]
    answer = _text(re.search(r'<div class="answer"[^>]*>.*?</div>', page, re.S).group(0))
    assert "Pay is published for ages 30 to 39, not for people aged exactly 30" in answer
    assert "no single change is worked out" in answer
    assert "No official measure of job security at 25 to 34 goes back to 1992." in answer


def test_cannot_yet_list_drops_pay_and_job_security(site_pages):
    page = site_pages[pages_generations.PAGE]
    section = _section(page, "cannot-yet", "about")
    assert "Pay at a given age" not in section
    assert "Job security" not in section


@pytest.mark.parametrize("pid", ["J12.7", "J12.12"])
def test_probes_are_closed_with_page_evidence(site_pages, pid):
    probe = _probe(pid)
    assert "gap" not in probe
    assert probe["answer"] in probe["options"]
    text = _text(site_pages[pages_generations.PAGE])
    for ev in probe["evidence"]:
        assert ev["page"] == pages_generations.PAGE
        assert ev["text"] in text, ev["text"]


def test_probe_answers_keep_the_age_band_and_scope():
    pay = _probe("J12.7")
    right = pay["options"][pay["answer"]]
    assert "30 to 39" in right and "no single" in right.lower()
    security = _probe("J12.12")
    right = security["options"][security["answer"]]
    assert "no measure of job security" in right.lower() and "2009" in right
    for claim in SECURITY_CLAIMS:
        assert claim not in right.lower()
