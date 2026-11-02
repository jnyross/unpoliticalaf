"""Income Tax and National Insurance rates read from the saved GOV.UK pages.

Used only for the clearly labelled worked example. The build fails if the
expected wording is not found, so a changed page cannot silently change it.
"""
import html
import re

from .readers import ROOT


def _text(path):
    t = (ROOT / path).read_text(encoding="utf-8")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return re.sub(r"\s+", " ", t)


def _money(s):
    return float(s.replace(",", ""))


def read_rates(sources, salary=30000):
    it = _text("data/fetched/gov/income-tax-rates.html")
    ni = _text("data/fetched/gov/national-insurance-rates.html")
    year = re.search(r"The current tax year is from 6 April (\d{4}) to 5 April (\d{4})", it)
    pa = re.search(r"Personal Allowance Up to £([\d,]+) 0%", it)
    basic = re.search(r"Basic rate £([\d,]+) to £([\d,]+) (\d+)%", it)
    nib = re.search(r"£([\d,.]+) to £([\d,.]+) \(£[\d,.]+ to £[\d,.]+ a month\) Over £([\d,.]+) a week .*? A 0% ([\d.]+)% ([\d.]+)%", ni)
    niyear = re.search(r"from 6 April (\d{4}) to 5 April (\d{4})", ni)
    if not (year and pa and basic and nib and niyear):
        raise SystemExit("GOV.UK rates pages changed: could not read Income Tax or National Insurance rates")
    if niyear.group(1) != year.group(1):
        raise SystemExit("Income Tax and National Insurance pages cover different tax years")
    allowance = _money(pa.group(1))
    basic_rate = float(basic.group(3)) / 100
    basic_top = _money(basic.group(2))
    ni_lower, ni_upper, ni_rate = _money(nib.group(2)), _money(nib.group(3)), float(nib.group(4)) / 100
    # nib.group(1) is the lower bound of the main band (e.g. 242.01); the threshold is that minus 1p.
    ni_lower = round(_money(nib.group(1)) - 0.01, 2)
    if not salary <= basic_top:
        raise SystemExit("illustration salary must stay inside the basic-rate band")
    income_tax = (salary - allowance) * basic_rate
    weekly = salary / 52
    ni_amount = max(0.0, min(weekly, ni_upper) - ni_lower) * ni_rate * 52
    total = income_tax + ni_amount
    return dict(
        year=f"{year.group(1)} to {year.group(2)}",
        basic=f"{basic.group(3)}%",
        allowance=f"£{allowance:,.0f}",
        retrieved=sources["gov-income-tax-rates"]["retrieved"],
        illustration=dict(salary=salary, allowance=int(allowance), income_tax=income_tax, ni_lower=f"{ni_lower:,.0f}",
                          ni_upper=f"{ni_upper:,.0f}", ni=ni_amount, ni_rate=ni_rate, basic_rate=basic_rate,
                          total=total, average_rate=100 * total / salary,
                          marginal=100 * (basic_rate + ni_rate)),
    )
