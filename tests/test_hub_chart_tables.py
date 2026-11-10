"""The housing hub chart's published totals also have a semantic table alternative."""

import csv
import io
import re
from dataclasses import replace
from unittest.mock import patch

import pytest

from builder import downloads, pages_history
from builder.data import YEARS, Facts, history, housing
from builder.html import Num, fmt


@pytest.fixture(scope="module")
def facts():
    loaded = Facts()
    housing(loaded)
    history(loaded)
    return loaded


def housing_rows(facts):
    html = pages_history.table_for(facts, Num(facts), "housing")
    rows = re.findall(r"<tbody>(.*?)</tbody>", html, re.S)[0]
    return html, re.findall(r"<tr>(.*?)</tr>", rows, re.S)


def test_all_housing_rows_use_published_totals_and_preserve_components(facts):
    html, rows = housing_rows(facts)
    assert downloads.table_rows(html)[0] == [
        "Year and survey",
        "All owners",
        "Own outright",
        "Mortgage",
        "Social rent",
        "Private rent",
    ]
    periods = [
        (year, "house.lfs", f"{year} (Labour Force Survey)")
        for year in pages_history.ALL
        if f"house.lfs.private.{year}" in facts
        and facts[f"house.lfs.private.{year}"].value is not None
    ] + [
        (year, "house", f"{year}-{str(year + 1)[2:]} (English Housing Survey)")
        for year in YEARS
        if f"house.private.{year}" in facts and facts[f"house.private.{year}"].value is not None
    ]
    assert len(rows) == len(periods)
    for row, (year, prefix, label) in zip(rows, periods):
        assert downloads.table_rows(f"<tr>{row}</tr>")[0][0] == label
        fact_ids = [
            f"{prefix}.{key}.{year}"
            for key in ("owners", "outright", "mortgage", "social", "private")
        ]
        assert re.findall(r'data-fact="([^"]+)"', row) == fact_ids
        for fid in fact_ids:
            fact = facts[fid]
            assert fact.source == "ehs-ft1101"
            assert f'data-fact="{fid}" data-kind="pct">{fmt(fact.value, "pct")}</data>' in row
            assert f'value="{fact.value!r}"' in row
        assert facts[fact_ids[0]].status == "published"
        assert facts[fact_ids[0]].inputs == []
    # The overlapping 2008 observations remain separate rows, not spliced or summed.
    assert "2008 (Labour Force Survey)" in html
    assert "2008-09 (English Housing Survey)" in html
    assert "1982 (Labour Force Survey)" not in html


def test_each_housing_hub_chart_total_is_present_in_table(facts):
    html, _ = housing_rows(facts)
    for year in range(1981, 2025):
        fid = f"house.lfs.owners.{year}" if year < 2008 else f"house.owners.{year}"
        if fid in facts and facts[fid].value is not None:
            assert pages_history._owners(year) == fid
            assert f'data-fact="{fid}"' in html


@pytest.mark.parametrize("fid", ["house.lfs.owners.1981", "house.owners.2008"])
@pytest.mark.parametrize("missing", ["absent", "null"])
def test_missing_owner_total_is_not_invented_from_components(facts, fid, missing):
    changed = Facts(facts)
    if missing == "absent":
        del changed[fid]
    else:
        changed[fid] = replace(changed[fid], value=None)
    html, rows = housing_rows(changed)
    label = "1981 (Labour Force Survey)" if ".lfs." in fid else "2008-09 (English Housing Survey)"
    row = next(row for row in rows if label in row)
    assert downloads.table_rows(f"<tr>{row}</tr>")[0][1] == "no figure"
    assert f'data-fact="{fid}"' not in html
    assert len(re.findall(r"<td>", row)) == 5


def test_housing_table_csv_matches_every_displayed_cell(facts):
    html, _ = housing_rows(facts)
    with patch.object(downloads, "FILES", {}):
        linked = downloads.add_links(html, "life/housing.html")
        assert downloads.LINK_TEXT in linked
        assert len(downloads.FILES) == 1
        exported = next(iter(downloads.FILES.values()))
    rows = list(csv.reader(io.StringIO(exported.lstrip("\ufeff"))))
    assert rows == downloads.table_rows(html)
    assert rows[0][1] == "All owners"
