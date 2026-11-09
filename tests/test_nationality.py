"""NHS and adult social care nationality: exact cells, separate populations and honest denominators."""

import copy
import json
import re
from datetime import datetime

import pytest
from pypdf import PdfReader

from builder import data_nationality as nat
from builder.data import Facts
from builder.readers import ROOT

MANIFEST = json.loads((ROOT / "sources/manifest.json").read_text())
RECEIPTS = json.loads((ROOT / "data/fetched/receipts.json").read_text())
NEW_SOURCES = {
    "nhs-hchs-workforce-aug26",
    "sfc-asc-appendix-2026",
    "sfc-state-2026",
    "sfc-method-jun26",
    "nhs-hchs-dqa-aug26",
}
RECEIPTS_DIR = ROOT / "data/fetched"


@pytest.fixture(scope="module")
def nhs_rows():
    return nat.sheet_rows(nat.NHS_FILE, nat.NHS_SHEET, 8)


@pytest.fixture(scope="module")
def asc_rows():
    return nat.sheet_rows(nat.ASC_FILE, nat.ASC_SHEET, 10)


@pytest.fixture(scope="module")
def facts():
    built = Facts()
    nat.build(built)
    return built


def _pdf_text(name, page):
    reader = PdfReader(ROOT / "data/fetched" / RECEIPTS[name]["file"])
    return re.sub(r"\s+", " ", reader.pages[page - 1].extract_text())


def test_superseded_june_2025_entry_is_replaced_not_back_filled():
    ids = [s["id"] for s in MANIFEST["sources"]]
    assert "nhs-staff-nationality-jun25" not in ids
    assert "nhs-staff-nationality-jun25" not in RECEIPTS
    assert NEW_SOURCES <= set(ids)
    assert sorted(ids) == sorted(RECEIPTS)


@pytest.mark.parametrize(
    "fid,locator,value",
    [
        ("nhs.nat.hc.all.aug2026", "14!E233", 1535465),
        ("nhs.nat.hc.uk.aug2026", "14!E234", 1184447),
        ("nhs.nat.hc.eu.aug2026", "14!E240", 78817),
        ("nhs.nat.hc.eea.aug2026", "14!E268", 679),
        ("nhs.nat.hc.row.aug2026", "14!E273", 256138),
        ("nhs.nat.hc.unknown.aug2026", "14!E458", 15688),
        ("nhs.nat.fte.all.aug2026", "14!E7", 1370051.12012),
        ("nhs.nat.fte.uk.aug2026", "14!E8", 1038030.53555),
        ("nhs.nat.fte.unknown.aug2026", "14!E232", 13718.50997),
        ("asc.nat.posts.all.2025-26", "4.7!C30", 1590000),
        ("asc.nat.british.all.2025-26", "4.7!C31", 67),
        ("asc.nat.eu.all.2025-26", "4.7!C32", 6),
        ("asc.nat.noneu.all.2025-26", "4.7!C33", 27),
        ("asc.nat.nonbritish.all.2025-26", "4.7!C35", 33),
        ("asc.nat.nonbritish.ind.2025-26", "4.7!E35", 37),
    ],
)
def test_exact_published_cells(facts, fid, locator, value):
    assert facts[fid].locator == locator
    assert facts[fid].status == "published"
    assert facts[fid].value == pytest.approx(value, abs=1e-9)


def test_nhs_unknown_nationality_is_outside_both_parts_of_the_share(facts):
    share = facts["nhs.nat.hc.nonuk.share.aug2026"]
    assert facts["nhs.nat.hc.known.aug2026"].value == 1184447 + 78817 + 679 + 256138
    assert facts["nhs.nat.hc.nonuk.aug2026"].value == 78817 + 679 + 256138
    assert share.value == pytest.approx(100 * 335634 / 1520081)
    assert share.value != pytest.approx(100 * 335634 / 1535465)
    assert "unknown" not in share.formula and ".all." not in share.formula
    assert sorted(share.inputs) == sorted(
        f"nhs.nat.hc.{k}.aug2026" for k in ("uk", "eu", "eea", "row")
    )
    unknown = facts["nhs.nat.hc.unknown.share.aug2026"]
    assert unknown.value == pytest.approx(100 * 15688 / 1535465)


def test_nhs_headcount_and_fte_are_never_mixed(facts):
    for measure in ("hc", "fte"):
        for fid, fact in facts.items():
            if fid.startswith(f"nhs.nat.{measure}."):
                assert all(i.startswith(f"nhs.nat.{measure}.") for i in fact.inputs), fid
    assert facts["nhs.nat.fte.nonuk.share.aug2026"].value == pytest.approx(
        100 * (71869.91154 + 618.21447 + 245813.94859) / (1370051.12012 - 13718.50997), abs=0.01
    )


def test_adult_social_care_counts_posts_not_people(facts):
    assert facts["asc.nat.posts.all.2025-26"].unit == "filled posts"
    for fid, fact in facts.items():
        if fid.startswith("asc."):
            assert "people" not in fact.unit and "staff" not in fact.unit
            assert fact.period == "2025/26" and fact.source == "sfc-asc-appendix-2026"
        if fid.startswith("nhs."):
            assert fact.period == "31 August 2026" and fact.source == "nhs-hchs-workforce-aug26"


def _set(rows, ref_row, col, value):
    changed = copy.deepcopy(rows)
    changed[ref_row - 1][col] = value
    return changed


@pytest.mark.parametrize(
    "row,col,value,message",
    [
        (458, 2, "Not known", "missing group totals"),
        (233, 0, datetime(2026, 7, 31), "is not for"),
        (2, 0, "Staff in NHS trusts, core organisations and GP practices, England", "scope"),
        (240, 4, "*", "is not a count"),
        (1, 0, "Table 15: HCHS staff by gender", "title"),
    ],
)
def test_nhs_layout_changes_stop_the_build(nhs_rows, row, col, value, message):
    with pytest.raises(ValueError, match=message):
        nat.nhs_cells(_set(nhs_rows, row, col, value))


def test_nhs_repeated_group_total_stops_the_build(nhs_rows):
    with pytest.raises(ValueError, match="repeats"):
        nat.nhs_cells(nhs_rows + [copy.deepcopy(nhs_rows[457])])


@pytest.mark.parametrize(
    "row,col,value,message",
    [
        (33, 2, 0.4, "do not add up"),
        (35, 2, 0.5, "do not add up"),
        (35, 1, "Not British", "no Non-British row"),
        (27, 1, "Source: Skills for Care's workforce estimates, 2024/25", "period"),
        (29, 5, "Personal assistants", "no Direct payment recipients column"),
        (31, 2, 1.67, "not valid"),
    ],
)
def test_care_layout_changes_stop_the_build(asc_rows, row, col, value, message):
    with pytest.raises(ValueError, match=message):
        nat.asc_cells(_set(asc_rows, row, col, value))


def test_care_shares_agree_with_the_reports_own_counts(facts):
    text = _pdf_text("sfc-state-2026", 107)
    m = re.search(r"All job roles ([\d,]+) 67% ([\d,]+) 27% ([\d,]+) 6%", text)
    british, non_eu, eu = (int(g.replace(",", "")) for g in m.groups())
    total = british + non_eu + eu
    assert round(100 * british / total) == facts["asc.nat.british.all.2025-26"].value
    assert round(100 * non_eu / total) == facts["asc.nat.noneu.all.2025-26"].value
    assert round(100 * eu / total) == facts["asc.nat.eu.all.2025-26"].value
    assert round(100 * (non_eu + eu) / total) == facts["asc.nat.nonbritish.all.2025-26"].value


@pytest.mark.parametrize(
    "source,page,phrase",
    [
        (
            "sfc-method-jun26",
            9,
            "A person may have more than one job (post), therefore the number of filled posts can be higher than the number of people working in the sector.",
        ),
        ("sfc-method-jun26", 46, "Unknown values are left as null."),
        (
            "sfc-method-jun26",
            56,
            "for the independent sector, we exclude missing and erroneous data at the point of analysis.",
        ),
        (
            "sfc-state-2026",
            9,
            "In 2023, Skills for Care was added to the Official Statistics Order and became an official statistics producer.",
        ),
        (
            "sfc-state-2026",
            9,
            "In February 2025, our report ‘The workforce employed by adult social services departments in England’ was badged as an accredited official statistic",
        ),
        (
            "sfc-state-2026",
            12,
            "Since 2024/25, we have not included adult social care related roles employed in the NHS",
        ),
    ],
)
def test_page_method_statements_are_in_the_retained_publications(source, page, phrase):
    assert phrase in _pdf_text(source, page)


def test_nhs_notes_back_the_page_method_statements():
    rows = nat.sheet_rows(nat.NHS_FILE, "Notes and definitions", 3)
    notes = {int(r[0]): r[2] for r in rows if str(r[0]).isdigit()}
    assert notes[11].startswith("Nationality is a self-reported value")
    assert "staff working in more than one role" in notes[1]
    assert "directly employed in NHS trusts and other core organisations" in notes[3]
    title = nat.sheet_rows(nat.NHS_FILE, "Title sheet", 1)
    assert ["Publication date: 29 October 2026"] in title
    assert ["Published by NHS England part of the Government Statistical Service"] in title


@pytest.mark.parametrize(
    "phrase",
    [
        "these have been included in GP workforce statistics rather than Hospital and Community Health Services (HCHS) workforce statistics",
        "these Primary Care staff to be identified within our data routines and excluded from HCHS secondary care publications",
    ],
)
def test_primary_care_exclusion_is_in_the_retained_annex(phrase):
    rows = nat.sheet_rows(
        RECEIPTS_DIR / RECEIPTS["nhs-hchs-dqa-aug26"]["file"], "DQ Annex - Core NHS", 8
    )
    assert any(isinstance(c, str) and phrase in c for r in rows for c in r)


def _immigration_section():
    from builder import data_mye
    from builder.html import Num
    from builder.pages_immigration import immigration_page
    from builder.sources import all_sources

    built = Facts()
    data_mye.build(built)
    nat.build(built)
    html = immigration_page(built, {}, Num(built), all_sources())
    html = html if isinstance(html, str) else html[0]
    start = html.index("<h2>What share of NHS and adult social care staff")
    end = html.index("<h2>", start + 4)
    section = html[start:end]
    return section, re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", section))


def test_immigration_page_keeps_sectors_dates_and_units_apart():
    section, text = _immigration_section()
    for fid in (
        "nhs.nat.hc.nonuk.share.aug2026",
        "nhs.nat.hc.unknown.aug2026",
        "nhs.nat.fte.nonuk.share.aug2026",
        "asc.nat.nonbritish.all.2025-26",
        "asc.nat.posts.all.2025-26",
    ):
        assert f'data-fact="{fid}"' in section
    for phrase in (
        "31 August 2026",
        "2025/26",
        "filled posts, not people",
        "NHS trusts and other core organisations",
        "left out of the share",
        "Nationality is not the same as country of birth",
        "do not show whether or when anyone moved to the UK",
        "cannot be added together",
        "official statistics producer",
        "accredited",
    ):
        assert phrase in text, phrase
    for word in ("citizen", "migrant", "born abroad", "foreign-born"):
        assert word not in text.lower(), word


def test_j2_5_is_answered_from_the_page():
    pack = json.loads((ROOT / "docs/johns-questions/questions.json").read_text())
    probe = next(p for q in pack["questions"] for p in q["probes"] if p["id"] == "J2.5")
    assert "gap" not in probe and probe["answer"] in probe["options"]
    assert {e["page"] for e in probe["evidence"]} == {"immigration.html"}
