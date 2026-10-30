"""Independent fiscal boundary verification using original workbooks.

Does not import build_data, build_site or the audit reader. Expected series/units
are declarative contracts; numeric reads, transformations, derived arithmetic and
reconciliation residuals are checked here against separately reopened raw inputs.
This is software verification; independent fiscal review remains a factory gate.
"""
import hashlib
import json
import math
import re
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils.cell import range_boundaries

from audit_scope import SHEETS, CATALOGUE_SHA256
from fiscal_contract import BASE, YEARS, FUNCTION_ROWS, selections
# Shared declarative policy, never producer functions or computed expectations.
from fiscal_schema import STATUS, FORMULAE, DASH

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


def source_metadata(contract, read):
    """Verify semantic roles directly, independently of producer metadata()."""
    def text(value):
        value = re.sub(r"\s*\(\d+\)(,\s*\(\d+\))*", "", str(value).replace("\u00a0", " "))
        return " ".join(value.split())
    for role, (ref, label) in contract["identity"].items():
        if text(read(ref)["value"]) != text(label):
            raise ValueError(f"Independent fiscal semantic {role} mismatch: {ref}")
    sheet = contract["ref"].split("!")[0]
    year = contract["period"]
    if sheet == "4_1":
        boundary = re.search(r"up to (\d{4}-\d{2})", read("4_1!B3")["value"]).group(1)
        status = "pesa_forecast" if year > boundary else "pesa_outturn"
        refs = [f"4_1!B{r}" for r in (3, 51, 52, 53)]
    elif sheet == "5_2":
        if read("5_2!G6")["value"] != "outturn":
            raise ValueError("Independent PESA outturn header changed")
        status, refs = "pesa_outturn", [f"5_2!{c}" for c in ("G6", "B137", "B138", "B147")]
    elif sheet.startswith("4_"):
        if read(sheet + "!B4")["value"] != "outturn":
            raise ValueError("Independent PESA outturn header changed")
        status, refs = "pesa_outturn", [sheet + "!B4", sheet + "!A1"]
        if sheet in ("4_3", "4_4"):
            refs.append(sheet + "!A28")
    elif sheet == "Public finances since 1900":
        status = "obr_databank_historical"
        early_end = "1973-74" if contract["series"] == "history.totals.debt" else "1945-46"
        refs = [sheet + "!" + c for c in ("B2", "B139", "B142" if year <= early_end else "B143",
                "B146" if year <= "1947-48" else "B147", "B144", "B148")]
    else:
        status = "obr_extrapolated" if year == "2022-23" and contract["note"] != "D57" else "obr_joined_historical"
        refs = ["Contents!" + c for c in ("D4", "D31", "D46", contract["note"], "D64")]
    if any(read(ref)["kind"] != "text" for ref in refs):
        raise ValueError("Missing independent fiscal status evidence")
    cell = read(contract["ref"])
    state = ("blank" if cell["kind"] == "blank" else
             "literal_dash" if isinstance(cell["value"], str) and cell["value"].strip() == "-" else
             "empty_text" if isinstance(cell["value"], str) and not cell["value"].strip() else "present")
    return {key: contract[key] for key in ("ref", "source_id", "period", "series", "unit", "scale",
            "geography", "scope", "basis", "precision", "identity")} | {
        "status": status, "status_refs": refs, "missingness": state,
        "formula": "source", "operands": [contract["ref"]]}


def independent_specs(read):
    """Locate reconciliation operands by raw labels/periods, not producer specs.

    Numeric expectations use the raw reader below. Header and period lookups make
    even an equal-valued wrong row/column in the producer's ledger detectable.
    """
    def locate(sheet, column, label, rows):
        matches = [r for r in rows if re.sub(r"\(\d+\)", "", str(read(f"{sheet}!{column}{r}")["value"])).strip() == label]
        if len(matches) != 1:
            raise ValueError(f"Independent reconciliation identity missing/duplicate: {sheet} {label}")
        return matches[0]
    def year_column(sheet, year, first, last):
        matches = [chr(c) for c in range(ord(first), ord(last) + 1)
                   if read(f"{sheet}!{chr(c)}5")["value"] == year]
        if len(matches) != 1:
            raise ValueError("Independent reconciliation period missing/duplicate")
        return matches[0]
    def ch4(label, year, sheet="4_2"):
        row = locate(sheet, "A", label, range(6, 28))
        return f"{sheet}!{year_column(sheet, year, 'B', 'X')}{row}"
    labels = [label for _, label in FUNCTION_ROWS.values()]
    for year in YEARS:
        ar = locate("4_1", "B", year, range(6, 50))
        yield (f"functions/{year}", year, "GBP billion",
            [(ch4(label, year), 1, .1) for label in labels] + [(ch4("Public sector expenditure on services", year), -1, .1)],
            [], "TES functions; excludes all of-which subcategories and accounting adjustments")
        yield (f"services-to-TME/{year}", year, "GBP billion",
            [(ch4(label, year), coefficient, .1) for label, coefficient in
             (("Public sector expenditure on services", 1), ("Accounting adjustments", 1), ("Total Managed Expenditure", -1))],
            [], "TES plus separately retained accounting adjustments; excludes temporary bank-classification effects (4_2 A35)")
        yield (f"TME-tables/{year}", year, "GBP billion",
            [(ch4("Total Managed Expenditure", year), 1, .1), (f"4_1!M{ar}", -1, .1)],
            [], "Same PESA TME basis, Tables 4.1 and 4.2")
    for key, (_, label) in FUNCTION_ROWS.items():
        yield (f"base-price/{key}", BASE, "GBP billion",
            [(ch4(label, BASE), 1, .1), (ch4(label, BASE, "4_3"), -1, .1)], [],
            "Same nominal and real price base; 4_3 A28")
    ar = locate("4_1", "B", BASE, range(6, 50))
    for key, nominal, real in (("current", "C", "D"), ("investment", "I", "J"), ("tme", "M", "N")):
        yield (f"aggregate-base/{key}", BASE, "GBP billion",
            [(f"4_1!{nominal}{ar}", 1, .1), (f"4_1!{real}{ar}", -1, .1)], [], "Same price base; 4_1 B51")
    # Chapter 5 has explicit total labels, rather than Chapter 4's headings.
    for key, (_, label) in FUNCTION_ROWS.items():
        target = "Total " + label.split(". ", 1)[-1]
        candidates = [r for r in range(7, 131) if
                      str(read(f"5_2!B{r}")["value"]).casefold() == target.casefold()]
        if len(candidates) != 1:
            raise ValueError(f"Independent Chapter 5 function identity: {target}")
        for start in range(2021, 2026):
            year = f"{start}-{(start + 1) % 100:02d}"
            ref5 = f"5_2!{year_column('5_2', year, 'C', 'G')}{candidates[0]}"
            yield (f"detail-total/{key}/{year}", year, "GBP billion",
                [(ref5, 1, .001), (ch4(label, year), -1, .1)], [],
                "PESA same-function totals, integer £million versus 0.1 £billion")
    yield ("debt-components", BASE, "GBP billion",
        [(f"5_2!G{r}", 1, .001) for r in range(15, 20)] + [("5_2!G14", -1, .001)], [],
        "Public debt transactions, including Bank of England and pension items; 5_2 B137:B138")
    yield ("debt-tables", BASE, "GBP billion", [("5_2!G14", 1, .001), (ch4("of which: public sector debt interest", BASE), -1, .1)], [],
        "Public debt transactions versus PESA debt-interest line")
    sheet = "Public finances since 1900"
    for row in range(7, 139):
        year = read(f"{sheet}!B{row}")["value"]
        yield (f"OBR-borrowing/{year}", year, "percentage points",
            [(f"{sheet}!{c}{row}", coef, 0) for c, coef in (("D", 1), ("C", -1), ("E", -1))], [],
            "Stored unrounded ratios; no filling of missing borrowing")
    sheet = "Spending (per cent of GDP)"
    # Derivations are source text, not formulas invented by the implementation.
    if read(sheet + "!E6")["value"] != "d-f" or read(sheet + "!N6")["value"] != "d-g-h-i-l-m":
        raise ValueError("Independent historical source derivation changed")
    for row in range(7, 330):
        year = read(f"{sheet}!B{row}")["value"]
        yield (f"history-current/{year}", year, "percentage points",
            [(f"{sheet}!{c}{row}", coef, 0) for c, coef in (("E", 1), ("F", 1), ("D", -1))], [],
            "Stored identity E=D-F; E6 and Contents D49; missing investment is not zero")
        yield (f"history-functions/{year}", year, "percentage points",
            [(f"{sheet}!{c}{row}", 1, 0) for c in ("G", "H", "I", "L", "M", "N")] + [(f"{sheet}!D{row}", -1, 0)],
            [f"{sheet}!J{row}", f"{sheet}!K{row}"],
            "Other is a SOURCE residual (N6, Contents D58), not an independent total check; pensioner subsets J/K excluded")


def independent_context(name, year):
    if name == "OBR-PESA-vintages":
        statuses, geography = ["obr_databank_historical", "pesa_outturn"], "UK"
        refs = ["Public finances since 1900!" + c for c in ("B2", "B139", "B143", "B147", "B144", "B148")] + ["4_1!B3"]
    elif name.startswith("history-"):
        geography = "Great Britain" if year < "1800-01" else "historical boundary uncertain" if year == "1800-01" else "Great Britain and Ireland" if year < "1922-23" else "UK"
        statuses = ["obr_joined_historical"]
        if name.startswith("history-functions/") and year == "2022-23":
            statuses.append("obr_extrapolated")
        refs = ["Contents!" + c for c in ("D31", "D48", "D49", "D50", "D51", "D52", "D53", "D56", "D57", "D58", "D64")]
        refs.append("Spending (per cent of GDP)!" + ("E6" if name.startswith("history-current/") else "N6"))
    elif name.startswith("OBR-"):
        geography = "UK" if year >= "1922-23" else "historical UK incl. Ireland"
        statuses = ["obr_databank_forecast" if year > BASE else "obr_databank_historical"]
        refs = ["Public finances since 1900!" + c for c in ("B2", "B139", "B142", "B143", "B144", "B146", "B147", "B148")]
    else:
        geography, statuses = "UK", ["pesa_outturn"]
        refs = ["4_1!B3", "4_1!B51", "4_1!B52", "5_2!G6"]
    return {"formula": "signed_sum", "geography": geography, "statuses": statuses, "status_refs": refs}


def check_reports(data, read):
    expected_specs = list(independent_specs(read))
    reports = data["reconciliations"]
    if [r["id"] for r in reports] != [s[0] for s in expected_specs] + ["OBR-PESA-vintages"]:
        raise ValueError("Missing, duplicate or unexpected reconciliation")
    for report, (name, year, unit, terms, exclusions, basis) in zip(reports, expected_specs):
        refs = [ref for ref, _, _ in terms]
        if len({o["ref"] for o in report["operands"]}) != len(report["operands"]):
            raise ValueError("Duplicate or overlapping reconciliation operands")
        if [o["ref"] for o in report["operands"]] != refs:
            raise ValueError("Wrong or overlapping reconciliation source cells")
        values = [amount(read, ref) for ref in refs]
        missing = [ref for ref, v in zip(refs, values) if v is None]
        if missing and not name.startswith(("OBR-", "history-")):
            raise ValueError(f"Missing required fiscal reconciliation operands: {name}")
        context = independent_context(name, year)
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
    expected_cross.update(independent_context("OBR-PESA-vintages", BASE))
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
        ref, key = contract["ref"], contract["series"] + "/" + contract["period"]
        expected_ids.add(key)
        leaf_objects.add(id(node))
        if node.get("ref") != ref or node.get("value_id") != key:
            raise ValueError(f"Fiscal semantic cell mismatch: {key}")
        want = source_metadata(contract, read)
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
