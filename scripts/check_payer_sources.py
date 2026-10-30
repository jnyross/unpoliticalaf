"""Reopen the seven retained payer sources and every readable audit cell.

Source evidence only: this does not accept a renderer or approve tax incidence.
No exporter or fiscal transformation is imported.
"""
import csv
import hashlib
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from openpyxl import load_workbook
from openpyxl.utils.cell import range_boundaries, get_column_letter

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = Path("data/payers")
REGISTER_SHA256 = "25fac4399c7f622848e86a208fa8546d9c0c09f5368f13a952447a098d116dcf"
HMRC = "hmrc-table24-july2026.ods"
ONS = "ons-etb-fye2024.xlsx"
T = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"
TEXT = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"


def cells(*ranges):
    result = []
    for region in ranges:
        c1, r1, c2, r2 = range_boundaries(region)
        result.extend(f"{get_column_letter(c)}{r}"
                      for r in range(r1, r2 + 1) for c in range(c1, c2 + 1))
    return result


# Selection is independent of the editable CSV/index, including labels and notes.
HMRC_SCOPE = {"Contents": cells("A3:A6")}
HMRC_SCOPE.update({sheet: cells("A1", "A2:L2", "A26:L30") for sheet in (
    "2_4_Taxpayer_share_inc_pretax", "2_4_Taxpayer_share_inc_posttax",
    "2_4_Taxpayer_share_tax", "2_4_Taxpayer_inc_quantiles")})
ONS_SCOPE = {
    "Cover sheet": cells("A1", "A5:A6", "A9", "A17", "A20", "A23"),
    "Notes": cells(*(f"A{r}:B{r}" for r in
                     (4, 6, 8, 9, 11, 12, 14, 19, 31, 34, 35, 16))),
    "Table 2b": cells(
        "A1:A2", "A4", "C6:M6", "A7:B7", "D7:L7",
        "B8:M9", "B16:M16", "B40:M40", "A41:M41", "B42:M42",
        "A43:M43", "B44:M48", "A49:M49", "B50:M50", "A51:M51",
        "A65:M65", "B66:M66", "B70:M70", "A71:M71"),
    "Table 8": cells(
        "A1:A3", "D4:I4", "A5:B5", "D5:I5", "C6:I8", "B9", "D9:I9",
        "C10:I14", "B15", "D15:I15", "A16:B16", "D16:I16",
        "C17:I21", "A22:B22", "D22:I22", "C23:I27"),
    "Table 2a": cells("C6:H6", "B41:H41", "B48:H49", "B70:H70"),
}
AUDITS = {
    "hmrc-cells.csv": (HMRC, "published_text", HMRC_SCOPE),
    "ons-cells.csv": (ONS, "published_value", ONS_SCOPE),
}


def read(path):
    path = Path(path)
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError("Payer evidence must be a regular file without symlinks")
    return path.read_bytes()


def digest(body):
    return hashlib.sha256(body).hexdigest()


def check_bytes(body, expected_hash, expected_length, label):
    if len(body) != expected_length or digest(body) != expected_hash:
        raise ValueError(f"Payer {label} hash/length mismatch")


def sources(root):
    base = root / DIRECTORY
    register_bytes = read(base / "sources.json")
    if digest(register_bytes) != REGISTER_SHA256:
        raise ValueError("Pinned payer source register hash changed")
    register = json.loads(register_bytes)
    entries = register["sources"]
    if register["schema_version"] != 1 or len(entries) != 7:
        raise ValueError("Payer source scope changed")
    original = {}
    for entry in entries:
        path = Path(entry["file"])
        if path.parent != DIRECTORY / "raw" or path.name in original:
            raise ValueError("Payer source path/identity changed")
        stored = read(root / path)
        body = stored
        if path.name.endswith(".html.json"):
            check_bytes(stored, entry["stored_sha256"], entry["stored_bytes"], "stored envelope")
            envelope = json.loads(stored.decode("ascii"))
            if set(envelope) != {"encoding", "original_response"} or envelope["encoding"] != "utf-8":
                raise ValueError("Payer HTML envelope fields changed")
            body = envelope["original_response"].encode("utf-8")
        check_bytes(body, entry["sha256"], entry["bytes"], "original response")
        original[path.name] = body
    return original


def repeat(element, attribute, limit):
    value = element.get(T + attribute, "1")
    if not re.fullmatch(r"[1-9][0-9]{0,6}", value) or int(value) > limit:
        raise ValueError("Unsafe ODS repeat count")
    return int(value)


def paragraph_text(element):
    """ODF text, preserving explicit spaces, tabs and line breaks."""
    result = element.text or ""
    for child in element:
        if child.tag == TEXT + "s":
            count = child.get(TEXT + "c", "1")
            if not re.fullmatch(r"[1-9][0-9]{0,4}", count):
                raise ValueError("Unsafe ODS space count")
            part = " " * int(count)
        elif child.tag == TEXT + "tab":
            part = "\t"
        elif child.tag == TEXT + "line-break":
            part = "\n"
        else:
            part = paragraph_text(child)
        result += part + (child.tail or "")
    return result


def ods_cells(source, scope):
    """Read selected displayed text without expanding repeated row/cell arrays."""
    with ZipFile(source) as archive:
        xml = ET.fromstring(archive.read("content.xml"))
    tables = {t.get(T + "name"): t for t in xml.iter(T + "table")}
    result = {}
    for name, coordinates in scope.items():
        if name not in tables:
            raise ValueError(f"Missing ODS sheet: {name}")
        targets = {}
        for coordinate in coordinates:
            c, r, _, _ = range_boundaries(coordinate)
            targets[coordinate] = (r, c)
        selected = {}
        row_number = 1
        for row in tables[name].iter(T + "table-row"):
            height = repeat(row, "number-rows-repeated", 1048576)
            if row_number + height - 1 > 1048576:
                raise ValueError("ODS row extent exceeds grid")
            wanted = {key: c for key, (r, c) in targets.items()
                      if row_number <= r < row_number + height}
            if wanted:
                column = 1
                for cell in row:
                    if cell.tag not in (T + "table-cell", T + "covered-table-cell"):
                        continue
                    width = repeat(cell, "number-columns-repeated", 16384)
                    if column + width - 1 > 16384:
                        raise ValueError("ODS column extent exceeds grid")
                    matches = [key for key, c in wanted.items() if column <= c < column + width]
                    if matches:
                        text = "\n".join(paragraph_text(p) for p in cell.findall(TEXT + "p"))
                        for key in matches:
                            selected[key] = text
                    column += width
            row_number += height
        # An omitted cell is blank, never zero. Repeated empty tails remain bounded.
        result[name] = {key: selected.get(key, "") for key in coordinates}
    return result


def xlsx_cells(source, scope):
    workbook = load_workbook(source, read_only=True, data_only=True)
    try:
        result = {}
        for name, coordinates in scope.items():
            if name not in workbook.sheetnames:
                raise ValueError(f"Missing XLSX sheet: {name}")
            wanted = set(coordinates)
            bounds = [range_boundaries(c) for c in coordinates]
            values = {c: "" for c in coordinates}
            for row in workbook[name].iter_rows(
                    max_row=max(b[1] for b in bounds), max_col=max(b[0] for b in bounds)):
                for cell in row:
                    if getattr(cell, "coordinate", None) in wanted:
                        # Cache only: no formula evaluation and no coercion of suppression/blank to zero.
                        values[cell.coordinate] = "" if cell.value is None else str(cell.value)
            result[name] = values
        return result
    finally:
        workbook.close()


def validate(root=ROOT):
    from io import BytesIO

    root = Path(root)
    originals = sources(root)
    audit_dir = root / DIRECTORY / "audit"
    index = json.loads(read(audit_dir / "index.json"))
    if set(index) != {"schema_version", "audits"} or index["schema_version"] != 1 or set(index["audits"]) != set(AUDITS):
        raise ValueError("Payer audit index scope changed")
    count = 0
    for filename, (snapshot, value_field, scope) in AUDITS.items():
        body = read(audit_dir / filename)
        if digest(body) != index["audits"][filename]:
            raise ValueError("Payer audit CSV hash mismatch")
        with (audit_dir / filename).open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, strict=True)
            fields = ["snapshot", "sheet", "cell", value_field]
            if reader.fieldnames != fields:
                raise ValueError("Payer audit CSV columns changed")
            rows = list(reader)
        expected = {(sheet, c) for sheet, coords in scope.items() for c in coords}
        if any(set(row) != set(fields) or any(v is None for v in row.values()) for row in rows):
            raise ValueError("Malformed payer audit CSV row")
        identities = [(row["sheet"], row["cell"]) for row in rows]
        if (len(identities) != len(expected) or set(identities) != expected
                or any(row["snapshot"] != snapshot for row in rows)):
            raise ValueError("Payer audit missing, duplicate or wrong cell identity")
        source = BytesIO(originals[snapshot])
        actual = ods_cells(source, scope) if snapshot == HMRC else xlsx_cells(source, scope)
        for row in rows:
            if actual[row["sheet"]][row["cell"]] != row[value_field]:
                raise ValueError(f"Payer source cell mismatch: {snapshot} {row['sheet']}!{row['cell']}")
            count += 1
    print(f"Payer source evidence: 7 original responses and {count} audit cells verified; no fiscal sign-off")
    return count


if __name__ == "__main__":
    validate()
