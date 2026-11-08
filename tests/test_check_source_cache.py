"""Reuse parsing, never producer values or results from an earlier check."""

import csv
import hashlib
from pathlib import Path

import pytest
import xlrd

from builder import check

ROOT = Path(__file__).resolve().parents[1]


def candidate(root, records):
    sources = {
        name: {"file": name, "sha256": hashlib.sha256((root / name).read_bytes()).hexdigest()}
        for name, _locator, _value in records
    }
    return {
        "sources": sources,
        "facts": [
            {
                "id": f"source.{index}",
                "source": name,
                "locator": locator,
                "value": value,
                "status": "published",
            }
            for index, (name, locator, value) in enumerate(records)
        ],
    }


def test_csv_parses_once_per_file_but_rechecks_each_fact_and_invocation(tmp_path, monkeypatch):
    monkeypatch.setattr(check, "ROOT", tmp_path)
    monkeypatch.setattr(check, "problems", [])
    records = [
        ("line.csv", "OBS_VALUE line 2", 2),
        ("line.csv", "OBS_VALUE line 3", 3),
        ("wide.csv", "CDID CODE row '2025'", 4),
        ("wide.csv", "CDID CODE row '2026'", 5),
        ("row.csv", "series row '2025'", 6),
        ("row.csv", "series row '2026'", 7),
    ]
    contents = {
        "line.csv": '\ufeffOBS_VALUE,note\n2,"two\nlines"\n3,other\n',
        "wide.csv": "CDID,CODE\n2025,4\n2026,5\n",
        "row.csv": "2025,6\n2026,7\n",
    }
    for name, text in contents.items():
        (tmp_path / name).write_text(text, encoding="utf-8")
    real_read_text = Path.read_text
    reads = []

    def read_text(path, *args, **kwargs):
        reads.append(path)
        return real_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)
    data = candidate(tmp_path, records)
    check.check_facts(data)
    assert check.problems == []
    assert sorted(reads) == sorted(tmp_path / name for name in contents)
    reads.clear()
    # Same relative source name in another root must not reuse earlier rows.
    other_root = tmp_path / "other"
    other_root.mkdir()
    (other_root / "row.csv").write_text("2025,8\n2026,9\n")
    monkeypatch.setattr(check, "ROOT", other_root)
    check.check_facts(candidate(other_root, [("row.csv", "series row '2025'", 8)]))
    assert check.problems == []
    # Replacing bytes between checks must be visible, even with the same root.
    (other_root / "row.csv").write_text("2025,10\n2026,11\n")
    check.check_facts(candidate(other_root, [("row.csv", "series row '2025'", 10)]))
    assert check.problems == []
    assert reads == [other_root / "row.csv", other_root / "row.csv"]
    # Direct callers without an invocation cache also remain fresh.
    assert check.cell_value("row.csv", "series row '2025'") == "10"
    (other_root / "row.csv").write_text("2025,12\n")
    assert check.cell_value("row.csv", "series row '2025'") == "12"


def test_csv_reuse_cannot_hide_hash_or_value_failures(tmp_path, monkeypatch):
    monkeypatch.setattr(check, "ROOT", tmp_path)
    monkeypatch.setattr(check, "problems", [])
    path = tmp_path / "row.csv"
    path.write_text("2025,2\n")
    data = candidate(tmp_path, [("row.csv", "series row '2025'", 2)] * 2)
    check.check_facts(data)
    assert check.problems == []
    path.write_text("2025,3\n")
    check.check_facts(data)
    assert check.problems == [
        "hash changed: row.csv",
        "source.0: source row.csv series row '2025' = '3', recorded 2",
        "source.1: source row.csv series row '2025' = '3', recorded 2",
    ]


def test_csv_cache_preserves_lazy_row_and_full_line_parsing(tmp_path, monkeypatch):
    monkeypatch.setattr(check, "ROOT", tmp_path)
    monkeypatch.setattr(check, "problems", [])
    path = tmp_path / "row.csv"
    path.write_text(f"2025,2\n2026,3\n2027,{'x' * (csv.field_size_limit() + 1)}\n")
    data = candidate(
        tmp_path,
        [("row.csv", "series row '2026'", 3), ("row.csv", "series row '2025'", 2)] * 2,
    )
    check.check_facts(data)
    assert check.problems == []
    # The line form must finish parsing even after a cached partial row lookup.
    with pytest.raises(csv.Error, match="field larger than field limit"):
        check.check_facts(
            candidate(
                tmp_path,
                [("row.csv", "series row '2026'", 3), ("row.csv", "series line 1", 2)],
            )
        )


def test_legacy_workbook_opens_once_per_check_without_reusing_verdicts(tmp_path, monkeypatch):
    name = "jobs.xls"
    path = tmp_path / name
    path.write_bytes((ROOT / "data/fetched/ons/jobs02.xls").read_bytes())
    book = xlrd.open_workbook(str(path))
    records = []
    for sheet in book.sheets():
        for row in range(sheet.nrows):
            for col in range(sheet.ncols):
                value = sheet.cell_value(row, col)
                if isinstance(value, (int, float)):
                    records.append(
                        (name, f"{sheet.name}!{xlrd.formula.colname(col)}{row + 1}", value)
                    )
                    if len(records) == 3:
                        break
            if len(records) == 3:
                break
        if len(records) == 3:
            break
    assert len(records) == 3
    monkeypatch.setattr(check, "ROOT", tmp_path)
    monkeypatch.setattr(check, "problems", [])
    real_open = xlrd.open_workbook
    opened = []

    def open_workbook(filename, *args, **kwargs):
        opened.append(filename)
        return real_open(filename, *args, **kwargs)

    monkeypatch.setattr(xlrd, "open_workbook", open_workbook)
    data = candidate(tmp_path, records)
    check.check_facts(data)
    assert check.problems == []
    assert opened == [str(path)]
    data["facts"][1]["value"] += 1
    check.check_facts(data)
    assert opened == [str(path), str(path)]
    assert len(check.problems) == 1
    assert check.problems[0].startswith("source.1: source jobs.xls")
