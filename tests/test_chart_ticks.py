"""Long annual axes retain readable, evenly spaced round-year ticks."""

import re

import pytest

from builder.html import line_chart


@pytest.mark.parametrize("first,last", [(1971, 2026), (1971, 2025), (1992, 2026)])
def test_long_annual_axis_uses_round_years_without_an_oversized_final_gap(first, last):
    years = list(range(first, last + 1))
    chart = line_chart("History", list(map(str, years)), [("Value", years, "a")], "units")
    ticks = [
        int(year)
        for year in re.findall(r'<text x="[\d.]+" y="210" text-anchor="\w+">(\d{4})</text>', chart)
    ]
    assert ticks[0] - first <= 10 and last - ticks[-1] <= 10
    assert all(year % 10 == 0 for year in ticks[1:-1])
    gaps = [right - left for left, right in zip(ticks, ticks[1:])]
    assert max(gaps) <= 15
    assert gaps[-1] <= max(gaps[:-1])
