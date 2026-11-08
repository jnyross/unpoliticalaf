"""Format and affected-source checks must run before receipt promotion."""

import shutil
import json
from pathlib import Path

import openpyxl
import pytest

from scripts.source_validation import validate_source

ROOT = Path(__file__).resolve().parents[1]
RECEIPTS = json.loads((ROOT / "data/fetched/receipts.json").read_text())


@pytest.mark.parametrize("source_id", sorted(RECEIPTS))
def test_retained_format_corpus(source_id):
    receipt = RECEIPTS[source_id]
    path = ROOT / "data/fetched" / receipt["file"]
    validate_source(source_id, path, receipt["content_type"], path)


@pytest.mark.parametrize(
    "name,source_id",
    [
        ("ons/l522.csv", "ons-l522"),
        ("dfe/spc-2015-national-tables.xlsx", "dfe-spc-2015-tables"),
        ("ehs/FT1421_Trends_in_overcrowding_by_tenure.ods", "ehs-ft1421"),
        ("dwp/spa-timetable.pdf", "dwp-spa-timetable"),
        ("gov/income-tax-rates.html", "gov-income-tax-rates"),
        ("nomis/ashe-sex-codes.json", "nomis-ashe-sex-codes"),
    ],
)
def test_retained_source_formats_and_affected_contracts(name, source_id):
    path = ROOT / "data/fetched" / name
    validate_source(source_id, path, "application/octet-stream", path)


@pytest.mark.parametrize(
    "suffix,body",
    [
        (".csv", b"<html><title>Access denied</title></html>"),
        (".csv", b"server failure"),
        (".csv", b""),
        (".csv", b'a,b\n"unterminated'),
        (".xlsx", b"PK-not-a-workbook"),
        (".ods", b"not a spreadsheet"),
        (".json", b'{"error":"service unavailable"}'),
        (".json", b"invalid"),
        (".pdf", b"%PDF-not-a-real-document"),
        (".html", b"<html><title>Access denied</title></html>"),
        (".bin", b"opaque download"),
    ],
)
def test_invalid_200_formats_are_rejected(tmp_path, suffix, body):
    staged = tmp_path / ("download" + suffix)
    staged.write_bytes(body)
    with pytest.raises(Exception):
        validate_source("test", staged, "application/octet-stream")


@pytest.mark.parametrize(
    "old,new",
    [
        ("L522", "OTHER"),
        ("2015=100", "2025=100"),
        ('"2026 APR","141.8"', '"2026 APR","NaN"'),
        ('"2026 APR","141.8"', '"2026 APR",""'),
        ('"2026 APR","141.8"', ""),
    ],
)
def test_l522_wrong_identity_base_missing_and_invalid_periods_fail(tmp_path, old, new):
    previous = ROOT / "data/fetched/ons/l522.csv"
    text = previous.read_text()
    assert old in text
    staged = tmp_path / "l522.csv"
    staged.write_text(text.replace(old, new))
    with pytest.raises(ValueError):
        validate_source("ons-l522", staged, "text/csv", previous)


def test_l522_compatible_numeric_revision_is_not_an_identity_change(tmp_path):
    previous = ROOT / "data/fetched/ons/l522.csv"
    staged = tmp_path / "l522.csv"
    staged.write_text(previous.read_text().replace('"2026 APR","141.8"', '"2026 APR","141.9"'))
    validate_source("ons-l522", staged, "text/csv", previous)


@pytest.mark.parametrize("mutation", ["sheet", "label", "number", "vintage"])
def test_school_workbook_contract_rejects_incompatible_valid_xlsx(tmp_path, mutation):
    previous = ROOT / "data/fetched/dfe/spc-2015-national-tables.xlsx"
    staged = tmp_path / "school.xlsx"
    workbook = openpyxl.load_workbook(previous)
    sheet = workbook["Table 6b"]
    if mutation == "sheet":
        sheet.title = "Wrong vintage"
    else:
        for row in sheet:
            for cell in row:
                if mutation == "label" and cell.value == "Average class size":
                    cell.value = "Different measure"
                elif mutation == "number" and isinstance(cell.value, float):
                    cell.value = None
                elif mutation == "vintage" and cell.value == 2015:
                    cell.value = 2026
    workbook.save(staged)
    workbook.close()
    with pytest.raises((ValueError, KeyError)):
        validate_source("dfe-spc-2015-tables", staged, "application/octet-stream", previous)


def test_overcrowding_wrong_sheet_is_rejected(tmp_path):
    import zipfile

    previous = ROOT / "data/fetched/ehs/FT1421_Trends_in_overcrowding_by_tenure.ods"
    staged = tmp_path / "overcrowding.ods"
    with zipfile.ZipFile(previous) as original, zipfile.ZipFile(staged, "w") as output:
        for name in original.namelist():
            body = original.read(name)
            if name == "content.xml":
                body = body.replace(b'table:name="FT1421"', b'table:name="Wrong sheet"')
            output.writestr(name, body)
    with pytest.raises(ValueError, match="FT1421"):
        validate_source("ehs-ft1421", staged, "application/octet-stream", previous)


def test_csv_schema_change_fails_but_compatible_value_update_passes(tmp_path):
    previous = tmp_path / "previous.csv"
    previous.write_text("period,value\n2025,1\n")
    staged = tmp_path / "staged.csv"
    staged.write_text("period,different_measure\n2025,2\n")
    with pytest.raises(ValueError, match="identity"):
        validate_source("test", staged, "text/csv", previous)
    shutil.copyfile(previous, staged)
    staged.write_text(staged.read_text().replace("2025,1", "2025,2"))
    validate_source("test", staged, "text/csv", previous)
