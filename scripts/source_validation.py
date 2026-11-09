"""Download format checks and narrow contracts for refreshed sources.

These checks are not a substitute for the independent retained-source checker
or review of a new vintage. They deliberately reject unsupported formats rather
than bless opaque bytes. No semantic-validator registry is introduced.
"""

import csv
import io
import json
import math
import re
import xml.etree.ElementTree as ET
import zipfile

import openpyxl
import xlrd
from pypdf import PdfReader

ERROR_PAGE = re.compile(
    r"access denied|captcha|service unavailable|page not found|just a moment", re.I
)
TABLE_NS = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
TEXT_NS = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
OFFICE_NS = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
GESMES_NS = "http://www.gesmes.org/xml/2002-08-01"


def csv_records(path):
    return list(csv.reader(io.StringIO(path.read_text(encoding="utf-8-sig")), strict=True))


def validate_l522(rows, previous):
    metadata = {row[0]: row[1] for row in rows if len(row) == 2}
    required = {
        "Title": "CPIH INDEX 00: ALL ITEMS 2015=100",
        "CDID": "L522",
        "Source dataset ID": "MM23",
        "Unit": "Index, base year = 100",
    }
    if any(metadata.get(key) != value for key, value in required.items()):
        raise ValueError("L522 identity/base/unit changed")
    periods = {}
    for row in rows:
        if row and re.fullmatch(r"\d{4}( Q[1-4]| [A-Z]{3})?", row[0]):
            if len(row) != 2 or row[0] in periods:
                raise ValueError("invalid or duplicate L522 observation")
            value = float(row[1])
            if not math.isfinite(value) or value <= 0:
                raise ValueError("invalid L522 index")
            periods[row[0]] = value
    required_periods = {"2015", "2025 APR", "2026 APR"}
    if previous:
        required_periods.update(
            row[0]
            for row in csv_records(previous)
            if row and re.fullmatch(r"\d{4}( Q[1-4]| [A-Z]{3})?", row[0])
        )
    if not required_periods <= periods.keys():
        raise ValueError("L522 required period coverage lost")
    if periods["2015"] != 100:
        raise ValueError("L522 annual base index is not 100")


def _school_texts(rows):
    return {
        (i, j): value
        for i, row in enumerate(rows)
        for j, value in enumerate(row)
        if isinstance(value, str) and value.strip()
    }


def _validate_school_coverage(rows, texts, previous):
    """Compare labels and every previously numeric cell before accepting revisions."""
    old_workbook = openpyxl.load_workbook(previous, read_only=True, data_only=True)
    try:
        old_rows = list(old_workbook["Table 6b"].values)
        old_texts = _school_texts(old_rows)
        if old_texts != texts:
            raise ValueError("Table 6b labels/layout changed; review new vintage")
        for i, row in enumerate(old_rows):
            for j, value in enumerate(row):
                if isinstance(value, (int, float)):
                    current = rows[i][j]
                    if not isinstance(current, (int, float)) or not math.isfinite(current):
                        raise ValueError("Table 6b numeric coverage lost")
    finally:
        old_workbook.close()


def validate_school(path, previous):
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        rows = list(workbook["Table 6b"].values)
        texts = _school_texts(rows)
        combined = " ".join(texts.values())
        for label in (
            "STATE-FUNDED PRIMARY",
            "STATE-FUNDED SECONDARY",
            "Average class size",
            "Percentage of pupils in classes with",
            "31-35 pupils",
            "36 or more pupils",
        ):
            if label not in combined:
                raise ValueError("Table 6b missing " + label)
        if not any(2006 in row and 2015 in row for row in rows):
            raise ValueError("Table 6b vintage/year columns changed")
        if previous:
            _validate_school_coverage(rows, texts, previous)
    finally:
        workbook.close()


def _overcrowding_labels(texts):
    return [text for text in texts if not re.fullmatch(r"\d+(\.\d+)?", text)]


def validate_overcrowding(root, previous):
    table = root.find(f".//{{{TABLE_NS}}}table[@{{{TABLE_NS}}}name='FT1421']")
    if table is None:
        raise ValueError("missing FT1421 sheet")
    texts = ["".join(node.itertext()) for node in table.iter(f"{{{TEXT_NS}}}p")]
    combined = " ".join(texts)
    for label in ("1995-96", "2021-22", "three year", "percentages", "owner", "social", "private"):
        if label not in combined:
            raise ValueError("FT1421 missing " + label)
    values = [
        float(node.attrib[f"{{{OFFICE_NS}}}value"])
        for node in table.iter()
        if f"{{{OFFICE_NS}}}value" in node.attrib
    ]
    if len(values) < 27 * 4 or any(
        not math.isfinite(value) or not 0 <= value <= 100 for value in values
    ):
        raise ValueError("invalid FT1421 percentage coverage")
    if previous:
        with zipfile.ZipFile(previous) as archive:
            old_root = ET.fromstring(archive.read("content.xml"))
        old_table = old_root.find(f".//{{{TABLE_NS}}}table[@{{{TABLE_NS}}}name='FT1421']")
        # Numbers' display text changes on revisions; only compare nonnumeric labels.
        old_texts = ["".join(node.itertext()) for node in old_table.iter(f"{{{TEXT_NS}}}p")]
        if _overcrowding_labels(old_texts) != _overcrowding_labels(texts):
            raise ValueError("FT1421 labels/vintage changed; review before replacing")
        # Deliberately conservative: re-encoding repeated XML cells needs review,
        # even when it might represent the same spreadsheet grid.
        old_cells = list(old_table.iter(f"{{{TABLE_NS}}}table-cell"))
        cells = list(table.iter(f"{{{TABLE_NS}}}table-cell"))
        for index, cell in enumerate(old_cells):
            if f"{{{OFFICE_NS}}}value" in cell.attrib:
                if index >= len(cells) or f"{{{OFFICE_NS}}}value" not in cells[index].attrib:
                    raise ValueError("FT1421 numeric coverage lost")


def _validate_csv_source(source_id, path, previous):
    rows = csv_records(path)
    if len(rows) < 2 or len(rows[0]) < 2 or not any(len(row) >= 2 for row in rows[1:]):
        raise ValueError("invalid CSV records")
    if previous and rows[0] != csv_records(previous)[0]:
        raise ValueError("CSV header/identity changed")
    if source_id == "ons-l522":
        validate_l522(rows, previous)


def _validate_xml_source(body):
    """Bank of England Database XML: a gesmes envelope naming at least one series."""
    root = ET.fromstring(body)
    if root.tag != f"{{{GESMES_NS}}}Envelope":
        raise ValueError("XML is not a gesmes data envelope")
    if not [node for node in root.iter() if node.get("SCODE")]:
        raise ValueError("XML envelope names no series")


def _validate_json_source(body):
    value = json.loads(body)
    if (
        not isinstance(value, (dict, list))
        or not value
        or (isinstance(value, dict) and "error" in value)
    ):
        raise ValueError("invalid JSON dataset/error response")


NHS_NATIONALITY_GROUPS = {
    ("All nationality groups", "All nationalities"),
    ("United Kingdom", "All nationalities"),
    ("European Union", "All nationalities"),
    ("European Economic Area", "All nationalities"),
    ("Rest of World", "All nationalities"),
    ("Unknown", "Unknown"),
}
# The published table repeats "British" just above "Non-British".
SFC_NATIONALITY_ROWS = [
    "Total filled posts",
    "British",
    "EU (non British)",
    "Non-EU",
    "British",
    "Non-British",
]


def _sheet_values(path, sheet, columns):
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        if sheet not in workbook.sheetnames:
            raise ValueError(f"missing sheet {sheet}")
        return [
            list(row)
            for row in workbook[sheet].iter_rows(
                min_row=1, min_col=1, max_col=columns, values_only=True
            )
        ]
    finally:
        workbook.close()


def validate_nhs_nationality(path):
    """NHS Table 14: one month, core-organisation scope and every group total for both measures."""
    rows = _sheet_values(path, "14", 5)
    if "staff by nationality group" not in str(rows[0][0]):
        raise ValueError("NHS Table 14 title changed")
    if rows[1][0] != "Staff in NHS trusts and other core organisations, England":
        raise ValueError("NHS Table 14 scope changed")
    found = {}
    months = set()
    for month, measure, group, nationality, value in rows[6:]:
        if (group, nationality) in NHS_NATIONALITY_GROUPS and measure in ("FTE", "Headcount"):
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError("NHS Table 14 group total is not a count")
            if (measure, group) in found:
                raise ValueError("NHS Table 14 repeats a group total")
            found[(measure, group)] = value
            months.add(month)
    if len(found) != 2 * len(NHS_NATIONALITY_GROUPS) or len(months) != 1:
        raise ValueError("NHS Table 14 group totals or data month changed")


def validate_sfc_nationality(path):
    """Skills for Care Table 4.7.1: labelled filled posts and whole-per-cent shares by sector."""
    rows = _sheet_values(path, "4.7", 6)
    top = next(
        (i for i, row in enumerate(rows) if "Table 4.7.1. Nationality by sector" in row), None
    )
    if top is None or rows[top + 1][1] != "Source: Skills for Care's workforce estimates, 2025/26":
        raise ValueError("Skills for Care Table 4.7.1 missing or period changed")
    if rows[top + 3][2:6] != [
        "All sectors",
        "Local authority",
        "Independent",
        "Direct payment recipients",
    ]:
        raise ValueError("Skills for Care Table 4.7.1 sector columns changed")
    block = rows[top + 4 : top + 10]
    if [row[1] for row in block] != SFC_NATIONALITY_ROWS:
        raise ValueError("Skills for Care Table 4.7.1 rows changed")
    for row in block:
        for value in row[2:6]:
            limit = math.inf if row[1] == "Total filled posts" else 1
            if not isinstance(value, (int, float)) or not 0 <= value <= limit:
                raise ValueError("Skills for Care Table 4.7.1 value is not valid")


def _validate_xlsx_source(source_id, path, previous):
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        if not workbook.sheetnames:
            raise ValueError("XLSX has no sheets")
        for sheet in workbook:
            for _ in sheet.values:
                pass
    finally:
        workbook.close()
    if source_id == "dfe-spc-2015-tables":
        validate_school(path, previous)
    elif source_id == "nhs-hchs-workforce-aug26":
        validate_nhs_nationality(path)
    elif source_id == "sfc-asc-appendix-2026":
        validate_sfc_nationality(path)


def _validate_spreadsheet_source(source_id, path, suffix, previous):
    with zipfile.ZipFile(path) as archive:
        if archive.testzip():
            raise ValueError("corrupt spreadsheet archive")
        if suffix == ".ods":
            if archive.read("mimetype") != b"application/vnd.oasis.opendocument.spreadsheet":
                raise ValueError("not an ODS spreadsheet")
            root = ET.fromstring(archive.read("content.xml"))
            if root.find(f".//{{{TABLE_NS}}}table") is None:
                raise ValueError("ODS has no sheets")
            if source_id == "ehs-ft1421":
                validate_overcrowding(root, previous)
    if suffix == ".xlsx":
        _validate_xlsx_source(source_id, path, previous)


# ASHE Table 1 packs: one sheet per work-pattern and sex combination (Nomis SEX codes 1 to 9).
ASHE_TABLE1_SHEETS = (
    "All",
    "Male",
    "Female",
    "Full-Time",
    "Part-Time",
    "Male Full-Time",
    "Male Part-Time",
    "Female Full-Time",
    "Female Part-Time",
)


def validate_ashe_table1(archive):
    """Gross weekly pay (1.1a) and its CVs (1.1b): every combination's UK median at D6."""
    for table in ("Table 1.1a", "Table 1.1b"):
        names = [
            n
            for n in archive.namelist()
            if table in n and "Weekly pay - Gross" in n and n.endswith(".xlsx")
        ]
        if len(names) != 1:
            raise ValueError(f"ASHE {table} weekly gross pay workbook missing or ambiguous")
        workbook = openpyxl.load_workbook(io.BytesIO(archive.read(names[0])), data_only=True)
        try:
            for sheet in ASHE_TABLE1_SHEETS:
                if sheet not in workbook.sheetnames:
                    raise ValueError(f"ASHE {table} missing sheet {sheet}")
                ws = workbook[sheet]
                if ws["A6"].value != "All Employees" or ws["D5"].value != "Median":
                    raise ValueError(f"ASHE {table} {sheet} layout changed")
                if not isinstance(ws["D6"].value, (int, float)):
                    raise ValueError(f"ASHE {table} {sheet} UK median is not a number")
        finally:
            workbook.close()


def _validate_zip_source(source_id, path):
    """A publisher's pack of workbooks: every workbook must open with at least one sheet."""
    with zipfile.ZipFile(path) as archive:
        if archive.testzip():
            raise ValueError("corrupt zip archive")
        names = [n for n in archive.namelist() if n.lower().endswith(".xlsx")]
        # Older ASHE packs (before 2022) hold legacy .xls workbooks instead.
        legacy = [n for n in archive.namelist() if n.lower().endswith(".xls")]
        if not names and not legacy:
            raise ValueError("zip archive holds no workbooks")
        for name in legacy:
            book = xlrd.open_workbook(file_contents=archive.read(name))
            try:
                if book.nsheets == 0:
                    raise ValueError(f"{name} has no sheets")
            finally:
                book.release_resources()
        for name in names:
            workbook = openpyxl.load_workbook(
                io.BytesIO(archive.read(name)), read_only=True, data_only=True
            )
            try:
                if not workbook.sheetnames:
                    raise ValueError(f"{name} has no sheets")
            finally:
                workbook.close()
        if source_id.startswith("ashe-") and "-table1-" in source_id:
            validate_ashe_table1(archive)


def validate_source(source_id, path, content_type, previous=None):
    body = path.read_bytes()
    if not body:
        raise ValueError("empty response")
    suffix = path.suffix.lower()
    head = body.lstrip()[:2048].lower()
    is_html = head.startswith((b"<!doctype html", b"<html")) or b"<html" in head
    if suffix != ".html" and (is_html or "text/html" in content_type.lower()):
        raise ValueError("HTML/error response instead of source format")
    if suffix == ".csv":
        _validate_csv_source(source_id, path, previous)
    elif suffix == ".json":
        _validate_json_source(body)
    elif suffix == ".xml":
        _validate_xml_source(body)
    elif suffix in {".xlsx", ".ods"}:
        _validate_spreadsheet_source(source_id, path, suffix, previous)
    elif suffix == ".zip":
        _validate_zip_source(source_id, path)
    elif suffix == ".xls":
        workbook = xlrd.open_workbook(path)
        try:
            if workbook.nsheets == 0:
                raise ValueError("XLS has no sheets")
        finally:
            workbook.release_resources()
    elif suffix == ".pdf":
        if not body.startswith(b"%PDF-") or not PdfReader(path, strict=True).pages:
            raise ValueError("invalid PDF")
    elif suffix == ".html":
        text = body.decode("utf-8")
        title = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
        if not is_html or not title or ERROR_PAGE.search(title.group(1)):
            raise ValueError("invalid HTML publication/error page")
    else:
        raise ValueError("unsupported source format: " + suffix)
