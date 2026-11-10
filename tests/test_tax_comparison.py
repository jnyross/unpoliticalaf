"""Fixed historical illustration: retained rules, independent arithmetic and boundaries."""

import pytest
import copy
import html
import re

from builder import data_tax_comparison as tax
from builder.pages_tax_comparison import comparison_page
from builder.html import Num
from builder.check import as_number, cell_value
from builder.data import Facts
from builder.sources import all_sources


def test_retained_period_rules_and_independent_stepwise_calculation():
    facts = Facts()
    tax.build(facts)
    sources = all_sources()
    for fact in facts.values():
        if fact.status == "published":
            actual = as_number(cell_value(sources[fact.source]["file"], fact.locator))
            assert actual * fact.scale == pytest.approx(fact.value)
    assert facts["tax.example.pa.1992"].value == 3445
    assert facts["tax.example.lel.1992"].value == 54
    assert facts["tax.example.uel.1992"].value == 405
    assert facts["tax.example.pt.2025"].value == 242
    assert facts["tax.example.uel.2025"].value == 967
    # Independent arithmetic, deliberately not using the producer's fiscal helpers.
    later_gross = 15600 * 137.7 / 61.8
    earlier_tax = 2000 * 0.20 + (15600 - 3445 - 2000) * 0.25
    earlier_ni = (54 * 0.02 + (300 - 54) * 0.09) * 52
    later_tax = (later_gross - 12570) * 0.20
    later_ni = (later_gross / 52 - 242) * 0.08 * 52
    for year, gross, income_tax, ni in [
        (1992, 15600, earlier_tax, earlier_ni),
        (2025, later_gross, later_tax, later_ni),
    ]:
        assert facts[f"tax.example.gross.{year}"].value == pytest.approx(gross)
        assert facts[f"tax.example.it.{year}"].value == pytest.approx(income_tax)
        assert facts[f"tax.example.ni.{year}"].value == pytest.approx(ni)
        assert facts[f"tax.example.share.{year}"].value == pytest.approx(
            100 * (income_tax + ni) / gross
        )
    assert facts["tax.example.share.2025"].value < facts["tax.example.share.1992"].value
    for key in ["gross.1992", "weeks"]:
        assert "Stated assumption" in facts[tax.PREFIX + key].note
        assert facts[tax.PREFIX + key].inputs == []
    assert facts["tax.example.it.1992"].period == "Hypothetical 1992-93"


@pytest.mark.parametrize(
    "weekly,expected",
    [(53.99, 0), (54, 1.08), (54.01, 1.0809), (300, 23.22), (405, 32.67), (406, 32.67)],
)
def test_historical_ni_initial_charge_and_cap(weekly, expected):
    assert tax._weekly_ni(weekly, 54, 405, 0.02, 0.09) == pytest.approx(expected)


@pytest.mark.parametrize(
    "weekly,expected", [(125, 0), (242, 0), (242.01, 0.0008), (967, 58), (968, 58.02)]
)
def test_current_ni_weekly_not_annual_thresholds(weekly, expected):
    assert tax._weekly_ni(weekly, 242, 967, 0, 0.08, 0.02) == pytest.approx(expected)


def test_pay_frequency_and_rounding_are_not_silently_changed():
    gross = 15600 * 137.7 / 61.8
    weekly_total = tax._weekly_ni(gross / 52, 242, 967, 0, 0.08, 0.02) * 52
    assert weekly_total != pytest.approx((gross - 12570) * 0.08)
    assert weekly_total != round(weekly_total / 52, 2) * 52


def test_illustration_has_limits_traces_and_downloads_without_javascript():
    facts = Facts()
    tax.build(facts)
    page = comparison_page(Num(facts), all_sources())
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", page)))
    for expected in [
        "One hypothetical employee, not an observed average",
        "26.6%",
        "17.9%",
        "52 equal weekly payments",
        "fractional pennies",
        "category A",
        "single",
        "not annual or monthly limits",
        "Excluded: employer NI",
        "not a tax-year average",
        "not observed household tax incidence",
        "Download this data (CSV)",
    ]:
        assert expected in text
    assert 'data-fact="tax.example.share.1992"' in page
    assert 'data-fact="tax.example.share.2025"' in page
    assert "<form" not in page


@pytest.mark.parametrize(
    "field,replacement", [(0, "1993 to 1994"), (1, "1 to 2,500"), (5, "2,001 to 24,000")]
)
def test_changed_historical_period_or_band_fails_closed(monkeypatch, field, replacement):
    original = tax.ods

    def changed(path):
        book = copy.deepcopy(original(path))
        if path == tax.RATES:
            book["TA2_Rates_of_IT"][6][field] = replacement
        return book

    monkeypatch.setattr(tax, "ods", changed)
    with pytest.raises(ValueError):
        tax.build(Facts())


def test_income_outside_fixed_bands_is_rejected(monkeypatch):
    original = tax.ons_series

    def changed(path):
        meta, values = original(path)
        values = dict(values)
        values["2025 APR"] = 1000
        return meta, values

    monkeypatch.setattr(tax, "ons_series", changed)
    with pytest.raises(ValueError, match="left its declared"):
        tax.build(Facts())


@pytest.mark.parametrize(
    "old,new",
    [
        (
            "My proposals will take effect from 6 April 1993",
            "My proposals will take effect from 6 April 1992",
        ),
        ("These new earnings limits will replace the current ones of", "These limits supersede"),
    ],
)
def test_hansard_date_or_current_limit_locator_change_fails_closed(monkeypatch, old, new):
    original = tax._text
    monkeypatch.setattr(tax, "_text", lambda path: original(path).replace(old, new))
    with pytest.raises(ValueError):
        tax.build(Facts())
