"""Independently reopen ONS age-30 period cells, not a cohort lifespan forecast."""

import hashlib
import json

import openpyxl
import pytest

from builder import data_generations as generations
from builder.check import as_number, cell_value
from builder.data import Facts
from builder.html import fmt
from builder.pages_life_expectancy import life_section
from builder.readers import ROOT
from builder.sources import all_sources


@pytest.mark.parametrize(
    "year,sex,cell,expected",
    [
        (1994, "male", "F37", 45.38),
        (1994, "female", "M37", 50.18),
        (2024, "male", "F37", 50.26),
        (2024, "female", "M37", 53.87),
    ],
)
def test_exact_age_thirty_period_cells(year, sex, cell, expected):
    facts = Facts()
    generations.build_life(facts)
    fact = facts[f"life.ex30.{sex}.{year}"]
    assert fact.value == expected
    assert fact.locator == f"{year}!{cell}"
    assert fact.period == f"{year} (period life table)"
    assert fact.unit == "remaining years at exact age 30"
    assert fact.status == "published"
    assert as_number(cell_value(generations.LIFE_FILE, fact.locator)) == expected


def test_source_identity_and_sex_age_boundaries():
    path = ROOT / generations.LIFE_FILE
    receipts = json.loads((ROOT / "data/fetched/receipts.json").read_text())
    assert (
        receipts[generations.LIFE_SOURCE]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    )
    # Identical to the original PR #225 retained bytes, independently fetched again.
    assert (
        hashlib.sha256(path.read_bytes()).hexdigest()
        == "34d2b0ee90ed78994e87d83a558caba977f0087a3ac306175c6a5cd24031730a"
    )
    wb = openpyxl.load_workbook(path, data_only=True)
    try:
        for year in (1994, 2024):
            sheet = wb[str(year)]
            assert "United Kingdom" in sheet["A1"].value
            assert str(year) in sheet["A1"].value
            assert (sheet["A5"].value, sheet["H5"].value) == ("Males", "Females")
            assert (sheet["F6"].value, sheet["M6"].value) == ("ex", "ex")
            assert [sheet[f"A{row}"].value for row in (36, 37, 38)] == [29, 30, 31]
            assert sheet["H37"].value == 30
        notes = " ".join(str(value) for row in wb["Notes"].values for value in row)
        assert "not accredited" in notes.lower()
    finally:
        wb.close()


@pytest.mark.parametrize(
    "cell,value",
    [
        ("F6", "mx"),
        ("H37", 31),
        ("F37", None),
        ("M37", ".."),
        ("A1", "England 1994"),
        ("A5", "Females"),
    ],
)
def test_changed_layout_age_geography_or_missing_value_fails_closed(
    tmp_path, monkeypatch, cell, value
):
    wb = openpyxl.load_workbook(ROOT / generations.LIFE_FILE)
    wb["1994"][cell] = value
    target = tmp_path / generations.LIFE_FILE
    target.parent.mkdir(parents=True)
    wb.save(target)
    wb.close()
    monkeypatch.setattr(generations, "ROOT", tmp_path)
    with pytest.raises(SystemExit, match="ONS life table"):
        generations.build_life(Facts())


def test_differences_and_static_table_caveat():
    facts = Facts()
    generations.build_life(facts)
    for sex, difference in (("male", 4.88), ("female", 3.69)):
        fact = facts[f"life.ex30.{sex}.change"]
        assert fact.value == pytest.approx(difference)
        assert fact.formula == f"life.ex30.{sex}.2024 - life.ex30.{sex}.1994"
        assert fact.inputs == [f"life.ex30.{sex}.2024", f"life.ex30.{sex}.1994"]
    page = life_section(lambda fid, kind: fmt(facts[fid].value, kind), all_sources())
    for text in (
        "50.3",
        "53.9",
        "45.4",
        "50.2",
        "4.9",
        "3.7",
        "1994",
        "2024",
        "UK",
        "not a forecast for a person",
        "not 2026",
        "not accredited official statistics",
        "adding 30",
        "<table",
    ):
        assert text in page
