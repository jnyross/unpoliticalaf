"""Regressions for issues revealed by exhaustive expanded scans."""

import re
from unittest.mock import patch

import pytest

from builder import html, pages_life


def test_scroll_shadows_preserve_muted_text_contrast():
    rule = re.search(r"(?:^|\n)\.tablewrap\{([^}]+)\}", html.CSS).group(1)
    opacity = max(float(value) for value in re.findall(r"rgba\(0,0,0,([.\d]+)\)", rule))
    muted = re.search(r"--muted:#([0-9a-f]{6})", html.CSS).group(1)

    def luminance(channels):
        linear = [
            value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
            for value in channels
        ]
        return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))

    foreground = luminance([int(muted[i : i + 2], 16) / 255 for i in (0, 2, 4)])
    # Both edge gradients may theoretically overlap on a very narrow region.
    background = luminance([(1 - opacity) ** 2] * 3)
    assert (background + 0.05) / (foreground + 0.05) >= 4.5


def test_missing_year_name_has_a_role_that_accepts_an_accessible_label():
    with patch.object(pages_life, "has_year_figure", return_value=False):
        markup = pages_life.year_finder(None, None, "housing")
    assert 'role="img" aria-label="2026: no figure"' in markup


def test_long_source_heading_can_wrap_unbroken_publisher_codes():
    heading_rule = re.search(r"(?:^|\n)h1\{([^}]+)\}", html.CSS).group(1)
    assert "overflow-wrap:anywhere" in heading_rule


def test_long_method_break_label_is_not_positioned_outside_the_chart():
    label = "Earnings counted as yearly pay from 1999"
    chart = html.line_chart(
        "Ratio",
        [str(year) for year in range(1997, 2026)],
        [("England", list(range(29)), "a")],
        "Times earnings",
        breaks=[(2, label)],
    )
    position = re.search(r'<text x="([\d.]+)" y="26" text-anchor="end"[^>]*>' + label, chart)
    assert position is not None
    assert float(position.group(1)) - len(label) * 8.4 >= 44


@pytest.mark.parametrize(
    ("values", "forecast_from"),
    [
        ([20_000, 30_000, 40_000, 50_000, 58_400], None),
        ([20_000, None, 40_000, 50_000, 58_400], None),
        ([20_000, 30_000, 40_000, 58_400, 59_000], 4),
    ],
)
def test_latest_value_clears_method_annotation_only_when_they_overlap(values, forecast_from):
    def chart(breaks):
        return html.line_chart(
            "Holidays",
            [str(year) for year in range(2020, 2025)],
            [("Visits", values, "a")],
            "Million visits",
            kind="millions",
            scale=1000,
            breaks=breaks,
            forecast_from=forecast_from,
        )

    def latest_baseline(markup):
        label = re.search(r'<text class="lbl"[^>]* y="([\d.]+)"[^>]*>58.4 million</text>', markup)
        assert label is not None
        return float(label.group(1))

    unannotated_baseline = latest_baseline(chart([]))
    assert unannotated_baseline == 26
    separate = chart([(1, "New method")])
    assert latest_baseline(separate) == unannotated_baseline
    overlapping = chart([(4, "New method")])
    annotation = re.search(r'<text[^>]* y="([\d.]+)"[^>]*>New method</text>', overlapping)
    assert annotation is not None
    assert latest_baseline(overlapping) >= float(annotation.group(1)) + 22
