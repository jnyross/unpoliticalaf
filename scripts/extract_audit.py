"""Export scoped, unrounded source cells using ZIP/XML, not build_data.py.

Run only in the credential-free check environment. The TSV files are private
review inputs and are deliberately absent from the public output allowlist.
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

from audit_scope import CATALOGUE_SHA256, SHEETS, SOURCE_MANIFEST_SHA256, filename

ROOT = Path(__file__).resolve().parent.parent
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def digest(content):
    return hashlib.sha256(content).hexdigest()


def raw_sheet(archive, sheet):
    """Return resolved original XML values, including formula caches and styles."""
    strings = []
    if "xl/sharedStrings.xml" in archive.namelist():
        for item in ET.fromstring(archive.read("xl/sharedStrings.xml")):
            strings.append("".join(t.text or "" for t in item.iter("{" + NS["m"] + "}t")))
    styles = ET.fromstring(archive.read("xl/styles.xml"))
    custom = {int(n.attrib["numFmtId"]): n.attrib["formatCode"]
              for n in styles.findall("m:numFmts/m:numFmt", NS)}
    formats = [custom.get(int(n.attrib["numFmtId"]), BUILTIN_FORMATS.get(int(n.attrib["numFmtId"])))
               for n in styles.find("m:cellXfs", NS)]
    if any(f is None for f in formats):
        raise ValueError("Unknown number format")
    rels = {r.attrib["Id"]: r.attrib["Target"]
            for r in ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))}
    sheets = ET.fromstring(archive.read("xl/workbook.xml")).find("m:sheets", NS)
    target = rels[next(s for s in sheets if s.attrib["name"] == sheet).attrib[RID]]
    target = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
    cells = {}
    for cell in ET.fromstring(archive.read(target)).findall("m:sheetData/m:row/m:c", NS):
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
            raise ValueError(f"Unsupported XML cell kind {kind}")
        formula = cell.find("m:f", NS)
        if formula is not None and formula.attrib:
            raise ValueError("Shared/array formula requires an explicit extraction decision")
        cells[cell.attrib["r"]] = (kind, value, formats[int(cell.attrib.get("s", "0"))],
                                   formula.text if formula is not None else None)
    return cells


def export(root=ROOT):
    pinned = (root / "reference/un-political/SOURCE.json").read_bytes()
    catalogue_bytes = (root / "data/sources.json").read_bytes()
    if digest(pinned) != SOURCE_MANIFEST_SHA256 or digest(catalogue_bytes) != CATALOGUE_SHA256:
        raise ValueError("Pinned manifest/catalogue hash changed")
    sources = json.loads(catalogue_bytes)
    pinned_files = {f["path"]: f["sha256"] for f in json.loads(pinned)["files"]}
    output = root / "data/audit"
    output.mkdir(parents=True, exist_ok=True)
    (output / "pinned-source.json").write_bytes(pinned)
    index = {"schema_version": 1, "pinned_manifest_sha256": digest(pinned),
             "catalogue_sha256": digest(catalogue_bytes), "sheets": []}
    for source_id, selected in SHEETS.items():
        source = sources[source_id]
        raw = root / source["file"]
        if raw.is_symlink() or digest(raw.read_bytes()) != source["sha256"] or source["sha256"] != pinned_files[source["file"]]:
            raise ValueError(f"Source hash mismatch: {source_id}")
        with ZipFile(raw) as archive:
            for sheet, ranges in selected.items():
                cells = raw_sheet(archive, sheet)
                path = output / filename(source_id, sheet)
                seen, formats = set(), []
                with path.open("w", newline="", encoding="utf-8") as stream:
                    writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
                    writer.writerow(["cell", "kind", "raw_value_json", "format_id", "formula_json"])
                    for region in ranges:
                        c1, r1, c2, r2 = range_boundaries(region)
                        for row in range(r1, r2 + 1):
                            for col in range(c1, c2 + 1):
                                coordinate = f"{get_column_letter(col)}{row}"
                                if coordinate in seen:
                                    raise ValueError("Overlapping audit ranges")
                                seen.add(coordinate)
                                kind, value, fmt, formula = cells.get(coordinate, ("blank", None, "General", None))
                                if fmt not in formats:
                                    formats.append(fmt)
                                writer.writerow([coordinate, kind, json.dumps(value, ensure_ascii=False),
                                                 formats.index(fmt), json.dumps(formula, ensure_ascii=False)])
                index["sheets"].append({"source_id": source_id, "source_file": source["file"],
                    "source_sha256": source["sha256"], "publication": source["publication"],
                    "published": source["published"], "retrieved": source["downloaded"],
                    "sheet": sheet, "ranges": ranges, "file": path.name, "cells": len(seen),
                    "formats": formats, "sha256": digest(path.read_bytes())})
    (output / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Exported {len(index['sheets'])} scoped sheets; exact raw numeric strings retained")


if __name__ == "__main__":
    export()
