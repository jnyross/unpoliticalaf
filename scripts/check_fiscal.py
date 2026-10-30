"""Independent fiscal boundary verification using original workbooks.

Does not import build_data, build_site or the audit reader. Expected series/units
are declarative contracts; numeric reads, transformations, derived arithmetic and
reconciliation residuals are checked here against separately reopened raw inputs.
This is software verification; independent fiscal review remains a factory gate.
"""
import hashlib
import json
import math
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils.cell import range_boundaries

from audit_scope import SHEETS, CATALOGUE_SHA256
from fiscal_contract import BASE, selections
from fiscal_schema import (STATUS, FORMULAE, DASH, metadata, value_id,
                           reconciliation_specs, partition, report_context)

ROOT = Path(__file__).resolve().parent.parent


class RawReader:
    def __init__(self, root=ROOT):
        manifest = root / "data/sources.json"
        if hashlib.sha256(manifest.read_bytes()).hexdigest() != CATALOGUE_SHA256:
            raise ValueError("Fiscal source catalogue hash changed")
        self.sources = json.loads(manifest.read_text())
        self.cells = {}
        for sid, sheets in SHEETS.items():
            source = self.sources[sid]
            path = root / source["file"]
            if any(p.is_symlink() for p in (path, *path.parents)) or hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
                raise ValueError("Fiscal source hash changed")
            book = load_workbook(path, read_only=True, data_only=True)
            formulas = load_workbook(path, read_only=True, data_only=False)
            try:
                for name, regions in sheets.items():
                    limits = [range_boundaries(region) for region in regions]
                    bounds = {"max_row": max(b[3] for b in limits), "max_col": max(b[2] for b in limits)}
                    fs = {c.coordinate: c for row in formulas[name].iter_rows(**bounds)
                          for c in row if hasattr(c, "coordinate")}
                    for row in book[name].iter_rows(**bounds):
                        for cell in row:
                            if not hasattr(cell, "coordinate"):
                                continue
                            formula = fs.get(cell.coordinate)
                            v = cell.value
                            self.cells[name + "!" + cell.coordinate] = {
                                "kind": "blank" if v is None else "number" if isinstance(v, (int, float)) and not isinstance(v, bool) else "text",
                                "value": v, "number_format": cell.number_format,
                                "formula": formula.value[1:] if formula is not None and formula.data_type == "f" else None}
                    self.cells[name + "!@sheet"] = {"kind": "text", "value": name, "number_format": None, "formula": None}
            finally:
                book.close()
                formulas.close()

    def __call__(self, ref):
        if ref not in self.cells:
            # EmptyCells have no coordinates; absent cells are explicit blanks.
            sheet, cell = ref.rsplit("!", 1)
            if sheet not in {s for sheets in SHEETS.values() for s in sheets} or not cell:
                raise ValueError("Unknown fiscal source locator")
            return {"kind": "blank", "value": None, "number_format": "General", "formula": None}
        return self.cells[ref]


def amount(reader, ref):
    cell = reader(ref)
    v = cell["value"]
    if v is None or isinstance(v, str) and v.strip() in ("", "-"):
        return None
    if isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v):
        raise ValueError("Independent fiscal operand must be finite numeric data")
    return float(v) / (1000 if ref.startswith("5_2!") else 1)


def same_number(actual, expected, what, tolerance=1e-9):
    if expected is None:
        if actual is not None:
            raise ValueError(f"Independent reconciliation failed: {what}: missing is not zero")
    elif isinstance(actual, bool) or not isinstance(actual, (int, float)) or not math.isfinite(actual) or abs(actual - expected) > tolerance:
        raise ValueError(f"Independent reconciliation failed: {what}: {actual} vs {expected}")


def check_reports(data, read):
    expected_specs = list(reconciliation_specs())
    reports = data["reconciliations"]
    if [r["id"] for r in reports] != [s[0] for s in expected_specs] + ["OBR-PESA-vintages"]:
        raise ValueError("Missing, duplicate or unexpected reconciliation")
    for report, (name, year, unit, terms, exclusions, basis) in zip(reports, expected_specs):
        refs = [ref for ref, _, _ in terms]
        partition([o["ref"] for o in report["operands"]])
        if [o["ref"] for o in report["operands"]] != refs:
            raise ValueError("Wrong or overlapping reconciliation source cells")
        values = [amount(read, ref) for ref in refs]
        missing = [ref for ref, v in zip(refs, values) if v is None]
        if missing and not name.startswith(("OBR-", "history-")):
            raise ValueError(f"Missing required fiscal reconciliation operands: {name}")
        context = report_context(name, year)
        if any(report.get(k) != v for k, v in context.items()):
            raise ValueError("Wrong reconciliation formula, geography or status")
        budget = sum(abs(coef) * quantum / 2 for _, coef, quantum in terms)
        residual = None if missing else math.fsum(coef * v for (_, coef, _), v in zip(terms, values))
        if residual is not None and abs(residual) > budget + 1e-9:
            raise ValueError(f"Independent reconciliation failed: {name}")
        for operand, (ref, coefficient, quantum), value in zip(report["operands"], terms, values):
            if set(operand) != {"ref", "coefficient", "value", "quantum"} or operand["coefficient"] != coefficient or operand["quantum"] != quantum:
                raise ValueError("Wrong reconciliation coefficients/quantisation")
            if quantum and value is not None and abs(value / quantum - round(value / quantum)) > 1e-6:
                raise ValueError("Independent source quantisation changed")
            same_number(operand["value"], value, ref)
        same_number(report["residual"], residual, name)
        same_number(report["quantisation_budget"], budget, name)
        if (report["period"] != year or report["unit"] != unit or report["basis"] != basis or
                report["numeric_epsilon"] != 1e-9 or report["excluded_refs"] != exclusions or
                report["missing_operands"] != missing or report["outcome"] !=
                ("not_testable_missing" if missing else "within_quantisation")):
            raise ValueError("Wrong reconciliation scope, exclusions or tolerance")
    cross = reports[-1]
    refs = ["Public finances since 1900!D132", "4_1!O46"]
    if cross["outcome"] != "not_comparable" or cross["quantisation_budget"] is not None or cross["numeric_epsilon"] is not None:
        raise ValueError("Cross-vintage proximity is not a source error bound")
    expected_cross = {"id": "OBR-PESA-vintages", "period": BASE, "unit": "percentage points",
        "operands": [{"ref": ref, "value": amount(read, ref)} for ref in refs],
        "residual": amount(read, refs[0]) - amount(read, refs[1]),
        "quantisation_budget": None, "numeric_epsilon": None, "outcome": "not_comparable",
        "missing_operands": [], "excluded_refs": [],
        "basis": "Different OBR/PESA vintages and GDP bases; no established source error bound. Difference shown, no pass/fail proximity claim."}
    expected_cross.update(report_context("OBR-PESA-vintages", BASE))
    if cross != expected_cross:
        raise ValueError("Incorrect cross-vintage residual or scope")


def check_derived(data, nodes):
    expected = {}
    def check(kind, a, b):
        aid, bid = a["value_id"], b["value_id"]
        key = kind + ":" + aid + ":" + bid
        av, bv = a["v"], b["v"]
        valid = av is not None and bv is not None and (bv != 0 if kind == "share" else av != 0)
        value = None
        if valid:
            value = av * 100 / bv if kind == "share" else (bv / av - 1) * 100
        pa, pb = data["provenance"][aid], data["provenance"][bid]
        expected[key] = {"v": value, "formula": kind, "operands": [aid, bid],
            "periods": [pa["period"], pb["period"]], "unit": "per 100 of TES" if kind == "share" else "percent change",
            "scale": 1, "geography": pa["geography"], "scope": [pa["scope"], pb["scope"]],
            "statuses": [pa["status"], pb["status"]], "basis": pa["basis"],
            "missingness": "present" if valid else "missing_or_zero_denominator"}
    whole = data["services_total"][BASE]
    for area in data["functions"]:
        check("share", area["series"][BASE]["nominal"], whole)
        for year in ("2015-16", "2005-06"):
            check("change", area["series"][year]["real"], area["series"][BASE]["real"])
    check("share", data["debt_interest"][BASE], whole)
    check("share", whole, whole)
    if set(data["derived"]) != set(expected):
        raise ValueError("Missing or unexpected derived fiscal values")
    for key, want in expected.items():
        got = dict(data["derived"][key])
        same_number(got.pop("v"), want.pop("v"), key)
        if got != want or any(op not in nodes for op in got["operands"]):
            raise ValueError("Wrong derived formula, operands or units")


def validate_fiscal(data, read=None):
    read = RawReader() if read is None else read
    if data.get("fiscal_schema_version") != 2:
        raise ValueError("Missing fiscal schema version")
    if (data["status_definitions"] != STATUS or data["formulae"] != FORMULAE or data["dash_semantics"] != DASH):
        raise ValueError("Changed fiscal status, formula or dash definitions")
    if data["sheet_sources"] != {sheet: sid for sid, sheets in SHEETS.items() for sheet in sheets}:
        raise ValueError("Changed source worksheet ownership")
    if hasattr(read, "sources") and data["sources"] != read.sources:
        raise ValueError("Fiscal source identity/publication/hash mismatch")
    expected_ids, expected_refs, nodes = set(), set(), {}
    leaf_objects = set()
    for node, contract in selections(data):
        ref, key = contract["ref"], value_id(contract)
        expected_ids.add(key)
        leaf_objects.add(id(node))
        if node.get("ref") != ref or node.get("value_id") != key:
            raise ValueError(f"Fiscal semantic cell mismatch: {key}")
        want = metadata(contract, read)
        if data["provenance"].get(key) != want:
            raise ValueError(f"Fiscal schema unit/status/scope/period mismatch: {key}")
        raw = amount(read, ref)
        if raw is None and contract["source_id"].startswith("pesa"):
            raise ValueError(f"Missing required fiscal value: {key}")
        if raw is not None:
            if ref.startswith("5_2!"):
                raw = round(raw, 3)
            if contract["precision"] is not None:
                raw = round(raw, contract["precision"])
        same_number(node["v"], raw, key)
        nodes[key] = node
        expected_refs.update([ref] + [v[0] for v in contract["identity"].values()] + want["status_refs"])
    if set(data["provenance"]) != expected_ids:
        raise ValueError("Missing or extra provenance records")
    def walk(obj):
        if isinstance(obj, dict):
            if "v" in obj and "ref" in obj and id(obj) not in leaf_objects:
                raise ValueError("Undeclared fiscal value outside semantic contract")
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)
    walk(data)
    check_reports(data, read)
    for report in data["reconciliations"]:
        expected_refs.update(o["ref"] for o in report["operands"])
        expected_refs.update(report["excluded_refs"])
        expected_refs.update(report["status_refs"])
    if set(data["source_cells"]) != expected_refs:
        raise ValueError("Missing or extra retained source operands")
    for ref, cell in data["source_cells"].items():
        original = read(ref)
        if set(cell) != {"kind", "value", "number_format", "formula"}:
            raise ValueError("Incomplete retained source cell")
        if cell["kind"] == "number":
            same_number(float(cell["value"]), original["value"], ref, tolerance=0)
            if original["kind"] != "number":
                raise ValueError("Wrong retained source kind")
        elif cell["kind"] == "text" and cell["value"] == "" and original["value"] is None:
            pass  # Empty inline strings preserved by XML, collapsed by openpyxl.
        elif cell["kind"] != original["kind"] or cell["value"] != original["value"]:
            raise ValueError(f"Changed retained raw value or missingness: {ref}")
        if cell["number_format"] != original["number_format"] or cell["formula"] != original["formula"]:
            raise ValueError(f"Changed retained formula/number format: {ref}")
    check_derived(data, nodes)
    return nodes
