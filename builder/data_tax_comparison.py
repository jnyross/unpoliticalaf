"""One fixed, analytical employee illustration, not a payroll calculator.

Annual legal Income Tax allowances/bands and 52 equal weekly NI periods.
No intermediate penny rounding: the page labels this simplification explicitly.
Source parameters and each arithmetic step remain independently checkable facts.
"""

import html
import re

from .data import Fact
from .readers import ROOT, ods, ons_series

PREFIX = "tax.example."
ALLOWANCES = "data/fetched/gov/Table_a1_-_Income_Tax_-_personal_allowances_and_reliefs.ods"
RATES = "data/fetched/gov/Table_a2_-_Income_Tax_-_rates_and_allowances.ods"
HANSARD = "data/fetched/parl/hansard-national-insurance-1992-11-12.html"
CURRENT = "data/fetched/gov/rates-and-thresholds-for-employers-2025-to-2026.html"


def _text(path):
    raw = (ROOT / path).read_text(encoding="utf-8")
    raw = re.sub(r"<script.*?</script>|<style.*?</style>", "", raw, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw)))


def _html_number(path, anchor, position):
    text = _text(path)
    if text.count(anchor) != 1:
        raise ValueError(f"Rule anchor changed: {anchor}")
    tail = text.split(anchor, 1)[1]
    return float(re.findall(r"\d[\d,]*", tail)[position - 1].replace(",", ""))


def _weekly_ni(weekly, lower, upper, initial, main, excess=0):
    """Unrounded weekly primary contribution, including the old LEL discontinuity."""
    if weekly < lower:
        return 0
    return lower * initial + (min(weekly, upper) - lower) * main + max(0, weekly - upper) * excess


def _rules(facts):
    def published(key, value, source, locator, unit="£", scale=1):
        facts.add(
            Fact(
                PREFIX + key,
                value * scale,
                unit,
                "1992-93" if key.endswith("1992") else "2025-26",
                source,
                locator,
                scale=scale,
                note="Employee illustration rule; not an observed tax payment.",
            )
        )

    allowances = ods(ALLOWANCES)["TA1_IT_PA_and_Reliefs"]
    rates = ods(RATES)["TA2_Rates_of_IT"]
    if allowances[6][0] != "1992 to 1993" or rates[6][0] != "1992 to 1993":
        raise ValueError("Historical rule period changed")
    published(
        "pa.1992",
        float(str(allowances[6][1]).replace(",", "")),
        "hmrc-historic-allowances",
        "TA1_IT_PA_and_Reliefs!B7",
    )
    if rates[6][1] != "1 to 2,000":
        raise ValueError("Historical lower tax band changed")
    for key, col, position, expected in [
        ("lower_rate.1992", "C", 2, "20"),
        ("basic_rate.1992", "G", 6, "25"),
    ]:
        cell = rates[6][position]
        if str(cell).removesuffix(".0") != expected:
            raise ValueError(f"Historical tax band changed: {col}7")
        published(
            key, float(cell), "hmrc-historic-rates", f"TA2_Rates_of_IT!{col}7", "fraction", 0.01
        )
    if rates[6][5] != "2,001 to 23,700" or rates[6][7] != "Over 23,700" or float(rates[6][8]) != 40:
        raise ValueError("Historical upper tax bands changed")
    # A numeric endpoint retained in a textual band is exposed through the checker's
    # ODS 'number' locator, rather than pretending an assumption is a source.
    published("lower_band.1992", 2000, "hmrc-historic-rates", "TA2_Rates_of_IT!B7 number 2")
    if "My proposals will take effect from 6 April 1993" not in _text(HANSARD):
        raise ValueError("Hansard effective date changed")
    for key, anchor, pos, scale in [
        ("lel.1992", "These new earnings limits will replace the current ones of", 1, 1),
        ("uel.1992", "These new earnings limits will replace the current ones of", 2, 1),
        ("initial.1992", "will continue to pay an initial contribution of", 1, 0.01),
        ("main.1992", "of that limit and standard rate contributions of", 1, 0.01),
    ]:
        published(
            key,
            _html_number(HANSARD, anchor, pos),
            "hansard-ni-1992",
            f"after '{anchor}' number {pos}",
            "fraction" if scale != 1 else "£ a week",
            scale,
        )
    if "following figures apply from 6 April 2025 to 5 April 2026" not in _text(CURRENT):
        raise ValueError("Current rule period changed")
    for key, anchor, pos, scale in [
        (
            "pa.2025",
            "England and Northern Ireland The standard employee personal allowance for the 2025 to 2026 tax year is:",
            3,
            1,
        ),
        ("pt.2025", "Primary threshold", 1, 1),
        ("uel.2025", "Upper earnings limit", 1, 1),
        ("main.2025", "Balance of earnings above upper earnings limit A 0%", 1, 0.01),
        ("excess.2025", "Balance of earnings above upper earnings limit A 0%", 2, 0.01),
    ]:
        published(
            key,
            _html_number(CURRENT, anchor, pos),
            "gov-employer-rates-2025",
            f"after '{anchor}' number {pos}",
            "fraction" if scale != 1 else "£",
            scale,
        )
    published(
        "basic_rate.2025",
        20,
        "hmrc-historic-rates",
        "TA2_Rates_of_IT!G40 number 1",
        "fraction",
        0.01,
    )
    if rates[39][0] != "2025 to 2026" or rates[39][5] != "1 to 37,700":
        raise ValueError("Current Income Tax band changed")


def build(facts):
    _rules(facts)
    _, cpi = ons_series("data/fetched/ons/l522.csv")
    for year in (1992, 2025):
        fid = f"cpih.apr.{year}"
        if fid not in facts:
            facts.add(
                Fact(
                    fid,
                    cpi[f"{year} APR"],
                    "index (2015=100)",
                    f"April {year}",
                    "ons-l522",
                    f"L522 row '{year} APR'",
                )
            )

    def calculated(key, value, formula, inputs, unit="£"):
        facts.add(
            Fact(
                PREFIX + key,
                value,
                unit,
                (
                    "Hypothetical 1992-93"
                    if key.endswith("1992")
                    else (
                        "Hypothetical 2025-26"
                        if key.endswith("2025")
                        else "Both hypothetical tax years"
                    )
                ),
                "ons-l522" if key.startswith("gross.") else "hmrc-historic-rates",
                "",
                "calculated",
                note=(
                    "Stated assumption for the illustration, not an official or source value."
                    if not inputs
                    else "Fixed employee illustration; no intermediate payroll rounding."
                ),
                formula=formula,
                inputs=inputs,
            )
        )

    def get(key):
        return facts[PREFIX + key].value

    calculated("gross.1992", 15600, "15600", [])
    calculated("weeks", 52, "52", [], "weekly payments (assumption)")
    later = 15600 * cpi["2025 APR"] / cpi["1992 APR"]
    calculated(
        "gross.2025",
        later,
        "tax.example.gross.1992 × cpih.apr.2025 ÷ cpih.apr.1992",
        [PREFIX + "gross.1992", "cpih.apr.2025", "cpih.apr.1992"],
    )
    # Fixed example must stay in these bands. This is deliberately not a general tax calculator.
    if not (
        2000 < 15600 - get("pa.1992") < 23700
        and 0 < later - get("pa.2025") < 37700
        and get("lel.1992") < 300 < get("uel.1992")
        and get("pt.2025") < later / 52 < get("uel.2025")
    ):
        raise ValueError("Fixed example has left its declared tax/NI bands")
    for year in (1992, 2025):
        gross = get(f"gross.{year}")
        calculated(
            f"weekly.{year}",
            gross / 52,
            f"tax.example.gross.{year} ÷ tax.example.weeks",
            [PREFIX + f"gross.{year}", PREFIX + "weeks"],
            "£ a week",
        )
        taxable = gross - get(f"pa.{year}")
        calculated(
            f"taxable.{year}",
            taxable,
            f"tax.example.gross.{year} - tax.example.pa.{year}",
            [PREFIX + f"gross.{year}", PREFIX + f"pa.{year}"],
        )
        if year == 1992:
            income_tax = get("lower_band.1992") * get("lower_rate.1992") + (
                taxable - get("lower_band.1992")
            ) * get("basic_rate.1992")
            formula = "tax.example.lower_band.1992 × tax.example.lower_rate.1992 + (tax.example.taxable.1992 - tax.example.lower_band.1992) × tax.example.basic_rate.1992"
            inputs = ["lower_band.1992", "lower_rate.1992", "taxable.1992", "basic_rate.1992"]
            weekly_ni = _weekly_ni(
                gross / 52, get("lel.1992"), get("uel.1992"), get("initial.1992"), get("main.1992")
            )
            ni_formula = "(tax.example.lel.1992 × tax.example.initial.1992 + (tax.example.weekly.1992 - tax.example.lel.1992) × tax.example.main.1992) × tax.example.weeks"
            ni_inputs = ["lel.1992", "initial.1992", "weekly.1992", "main.1992", "weeks"]
        else:
            income_tax = taxable * get("basic_rate.2025")
            formula = "tax.example.taxable.2025 × tax.example.basic_rate.2025"
            inputs = ["taxable.2025", "basic_rate.2025"]
            weekly_ni = _weekly_ni(
                gross / 52, get("pt.2025"), get("uel.2025"), 0, get("main.2025"), get("excess.2025")
            )
            ni_formula = "(tax.example.weekly.2025 - tax.example.pt.2025) × tax.example.main.2025 × tax.example.weeks"
            ni_inputs = ["weekly.2025", "pt.2025", "main.2025", "weeks"]
        calculated(f"it.{year}", income_tax, formula, [PREFIX + i for i in inputs])
        calculated(f"ni.{year}", weekly_ni * 52, ni_formula, [PREFIX + i for i in ni_inputs])
        calculated(
            f"total.{year}",
            income_tax + weekly_ni * 52,
            f"tax.example.it.{year} + tax.example.ni.{year}",
            [PREFIX + f"it.{year}", PREFIX + f"ni.{year}"],
        )
        calculated(
            f"share.{year}",
            100 * (income_tax + weekly_ni * 52) / gross,
            f"100 × tax.example.total.{year} ÷ tax.example.gross.{year}",
            [PREFIX + f"total.{year}", PREFIX + f"gross.{year}"],
            "% of gross pay",
        )
