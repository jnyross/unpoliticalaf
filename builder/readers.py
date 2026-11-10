"""Small, dependency-light readers for the official source formats.

Every reader returns plain Python values together with a locator string
(sheet and cell, or CSV row label) so that each published number can be
traced back to the exact place in the original file.
"""

import csv
import io
import re
import zipfile
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path

import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

ROOT = Path(__file__).resolve().parent.parent
ODSValue = float | str | None


@lru_cache(maxsize=None)
def xlsx(path: str) -> Workbook:
    return openpyxl.load_workbook(ROOT / path, data_only=True)


def cell(path: str, sheet: str, ref: str) -> object:
    """Return the value at sheet!ref in an .xlsx file."""
    ws = xlsx(path)[sheet]
    if not isinstance(ws, Worksheet):
        raise ValueError(f"{sheet!r} is not a worksheet")
    found = ws[ref]
    if isinstance(found, tuple):
        raise ValueError(f"{ref!r} is not a single cell reference")
    return found.value


def xlsx_rows(path: str, sheet: str) -> list[list[object]]:
    ws = xlsx(path)[sheet]
    if not isinstance(ws, Worksheet):
        raise ValueError(f"{sheet!r} is not a worksheet")
    return [[c.value for c in row] for row in ws.iter_rows()]


@lru_cache(maxsize=None)
def zip_xlsx(path: str, member: str) -> Workbook:
    """A workbook inside a retained zip pack, such as ONS's ASHE tables."""
    with zipfile.ZipFile(ROOT / path) as archive:
        return openpyxl.load_workbook(io.BytesIO(archive.read(member)), data_only=True)


def zip_sheet(path: str, member: str, sheet: str) -> Worksheet:
    ws = zip_xlsx(path, member)[sheet]
    if not isinstance(ws, Worksheet):
        raise ValueError(f"{sheet!r} is not a worksheet")
    return ws


_NS = {
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
}


def _q(prefix: str, name: str) -> str:
    return "{%s}%s" % (_NS[prefix], name)


@lru_cache(maxsize=None)
def ods(path: str) -> dict[str, list[list[ODSValue]]]:
    """Read every sheet of an .ods file into {sheet: [[value, ...], ...]}.

    Numbers come from office:value (the stored value, not the display text).
    Repeated rows are expanded so row numbers match the spreadsheet; repeated
    columns are expanded up to the last real value in each row.
    """
    with zipfile.ZipFile(ROOT / path) as z:
        root = ET.fromstring(z.read("content.xml"))
    sheets: dict[str, list[list[ODSValue]]] = {}
    for table in root.iter(_q("table", "table")):
        repeated_rows: list[tuple[list[ODSValue], int]] = []
        for row in table.iter(_q("table", "table-row")):
            values: list[ODSValue] = []
            for c in row:
                if c.tag not in (_q("table", "table-cell"), _q("table", "covered-table-cell")):
                    continue
                repeat = int(c.get(_q("table", "number-columns-repeated"), "1"))
                vtype = c.get(_q("office", "value-type"))
                v: ODSValue
                if vtype in ("float", "percentage", "currency"):
                    stored = c.get(_q("office", "value"))
                    if stored is None:
                        raise ValueError("Numeric ODS cell has no office:value")
                    v = float(stored)
                else:
                    text = "\n".join("".join(p.itertext()) for p in c.iter(_q("text", "p")))
                    v = text if text != "" else None
                values.extend([v] * min(repeat, 200))
            while values and values[-1] is None:
                values.pop()
            repeat = int(row.get(_q("table", "number-rows-repeated"), "1"))
            repeated_rows.append((values, repeat))
        while repeated_rows and not repeated_rows[-1][0]:
            repeated_rows.pop()  # trailing empty rows carry no data
        rows = [values for values, repeat in repeated_rows for _ in range(repeat)]
        name = table.get(_q("table", "name"))
        if name is None:
            raise ValueError("ODS table has no name")
        sheets[name] = rows
    return sheets


def ref(row_index: int, col_index: int) -> str:
    """Spreadsheet-style reference from 0-based indexes."""
    return f"{get_column_letter(col_index + 1)}{row_index + 1}"


def ons_series(path: str) -> tuple[dict[str, str], dict[str, float | None]]:
    """Parse an ONS time-series CSV (generator format) into metadata and periods."""
    text = (ROOT / path).read_text(encoding="utf-8-sig")
    meta: dict[str, str] = {}
    data: dict[str, float | None] = {}
    for row in csv.reader(io.StringIO(text)):
        if len(row) < 2:
            continue
        key, value = row[0], row[1]
        if re.fullmatch(r"\d{4}( Q[1-4]| [A-Z]{3})?", key):
            data[key] = None if value.strip() in ("", "x", "..") else float(value)
        else:
            meta[key] = value
    return meta, data


def csv_rows(path: str) -> Sequence[dict[str | None, str | list[str] | None]]:
    return list(csv.DictReader(io.StringIO((ROOT / path).read_text(encoding="utf-8-sig"))))


@lru_cache(maxsize=None)
def pdf_pages(path: str) -> list[str]:
    """Text of each page of a PDF, one string per page (page 1 is index 0)."""
    from pypdf import PdfReader

    return [p.extract_text() or "" for p in PdfReader(ROOT / path).pages]


def pdf_number(path: str, locator: str) -> float:
    """Read a number from a PDF by a locator like
    "p10 after 'Holidays Q4 2024' line 'Visits (million))' number 5":
    on page 10, after the first line starting with the anchor text, the first line
    starting with the line label, and the nth number on that line (counting from 1).
    """
    m = re.fullmatch(r"p(\d+) after '(.+)' line '(.+)' number (\d+)", locator)
    if m is None:
        raise ValueError(f"Invalid PDF number locator: {locator!r}")
    page, anchor, label, n = int(m.group(1)), m.group(2), m.group(3), int(m.group(4))
    if page < 1 or n < 1:
        raise ValueError("PDF page and number indexes must start at 1")
    lines = pdf_pages(path)[page - 1].splitlines()
    start = next(i for i, l in enumerate(lines) if l.strip().startswith(anchor))
    line = next(l for l in lines[start + 1 :] if l.strip().startswith(label))
    nums = re.findall(r"-?[\d,]+(?:\.\d+)?", line[len(label) + line.index(label) :])
    return float(nums[n - 1].replace(",", ""))
