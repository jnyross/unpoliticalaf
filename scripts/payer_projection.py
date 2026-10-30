"""Small public projection from the retained payer workbooks. No writes on import.

project(root) returns JSON-compatible data. The independent checker must approve
that data before the controller publishes it. This reader never fills source gaps.
"""
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

RAW = "data/payers/raw/"
FILES = (
    "hmrc-latest-release.html.json", "hmrc-table24-july2026.ods",
    "ons-bulletin-2024.html.json", "ons-dataset-page.html.json",
    "ons-etb-fye2024.xlsx", "ons-qmi.html.json", "ons-technical-2019.html.json",
)
NS = {"t": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
      "o": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
      "p": "urn:oasis:names:tc:opendocument:xmlns:text:1.0"}
HMRC_POPULATION = "UK individuals with positive Income Tax liability"
HMRC_RANKING = "Income assessable for tax before deductions and allowances"
ONS_POPULATION = "UK people in private households"
ONS_RANKING = "Equivalised household disposable income"
HMRC_STATUS = "Estimated outturn"
ONS_STATUS = "Completed-year survey/model estimates, not a forecast"
MEASURES = (("direct", 5, "Direct taxes", "Gross household income"),
            ("indirect", 9, "Indirect taxes", "Gross household income"),
            ("combined", 15, "Direct and indirect taxes counted in this ONS analysis", "Gross household income"),
            ("expenditure", 22, "Indirect taxes", "Household expenditure"))


def safe_file(root, relative):
    given = Path(root).absolute()
    if any(p.is_symlink() for p in (given, *given.parents)):
        raise ValueError("Symlink in payer input root")
    root = given.resolve(strict=True)
    target = root / relative
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("Unsafe payer source path")
    for part in (target, *target.parents):
        if part == root:
            break
        if part.is_symlink():
            raise ValueError("Symlink in payer source path")
    if not target.is_file() or not target.resolve().is_relative_to(root):
        raise ValueError("Payer source is outside the input root or missing")
    return target


def sources(root):
    register = json.loads(safe_file(root, "data/payers/sources.json").read_text())
    if register.get("schema_version") != 1:
        raise ValueError("Unknown payer source register")
    rows = register["sources"]
    if len(rows) != len(FILES) or {s["file"] for s in rows} != {RAW + f for f in FILES}:
        raise ValueError("Unexpected payer source set")
    public = {}
    for index, filename in enumerate(FILES):
        entry = next(s for s in rows if s["file"] == RAW + filename)
        blob = safe_file(root, entry["file"]).read_bytes()
        if filename.endswith(".json"):
            if len(blob) != entry["stored_bytes"] or hashlib.sha256(blob).hexdigest() != entry["stored_sha256"]:
                raise ValueError("Payer envelope hash mismatch")
            envelope = json.loads(blob)
            if (set(envelope) != {"encoding", "original_response"} or
                    envelope.get("encoding") != "utf-8" or not isinstance(envelope.get("original_response"), str)):
                raise ValueError("Invalid lossless payer envelope")
            blob = envelope["original_response"].encode("utf-8")
        if len(blob) != entry["bytes"] or hashlib.sha256(blob).hexdigest() != entry["sha256"]:
            raise ValueError("Payer source hash mismatch")
        sid = ("hmrc_release", "hmrc", "ons_bulletin", "ons_dataset", "ons", "ons_qmi", "ons_method")[index]
        public[sid] = {"url": entry["url"], "sha256": entry["sha256"], "bytes": entry["bytes"],
                       "published": entry["publication_or_update_date"],
                       "publisher": "HM Revenue & Customs" if sid.startswith("hmrc") else "Office for National Statistics",
                       "publication": {"hmrc_release": "Income Tax liabilities, July 2026 release",
                                       "hmrc": "Income Tax liabilities, Table 2.4",
                                       "ons_bulletin": "Effects of taxes and benefits, FYE 2024 bulletin",
                                       "ons_dataset": "Effects of taxes and benefits dataset",
                                       "ons": "Effects of taxes and benefits, FYE 2024 reference tables",
                                       "ons_method": "Effects of taxes and benefits, FYE 2019 technical report",
                                       "ons_qmi": "Effects of taxes and benefits QMI"}.get(sid, sid.replace("_", " "))}
        if filename.endswith(".json"):
            public[sid].update(stored_sha256=entry["stored_sha256"], stored_bytes=entry["stored_bytes"])
    return public


def colname(number):
    result = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def odf_text(element):
    """Preserve the ODF text:s, tab, line-break and inline-span semantics."""
    result = element.text or ""
    for child in element:
        if child.tag == f"{{{NS['p']}}}s":
            count = child.get(f"{{{NS['p']}}}c", "1")
            if not re.fullmatch(r"[1-9][0-9]{0,4}", count):
                raise ValueError("Unsafe ODF space count")
            part = " " * int(count)
        elif child.tag == f"{{{NS['p']}}}tab":
            part = "\t"
        elif child.tag == f"{{{NS['p']}}}line-break":
            part = "\n"
        else:
            part = odf_text(child)
        result += part + (child.tail or "")
    return result


def ods_cells(path):
    """Read sparse ODS cells. Advance repeats without expanding empty tails."""
    with ZipFile(path) as archive:
        xml = ET.fromstring(archive.read("content.xml"))
    result = {}
    for table in xml.findall(".//t:table", NS):
        sheet = table.get(f"{{{NS['t']}}}name")
        row_number = 1
        for row in table.findall(".//t:table-row", NS):
            repeated_rows = int(row.get(f"{{{NS['t']}}}number-rows-repeated", "1"))
            column = 1
            for cell in row:
                if cell.tag not in {f"{{{NS['t']}}}table-cell", f"{{{NS['t']}}}covered-table-cell"}:
                    continue
                repeats = int(cell.get(f"{{{NS['t']}}}number-columns-repeated", "1"))
                text = "\n".join(odf_text(p) for p in cell.findall("p:p", NS))
                stored = cell.get(f"{{{NS['o']}}}value")
                formula = cell.get(f"{{{NS['t']}}}formula")
                value = float(stored) if stored is not None else text or None
                if text or stored is not None or formula:
                    for r in range(row_number, min(row_number + repeated_rows, 101)):
                        for c in range(column, min(column + repeats, 41)):
                            result[(sheet, f"{colname(c)}{r}")] = {"value": value, "text": text, "formula": formula}
                column += repeats
            row_number += repeated_rows
    return result


def number(value):
    """Do not coerce blanks, suppressed cells, dashes or booleans to zero."""
    if isinstance(value, bool) or value is None:
        raise ValueError("Required payer value is missing")
    try:
        result = float(Decimal(str(value)))
    except (InvalidOperation, ValueError):
        raise ValueError("Required payer value is not numeric") from None
    if not math.isfinite(result) or not 0 <= result <= 100:
        raise ValueError("Invalid published percentage")
    return result


def project(root):
    """Return only the approved 23 published percentages and their provenance."""
    from openpyxl import load_workbook

    src = sources(root)
    ods = ods_cells(safe_file(root, RAW + "hmrc-table24-july2026.ods"))
    workbook_path = safe_file(root, RAW + "ons-etb-fye2024.xlsx")
    workbook = load_workbook(workbook_path, read_only=True, data_only=True)
    formula_book = load_workbook(workbook_path, read_only=True, data_only=False)
    evidence = {}

    def retain(sid, sheet, address):
        key = f"{sid}:{sheet}!{address}"
        if key not in evidence:
            if sid == "hmrc":
                raw = ods.get((sheet, address), {"value": None, "text": "", "formula": None})
            else:
                cell = workbook[sheet][address]
                formula = formula_book[sheet][address]
                raw = {"value": cell.value, "text": None,
                       "formula": formula.value if formula.data_type == "f" else None}
            evidence[key] = {"source_id": sid, "sheet": sheet, "cell": address, **raw}
        return key

    values = []

    def add(vid, sid, sheet, address, group, measure, denominator, labels):
        reference = retain(sid, sheet, address)
        value = number(evidence[reference]["value"])
        # Display aliases must be supported by the selected source year labels.
        if sid == "hmrc":
            period_ref = retain(sid, sheet, "A27")
            basis_ref = retain(sid, sheet, "A2")
            match = re.fullmatch(r"(\d{4}) to (\d{4})", str(evidence[period_ref]["value"]).strip())
            if not match or match.groups() != ("2023", "2024") or evidence[basis_ref]["value"] != "Tax year":
                raise ValueError("HMRC source period/year basis changed")
            period, basis = match[1] + "/" + match[2][-2:], evidence[basis_ref]["value"]
        else:
            period_ref = retain(sid, "Table 8", "A1")
            basis_ref = retain(sid, "Cover sheet", "A5")
            match = re.search(r", UK, (\d{4}/\d{2})$", str(evidence[period_ref]["value"]))
            basis_note = evidence[basis_ref]["value"]
            if (not match or match[1] != "2023/24" or basis_note !=
                    "2023/24 refers to the financial year ending 2024.  Similarly other years in this format refer to financial years."):
                raise ValueError("ONS source period/year basis changed")
            period, basis = match[1], "Financial year ending 2024"
        labels = labels + ([(sheet, "A2")] if sid == "hmrc" else [("Cover sheet", "A5")])
        values.append({"id": vid, "value": value, "group": group, "measure": measure,
                       "source_id": sid, "sheet": sheet, "cell": address,
                       "source_sha256": src[sid]["sha256"], "published": src[sid]["published"],
                       "period": period, "year_basis": basis,
                       "status": HMRC_STATUS if sid == "hmrc" else ONS_STATUS,
                       "unit": "%", "denominator": denominator, "geography": "UK",
                       "population": HMRC_POPULATION if sid == "hmrc" else ONS_POPULATION,
                       "ranking": HMRC_RANKING if sid == "hmrc" else ONS_RANKING,
                       "formula": None, "operands": [], "source_cell": reference,
                       "label_cells": [retain(sid, sh, a) for sh, a in labels]})

    try:
        sheet = "2_4_Taxpayer_share_tax"
        for column, gid, group in (("F", "bottom50", "Bottom 50%"), ("I", "top10", "Top 10%"), ("K", "top1", "Top 1%")):
            add("hmrc-" + gid, "hmrc", sheet, column + "27", group, "Share of Income Tax due",
                "Total Income Tax liabilities", [(sheet, "A1"), (sheet, "A27"), (sheet, column + "2"), ("Contents", "A5")])
        for index, column in enumerate("DEFGH"):
            group = ("Bottom fifth", "Second fifth", "Middle fifth", "Fourth fifth", "Top fifth")[index]
            for key, row, label, denominator in MEASURES:
                add(f"ons-{index + 1}-{key}", "ons", "Table 8", f"{column}{row}", group, label, denominator,
                    [("Table 8", "A1"), ("Table 8", column + "4"), ("Table 8", f"B{row}"),
                     ("Table 8", "A22" if row == 22 else "A5")])
        for address in ("A3", "A4", "A5", "A6"):
            retain("hmrc", "Contents", address)
        for sheet, addresses in {
            "Cover sheet": ("A1", "A5", "A6", "A9", "A20", "A23"),
            "Table 8": ("A2",),
            "Notes": ("B4", "B6", "A8", "B8", "A9", "B9", "A16", "B16", "B31"),
            "Table 2b": ("A43", "B44", "B45", "A65", "B66", "C45"),
        }.items():
            for address in addresses:
                retain("ons", sheet, address)
    finally:
        workbook.close()
        formula_book.close()
    return {"schema_version": 1, "scope": "Two separate official views; not complete all-tax incidence",
            "sources": src, "values": values, "source_cells": evidence,
            "groups_overlap": True, "ons_group_basis": "Five approximately equal-person groups, not equal-household groups"}
