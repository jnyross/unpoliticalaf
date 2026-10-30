"""Export receipt audit evidence using bounded ZIP/XML reads, in clean Boat.

No fiscal calculations, missing-value coercion, status inference or publication.
The original spending scope, exporter and manifest are deliberately unchanged.
"""
import csv
import hashlib
import json
from pathlib import Path
import posixpath
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from openpyxl.styles.numbers import BUILTIN_FORMATS
from openpyxl.utils.cell import range_boundaries, get_column_letter

from receipt_audit_scope import (CATALOGUE_SHA256, SOURCE_MANIFEST_SHA256,
                                 SCOPE_ID, DIRECTORY, SHEETS, filename)

ROOT = Path(__file__).resolve().parent.parent
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
COLUMNS = ["cell", "kind", "raw_value_json", "format_id", "formula_json"]


def digest(content):
    return hashlib.sha256(content).hexdigest()


def safe(path):
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Receipt audit/source path contains a symlink")
    return path


def coordinates(ranges):
    result = []
    for region in ranges:
        c1, r1, c2, r2 = range_boundaries(region)
        result.extend(f"{get_column_letter(c)}{r}"
                      for r in range(r1, r2 + 1) for c in range(c1, c2 + 1))
    if len(result) != len(set(result)):
        raise ValueError("Overlapping receipt audit ranges")
    return result


def raw_cells(archive, sheet, selected):
    """Decode only the explicit scope; unrelated Excel chart errors stay outside.

    In-scope errors, booleans, unsupported styles or shared/array formulas fail
    closed. Preserve stored numeric strings and formula caches without rounding.
    """
    strings = []
    if "xl/sharedStrings.xml" in archive.namelist():
        for item in ET.fromstring(archive.read("xl/sharedStrings.xml")):
            strings.append("".join(t.text or "" for t in item.iter("{" + NS["m"] + "}t")))
    styles = ET.fromstring(archive.read("xl/styles.xml"))
    custom = {int(n.attrib["numFmtId"]): n.attrib["formatCode"]
              for n in styles.findall("m:numFmts/m:numFmt", NS)}
    formats = [custom.get(int(n.attrib["numFmtId"]), BUILTIN_FORMATS.get(int(n.attrib["numFmtId"])))
               for n in styles.find("m:cellXfs", NS)]
    rels = {r.attrib["Id"]: r.attrib["Target"]
            for r in ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))}
    sheets = ET.fromstring(archive.read("xl/workbook.xml")).find("m:sheets", NS)
    target = rels[next(s for s in sheets if s.attrib["name"] == sheet).attrib[RID]]
    target = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
    cells = {}
    for cell in ET.fromstring(archive.read(target)).findall("m:sheetData/m:row/m:c", NS):
        coordinate = cell.attrib["r"]
        if coordinate not in selected:
            continue
        if coordinate in cells:
            raise ValueError("Duplicate receipt XML cell")
        kind = cell.attrib.get("t", "n")
        value = cell.find("m:v", NS)
        value = value.text if value is not None else None
        if kind == "s":
            value, kind = strings[int(value)], "text"
        elif kind == "inlineStr":
            value = "".join(t.text or "" for t in cell.findall("m:is//m:t", NS))
            kind = "text"
        elif kind == "str":
            kind = "text"
        elif kind == "n":
            kind = "number" if value is not None else "blank"
        else:
            raise ValueError(f"Unsupported receipt XML cell kind: {sheet}!{coordinate} {kind}")
        formula = cell.find("m:f", NS)
        if formula is not None and formula.attrib:
            raise ValueError("Receipt shared/array formula requires an explicit extraction decision")
        fmt = formats[int(cell.attrib.get("s", "0"))]
        if fmt is None:
            raise ValueError("Unknown receipt number format")
        cells[coordinate] = (kind, value, fmt, formula.text if formula is not None else None)
    return cells


def export(root=ROOT):
    pinned = safe(root / "reference/un-political/SOURCE.json").read_bytes()
    catalogue = safe(root / "data/sources.json").read_bytes()
    if digest(pinned) != SOURCE_MANIFEST_SHA256 or digest(catalogue) != CATALOGUE_SHA256:
        raise ValueError("Receipt pinned manifest/catalogue hash changed")
    sources = json.loads(catalogue)
    files = {f["path"]: f["sha256"] for f in json.loads(pinned)["files"]}
    output = safe(root / DIRECTORY)
    output.mkdir(parents=True, exist_ok=True)
    index = {"schema_version": 1, "scope": SCOPE_ID,
             "pinned_manifest_sha256": SOURCE_MANIFEST_SHA256,
             "catalogue_sha256": CATALOGUE_SHA256, "sheets": []}
    for sid, selected in SHEETS.items():
        source = sources[sid]
        raw = safe(root / source["file"])
        if digest(raw.read_bytes()) != source["sha256"] or source["sha256"] != files[source["file"]]:
            raise ValueError(f"Receipt source hash mismatch: {sid}")
        with ZipFile(raw) as archive:
            for sheet, ranges in selected.items():
                ordered = coordinates(ranges)
                cells = raw_cells(archive, sheet, set(ordered))
                path = safe(output / filename(sid, sheet))
                formats = []
                with path.open("w", newline="", encoding="utf-8") as stream:
                    writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
                    writer.writerow(COLUMNS)
                    for coordinate in ordered:
                        kind, value, fmt, formula = cells.get(coordinate, ("blank", None, "General", None))
                        if fmt not in formats:
                            formats.append(fmt)
                        writer.writerow([coordinate, kind, json.dumps(value, ensure_ascii=False),
                                         formats.index(fmt), json.dumps(formula, ensure_ascii=False)])
                index["sheets"].append({"source_id": sid, "source_file": source["file"],
                    "source_sha256": source["sha256"], "publication": source["publication"],
                    "published": source["published"], "retrieved": source["downloaded"],
                    "sheet": sheet, "ranges": ranges, "file": path.name,
                    "cells": len(ordered), "formats": formats, "sha256": digest(path.read_bytes())})
    safe(output / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Exported {len(index['sheets'])} receipt evidence sheets; no fiscal interpretation or public output")


if __name__ == "__main__":
    export()
