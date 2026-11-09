"""J5.2: defence in 2010-11 against 2025-26, read from the page's every-year table.

The headline sentence keeps the site's fixed ten-year window (2015-16 to 2025-26).
The 2010-11 comparison John asked about is answered from the annual PESA rows that
the same page already shows, and the checks below reopen those cells directly and
reconcile them with the OBR deflator and GDP rather than trusting the builder.
"""

import hashlib
import json
import re
import warnings

import openpyxl
import pytest

from builder import pages_defence
from builder.readers import ROOT
from builder.sources import SOURCES, all_sources

QUESTIONS = ROOT / "docs/johns-questions/questions.json"
PESA_SHEETS = {"cash": "4_2", "real": "4_3", "gdp": "4_4"}
ENDPOINTS = ("2010-11", "2025-26")
EXPECTED = {
    "2010-11": {"cash": 39.3, "real": 59.0, "gdp": 2.4},
    "2025-26": {"cash": 65.4, "real": 65.4, "gdp": 2.1},
}


def _probe(pid):
    data = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    return next(p for q in data["questions"] for p in q["probes"] if p["id"] == pid)


def _rows(path, sheet):
    wb = openpyxl.load_workbook(ROOT / path, data_only=True, read_only=True)
    try:
        return [list(r) for r in wb[sheet].iter_rows(values_only=True)]
    finally:
        wb.close()


@pytest.fixture(scope="module")
def pesa():
    """Defence cells for both endpoints, found by their own row label and year heading."""
    path = SOURCES["pesa4"]["file"]
    out = {}
    for view, sheet in PESA_SHEETS.items():
        rows = _rows(path, sheet)
        head = next(r for r in rows if "2010-11" in [str(v) for v in r])
        cols = {y: [str(v) for v in head].index(y) for y in ENDPOINTS}
        label = [r for r in rows if r[0] and str(r[0]).startswith("2. Defence")]
        assert len(label) == 1, sheet
        out[view] = {y: label[0][cols[y]] for y in ENDPOINTS}
        out[f"{view}.notes"] = " ".join(str(r[0]) for r in rows if r[0])
        # The publisher's own status line sits directly above the year headings.
        out[f"{view}.status"] = [v for v in rows[rows.index(head) - 1] if v]
    return out


@pytest.fixture(scope="module")
def obr():
    rows = _rows(SOURCES["obr-prices"]["file"], "Aggregates (£bn)")
    heads = [
        [str(v).strip() if v else "" for v in r]
        for r in rows
        if any(str(v).strip() == "GDP Deflator (2025-26=100)" for v in r if v)
    ]
    assert len(heads) == 1
    deflator = heads[0].index("GDP Deflator (2025-26=100)")
    gdp = heads[0].index("Nominal GDP (£ billion)")
    out = {}
    for y in ENDPOINTS:
        matches = [r for r in rows if len(r) > 1 and r[1] == y]
        assert len(matches) == 1, y
        out[y] = {"deflator": matches[0][deflator], "gdp": matches[0][gdp]}
    return out


@pytest.fixture(scope="module")
def built():
    from builder.data import build_all
    from builder.html import Num

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        facts, d = build_all()
    html = pages_defence.defence_page(facts, d, Num(facts), all_sources())
    return facts, d, html


def test_retained_originals_match_their_registered_hashes():
    for sid in ("pesa4", "obr-prices"):
        digest = hashlib.sha256((ROOT / SOURCES[sid]["file"]).read_bytes()).hexdigest()
        assert digest == SOURCES[sid]["sha256"], sid


def test_both_endpoints_are_published_cofog_cells(pesa):
    for view in PESA_SHEETS:
        for y in ENDPOINTS:
            assert pesa[view][y] == pytest.approx(EXPECTED[y][view]), (view, y)
    # COFOG defence, not NATO's wider definition that counts military pensions.
    for view in PESA_SHEETS:
        assert "UN COFOG definition of Defence spending" in pesa[f"{view}.notes"]
        assert "not comparable" in pesa[f"{view}.notes"]
        assert pesa[f"{view}.status"] == ["outturn"], view
    assert (
        "2025-26 price levels using GDP deflators from the Office for National Statistics "
        "(released 30 June 2026)" in pesa["real.notes"]
    )


def test_real_and_gdp_operands_reconcile_with_the_obr_deflator_and_gdp(pesa, obr):
    for y in ENDPOINTS:
        cash = pesa["cash"][y]
        real = cash * 100 / obr[y]["deflator"]
        share = 100 * cash / obr[y]["gdp"]
        # PESA rounds cash to £0.1bn and uses the ONS deflator and GDP of 30 June 2026,
        # so the OBR October vintage agrees only to within rounding.
        assert real == pytest.approx(pesa["real"][y], abs=0.1), y
        assert share == pytest.approx(pesa["gdp"][y], abs=0.05), y


def test_direction_is_higher_after_inflation_and_lower_as_a_share(pesa, obr):
    then, now = ENDPOINTS
    assert pesa["real"][now] > pesa["real"][then]
    assert pesa["gdp"][now] < pesa["gdp"][then]
    # The cash figure alone would also say "higher"; the share is the part that reverses.
    assert pesa["cash"][now] > pesa["cash"][then]
    unrounded_then = 100 * pesa["cash"][then] / obr[then]["gdp"]
    unrounded_now = 100 * pesa["cash"][now] / obr[now]["gdp"]
    assert unrounded_now < unrounded_then


def test_j5_2_is_answered_from_the_every_year_table():
    p = _probe("J5.2")
    assert "gap" not in p
    assert "decision" not in json.dumps(p).lower()
    answer = p["options"][p["answer"]].lower()
    assert "higher after inflation" in answer
    assert "lower share of gdp" in answer
    texts = {e["text"] for e in p["evidence"]}
    assert {e["page"] for e in p["evidence"]} == {"defence.html"}
    assert "2010-11 £39.3bn £59.0bn 2.4%" in texts
    assert "2025-26 £65.4bn £65.4bn 2.1%" in texts


def test_the_page_table_holds_both_endpoints_with_traceable_figures(built):
    facts, _, html = built
    for y in ENDPOINTS:
        for view in PESA_SHEETS:
            fid = f"spend.{view}.defence.{y}"
            assert f'data-fact="{fid}"' in html, fid
            assert facts[fid].source == "pesa4"
            assert facts[fid].locator.startswith(PESA_SHEETS[view] + "!")
    assert "Show defence spending every year" in html
    assert "using the GDP deflator from the Office for National Statistics (30 June 2026)" in html


def test_headline_words_follow_the_direction_of_the_change():
    assert pages_defence._moved(65.4, 36.6) == ("up from", "rise")
    assert pages_defence._moved(36.6, 65.4) == ("down from", "fall")
    assert pages_defence._moved(50.0, 50.0) == ("the same as", "change")


def test_headline_keeps_the_fixed_ten_year_window(built):
    _, d, html = built
    assert d["spending"]["latest"] == "2025-26"
    assert pages_defence.WINDOW_YEARS == 10
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
    assert re.search(
        r"Defence spending was £65\.4bn in 2025-26, up from £36\.6bn in 2015-16\.", text
    )
    assert re.search(r"After inflation the rise was 28\.7% ?, from £50\.8bn to £65\.4bn", text)
    assert "than in 2015-16" in text
    # No headline sentence is rebuilt around 2010-11; that year is read from the table.
    assert "than in 2010-11" not in text
    assert text.count("Defence spending was ") == 1
    assert "The two years are a fixed ten years apart, not chosen for the result." in text
    assert "The table below has every year from 2003-04 to 2025-26" in text
