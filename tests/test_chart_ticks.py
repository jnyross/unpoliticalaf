"""Readable annual ticks and endpoint names that identify the correct lines."""

import re

import pytest

from builder.html import _end_labels, line_chart


def test_endpoint_names_keep_the_vertical_order_of_their_lines():
    # A falling upper series and rising lower series used to swap names when
    # their preferred above/below positions crossed, even with distinct ends.
    labels = _end_labels(
        [("Men", [78.2, 78.0], "a"), ("Women", [72.0, 72.3], "b")],
        lambda index: 392,
        lambda value: 366.4 - value * 3.526,
        14,
        190,
    )
    positions = {
        name: float(position)
        for position, name in re.findall(
            r'y="([\d.]+)" text-anchor="end">(\w+)</text>', "".join(labels)
        )
    }
    assert positions["Men"] < positions["Women"]
    assert positions["Women"] - positions["Men"] >= 17
    assert abs(positions["Men"] - (366.4 - 78.0 * 3.526)) <= 7
    assert abs(positions["Women"] - (366.4 - 72.3 * 3.526)) <= 7


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
