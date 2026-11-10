"""Regressions for issues revealed by exhaustive expanded scans."""

import re
from unittest.mock import patch

from builder import html, pages_life


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
