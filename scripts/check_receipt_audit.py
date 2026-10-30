"""Independently verify the separate receipt audit scope against raw workbooks.

This reader does not import the XML exporter or the fiscal transformation.
It checks selections, labels, blanks, dashes, units, formulas and number formats,
as well as numeric values. It is a source-evidence check, not a fiscal sign-off.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace

from openpyxl import load_workbook
from openpyxl.utils.cell import range_boundaries, get_column_letter

from receipt_audit_scope import (CATALOGUE_SHA256, SHEETS, SOURCE_MANIFEST_SHA256,
                                 SCOPE_ID, DIRECTORY, filename)

ROOT = Path(__file__).resolve().parent.parent


def sha(path):
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Audit/source path contains a symlink")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root=ROOT):
    output = root / DIRECTORY
    catalogue = root / "data/sources.json"
    pinned = root / "reference/un-political/SOURCE.json"
    if sha(catalogue) != CATALOGUE_SHA256 or sha(pinned) != SOURCE_MANIFEST_SHA256:
        raise ValueError("Pinned manifest/catalogue hash changed")
    sources = json.loads(catalogue.read_text())
    files = {f["path"]: f["sha256"] for f in json.loads(pinned.read_text())["files"]}
    index_path = output / "index.json"
    sha(index_path)  # Reject symlinks in the manifest path as well as TSV/raw paths.
    index = json.loads(index_path.read_text())
    if set(index) != {"schema_version", "scope", "pinned_manifest_sha256", "catalogue_sha256", "sheets"} or index["scope"] != SCOPE_ID:
        raise ValueError("Receipt audit manifest scope/fields changed")
    if index["schema_version"] != 1 or index["pinned_manifest_sha256"] != SOURCE_MANIFEST_SHA256 or index["catalogue_sha256"] != CATALOGUE_SHA256:
        raise ValueError("Audit manifest identity changed")
    expected = {(sid, sheet) for sid, sheets in SHEETS.items() for sheet in sheets}
    entries = index["sheets"]
    fields = {"source_id", "source_file", "source_sha256", "publication", "published",
              "retrieved", "sheet", "ranges", "file", "cells", "formats", "sha256"}
    if not isinstance(entries, list) or any(not isinstance(e, dict) or set(e) != fields for e in entries):
        raise ValueError("Receipt audit entry fields changed")
    if len(entries) != len(expected) or {(e["source_id"], e["sheet"]) for e in entries} != expected:
        raise ValueError("Missing or duplicate audit sheet")
    count = 0
    for sid, selected in SHEETS.items():
        source = sources[sid]
        path = root / source["file"]
        if sha(path) != source["sha256"] or source["sha256"] != files[source["file"]]:
            raise ValueError(f"Source hash mismatch: {sid}")
        # Streaming mode preserves the stored styles on cells inside merged
        # ranges; normal mode replaces those with synthetic MergedCell objects.
        values = load_workbook(path, read_only=True, data_only=True)
        formulas = load_workbook(path, read_only=True, data_only=False)
        try:
            for sheet, ranges in selected.items():
                bounds = [range_boundaries(r) for r in ranges]
                limits = {"max_row": max(b[3] for b in bounds), "max_col": max(b[2] for b in bounds)}
                source_cells = {c.coordinate: c for row in values[sheet].iter_rows(**limits) for c in row if hasattr(c, "coordinate")}
                formula_cells = {c.coordinate: c for row in formulas[sheet].iter_rows(**limits) for c in row if hasattr(c, "coordinate")}
                blank = SimpleNamespace(value=None, number_format="General", data_type="n")
                entry = next(e for e in entries if (e["source_id"], e["sheet"]) == (sid, sheet))
                for key, value in {"source_file": source["file"], "source_sha256": source["sha256"],
                                   "publication": source["publication"], "published": source["published"],
                                   "retrieved": source["downloaded"], "ranges": ranges,
                                   "file": filename(sid, sheet)}.items():
                    if entry[key] != value:
                        raise ValueError(f"Audit source/selection mismatch: {sid} {sheet} {key}")
                extract = output / entry["file"]
                if not isinstance(entry["formats"], list) or not entry["formats"] or any(not isinstance(f, str) for f in entry["formats"]):
                    raise ValueError("Receipt audit format dictionary changed")
                if sha(extract) != entry["sha256"]:
                    raise ValueError(f"Audit extract hash mismatch: {sheet}")
                coordinates = []
                for region in ranges:
                    c1, r1, c2, r2 = range_boundaries(region)
                    coordinates.extend(f"{get_column_letter(c)}{r}" for r in range(r1, r2+1) for c in range(c1, c2+1))
                with extract.open(newline="", encoding="utf-8") as stream:
                    reader = csv.DictReader(stream, delimiter="\t")
                    if reader.fieldnames != ["cell", "kind", "raw_value_json", "format_id", "formula_json"]:
                        raise ValueError("Audit columns changed")
                    rows = list(reader)
                if any(set(r) != set(reader.fieldnames) or any(v is None for v in r.values()) for r in rows):
                    raise ValueError("Receipt audit malformed row")
                if len(coordinates) != len(set(coordinates)) or entry["cells"] != len(coordinates) or [r["cell"] for r in rows] != coordinates:
                    raise ValueError(f"Audit missing, duplicate or wrong cell: {sheet}")
                for row in rows:
                    coordinate = row["cell"]
                    cell, formula = source_cells.get(coordinate, blank), formula_cells.get(coordinate, blank)
                    value = json.loads(row["raw_value_json"])
                    kind = row["kind"]
                    if kind == "number":
                        if not isinstance(cell.value, (int, float)) or isinstance(cell.value, bool) or not isinstance(value, str) or not math.isfinite(float(value)) or float(value) != cell.value:
                            raise ValueError(f"Audit numeric cell mismatch: {sheet}!{coordinate}")
                    elif kind == "text":
                        # openpyxl represents empty inline strings as None.
                        if not isinstance(value, str) or (cell.value != value and not (value == "" and cell.value is None)) or (cell.value is not None and not isinstance(cell.value, str)):
                            raise ValueError(f"Audit text/label/unit mismatch: {sheet}!{coordinate}")
                    elif kind == "blank":
                        if value is not None or cell.value is not None:
                            raise ValueError(f"Audit missing value mismatch: {sheet}!{coordinate}")
                    else:
                        raise ValueError("Unknown audit cell kind")
                    try:
                        fmt_id = int(row["format_id"])
                    except ValueError as exc:
                        raise ValueError("Audit source precision mismatch: invalid format ID") from exc
                    if fmt_id < 0 or fmt_id >= len(entry["formats"]) or entry["formats"][fmt_id] != cell.number_format:
                        raise ValueError(f"Audit source precision mismatch: {sheet}!{coordinate}")
                    expected_formula = formula.value[1:] if formula.data_type == "f" else None
                    if json.loads(row["formula_json"]) != expected_formula:
                        raise ValueError(f"Audit formula mismatch: {sheet}!{coordinate}")
                    count += 1
        finally:
            values.close()
            formulas.close()
    print(f"Independent receipt audit check: {count} raw cells, {len(expected)} sheets, two pinned source hashes verified")
    return count


if __name__ == "__main__":
    validate()
