"""Validate receipt source binding and arithmetic against retained OBR workbooks.

This checker does not import the receipt producer, audit exporter or mappings.
It reopens pinned workbooks with openpyxl, but transcribes the producer's fiscal
classification and context rules. It checks source cells and the implementation
of declared formulas, not whether those fiscal choices are justified. Residual
closures are not independent accuracy evidence. Separate fiscal review of the
pinned sources and populated calculations remains required.
"""
import hashlib
import json
import math
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils.cell import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
CATALOGUE_HASH = "5e7ebb343bee091960052b1727bf7bff6997216e8a5bf7805d18770aa7d5914a"
SOURCES = {
    "obr_databank": ("data/raw/OBR_Public_finances_databank_October_2026.xlsx",
                     "16a4bf46d8692e18790e87add342c6c44aa909cebb19f68ae857126a36d36459"),
    "obr_hist": ("data/raw/OBR_Historical_public_finances_database.xlsx",
                 "df154a4774807de330ad3b356db085c1d7adf4b1a4f7bcd13484ad9374f0e3f8"),
}

# These selections are independently transcribed from the raw-source audit
# evidence. In particular historic aggregates are two rows below receipts.
TABLES = {
    "current_receipts": ("obr_databank", "Receipts (£bn)", "GBP billion", "B",
                         1999, 2031, 7, list(range(3, 35)), 4, 5),
    "historical_receipts_cash": ("obr_hist", "Receipts (£m)", "GBP million", "A",
                                 1700, 2022, 7, list(range(2, 27)), 4, 5),
    "historical_receipts_gdp": ("obr_hist", "Receipts (per cent of GDP)", "percent GDP", "A",
                                1700, 2022, 7, list(range(2, 27)), 4, 5),
    "current_aggregates_cash": ("obr_databank", "Aggregates (£bn)", "GBP billion", "B",
                                1946, 2031, 8, [3, 4, 9, 15, 24, 31, 32], 4, 5),
    "current_aggregates_gdp": ("obr_databank", "Aggregates (per cent of GDP)", "percent GDP", "B",
                               1948, 2031, 5, [3, 4, 9, 15, 24, 31, 32], 4, None),
    "historical_aggregates_cash": ("obr_hist", "Aggregates (£m)", "GBP million", "B",
                                   1700, 2022, 9, [3, 4, 5, 6], 6, 7),
    "historical_aggregates_gdp": ("obr_hist", "Aggregates (per cent of GDP)", "percent GDP", "B",
                                  1700, 2022, 9, [3, 4, 5, 6], 6, 7),
}
GLOSSARY = ["Glossary!" + c for c in ["C5", "C6", "C11", "C14", "C15"]]
HISTORY = ["Contents!" + c for c in ["D4", "D31", "D62", "D63", "D64", "D73", "D74"]]
HISTORY_RECEIPTS = ["Contents!" + c for c in ["D4", "D31"] + ["D" + str(r) for r in range(34, 44)] + ["D62", "D63", "D64", "D73", "D74"]]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(value, expected, context):
    require(isinstance(value, dict) and set(value) == set(expected),
            f"{context}: unexpected or missing fields")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    def invalid(value):
        raise ValueError(f"Non-finite JSON constant: {value}")
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object,
                      parse_constant=invalid)


def digest(path):
    require(not any(p.is_symlink() for p in (path, *path.parents)), "Source/data path contains a symlink")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def same_number(actual, expected, context, tolerance=0):
    if expected is None:
        require(actual is None, f"{context}: missing value was replaced")
    else:
        require(numeric(actual) and abs(actual - expected) <= tolerance,
                f"{context}: numeric value mismatch ({actual!r} versus {expected!r})")


def year_name(start):
    return f"{start}-{(start + 1) % 100:02d}"


def context(tid, column, start):
    historical = tid.startswith("historical")
    status = "historical_status_uncertain" if historical else ("forecast" if start >= 2026 else "outturn")
    geography = ("Great Britain" if start < 1800 else "Uncertain: Great Britain or Great Britain and Ireland" if start == 1800 else "Great Britain and Ireland" if start <= 1921 else "UK") if historical else "UK"
    if "receipts" in tid:
        basis = "cash" if historical and start <= 1998 else "annual_accrual"
    elif historical and column in ("C", "D"):
        basis = "historical_basis_uncertain"
    elif not historical and column == "X":
        basis = "cash_stock"
    elif (historical and column in ("E", "F")) or (not historical and column in ("AE", "AF")):
        basis = "march_centred" if column in ("F", "AF") else "financial_year"
    else:
        basis = "annual_accrual"
    if role(tid, column) == "gdp_denominator":
        scope = "whole_economy"
    elif historical and "aggregates" in tid and column == "D":
        scope = "historical_scope_uncertain"
    elif historical and "aggregates" in tid and column == "C" and start < 1900:
        scope = "central_government_proxy"
    elif historical and "receipts" in tid and column in ("U", "V"):
        scope = "central_government"
    elif historical and "receipts" in tid and column == "X":
        scope = "non_central_government"
    else:
        scope = "public_sector"
    return {"status": status, "basis": basis, "geography": geography, "scope": scope}


def role(tid, col):
    if "receipts" in tid:
        if tid.startswith("current"):
            return {"D": "refund_component", "AD": "non_tax_component", "AE": "non_tax_component",
                    "AF": "mixed_residual", "AG": "receipts_total", "AH": "tax_total"}.get(col, "tax_component")
        return {"B": "subtotal", "G": "subtotal", "P": "subtotal", "V": "subtotal",
                "U": "mixed_residual", "X": "mixed_residual", "Y": "receipts_total",
                "Z": "tax_total"}.get(col, "tax_component")
    if tid.startswith("current"):
        return {"C": "receipts_total", "D": "spending_total", "I": "tax_total",
                "O": "borrowing_flow", "X": "debt_stock", "AE": "gdp_denominator",
                "AF": "gdp_denominator"}[col]
    return {"C": "borrowing_flow", "D": "debt_stock", "E": "gdp_denominator", "F": "gdp_denominator"}[col]


def series_unit(tid, col, unit):
    if tid == "current_aggregates_gdp" and col in ("AE", "AF"):
        return "GBP billion"
    if tid == "historical_aggregates_gdp" and col in ("E", "F"):
        return "GBP million"
    return unit


def note_refs(tid, sheet):
    if tid == "current_receipts":
        own = ["C1", "C40", "C41", "C42", "C43"]
        other = [r for r in GLOSSARY if r != "Glossary!C6"]
    elif tid == "current_aggregates_cash":
        own, other = ["C1", "D7", "O7", "C94", "C95"], GLOSSARY
    elif tid == "current_aggregates_gdp":
        own, other = ["C1", "C89", "C90", "C91", "C92"], GLOSSARY
    elif "receipts" in tid:
        own = ["B1", "B6", "G6", "P6", "U6", "X6", "B332", "C332", "D332", "E332", "F332", "I332"]
        other = HISTORY_RECEIPTS
    else:
        own, other = [], HISTORY
    return [sheet + "!" + c for c in own] + other


class Raw:
    def __init__(self, root):
        self.books = {}
        self.formulas = {}
        self.cache = {}
        try:
            for sid, (filename, expected_hash) in SOURCES.items():
                path = root / filename
                require(digest(path) == expected_hash, f"Pinned source hash mismatch: {sid}")
                self.books[sid] = load_workbook(path, read_only=True, data_only=True)
                self.formulas[sid] = load_workbook(path, read_only=True, data_only=False)
        except Exception:
            self.close()
            raise

    def close(self):
        for book in list(self.books.values()) + list(self.formulas.values()):
            book.close()

    def sheet(self, sid, name):
        key = sid, name
        if key not in self.cache:
            # Cache complete bounded source sheets once. Direct indexed access
            # repeatedly scans read-only XML and would make checks quadratic.
            if name == "Contents":
                bounds = {"max_row": 74, "max_col": 4}
            elif name == "Glossary":
                bounds = {"max_row": 24, "max_col": 5}
            elif sid == "obr_hist":
                bounds = {"max_row": 332, "max_col": 26 if name.startswith("Receipts") else 6}
            else:
                bounds = {"max_row": 106, "max_col": 34}
            values = {c.coordinate: c for row in self.books[sid][name].iter_rows(**bounds)
                      for c in row if hasattr(c, "coordinate")}
            formulas = {c.coordinate: c for row in self.formulas[sid][name].iter_rows(**bounds)
                        for c in row if hasattr(c, "coordinate")}
            self.cache[key] = values, formulas
        return self.cache[key]

    def cell(self, sid, ref):
        name, coordinate = ref.rsplit("!", 1)
        values, formulas = self.sheet(sid, name)
        cell, formula = values.get(coordinate), formulas.get(coordinate)
        value = cell.value if cell else None
        require(not cell or cell.data_type != "e", f"Excel error: {ref}")
        require(not formula or formula.data_type != "f", f"Unreviewed source formula: {ref}")
        # The pinned in-scope source cells are constants. A changed workbook
        # with formulas fails its hash before reaching this assertion.
        kind = "number" if numeric(value) else "blank" if value is None else "text"
        require(kind != "text" or isinstance(value, str), f"Unsupported source type: {ref}")
        return kind, value, cell.number_format if cell else "General", None

    def value(self, sid, ref):
        kind, value, _, _ = self.cell(sid, ref)
        return value if kind == "number" else None

    def check_cell(self, record, sid, ref):
        fields(record, {"kind", "raw", "format", "source_formula"}, ref)
        kind, value, number_format, formula = self.cell(sid, ref)
        require(record["kind"] == kind, f"{ref}: blank/dash/number kind changed")
        require(record["format"] == number_format, f"{ref}: source precision changed")
        require(record["source_formula"] == formula, f"{ref}: source formula changed")
        if kind == "number":
            require(isinstance(record["raw"], str), f"{ref}: raw number must retain a numeric string")
            try:
                decoded = float(record["raw"])
            except (ValueError, OverflowError) as exc:
                raise ValueError(f"{ref}: invalid raw number") from exc
            require(math.isfinite(decoded) and decoded == value, f"{ref}: raw value differs from workbook")
        else:
            require(record["raw"] == value, f"{ref}: raw text/missingness differs from workbook")
        return value if kind == "number" else None


def operands(sheet, row, specification):
    return [{"ref": f"{sheet}!{col}{row}", "coefficient": coefficient}
            for col, coefficient in specification]


def derived_specs(current):
    if current:
        return {
            "income_tax": [("Q", 1), ("R", 1), ("S", 1)],
            "nic": [("AB", 1)], "vat": [("C", 1), ("D", 1)],
            "corporation_tax": [("U", 1), ("V", 1)],
            "other_taxes": [("AH", 1), ("Q", -1), ("R", -1), ("S", -1), ("AB", -1), ("C", -1), ("D", -1), ("U", -1), ("V", -1)],
            "non_tax": [("AG", 1), ("AH", -1)],
        }
    return {
        "income_tax": [("C", 1)], "nic": [("D", 1)], "vat": [("Q", 1)],
        "corporation_tax": [("I", 1)],
        "other_taxes": [("Z", 1), ("C", -1), ("D", -1), ("Q", -1), ("I", -1)],
        "non_tax": [("Y", 1), ("Z", -1)],
    }


def linear(raw, sid, ops):
    missing = [o["ref"] for o in ops if raw.value(sid, o["ref"]) is None]
    result = None if missing else math.fsum(o["coefficient"] * raw.value(sid, o["ref"]) for o in ops)
    return result, missing


def check_operands(actual, expected, location):
    require(isinstance(actual, list) and len(actual) == len(expected), f"{location}: operand count changed")
    for a, e in zip(actual, expected):
        fields(a, {"ref", "coefficient"}, location)
        require(a["ref"] == e["ref"] and numeric(a["coefficient"]) and a["coefficient"] == e["coefficient"],
                f"{location}: wrong, duplicate or overlapping formula operand")


def check_historical_debt(record, raw, start):
    """Limit inference to the historical source note, outside context mapping.

    D63 names two suppliers only. Neither the PSND label nor the different
    workbook's cash definition establishes historical accounting or scope.
    This guard must still reject unsupported labels if context() is wrong too.
    It is a conservative evidence boundary, not independent fiscal approval.
    """
    note = raw.cell("obr_hist", "Contents!D63")[1]
    require(note == "2 PSND sourced from Bank of England (2017) from 1700-01 to 1899-00, then from OBR (2023) for 1900-01 onwards. ",
            "Historical debt source regime note changed")
    require(record["basis"] == "historical_basis_uncertain" and
            record["scope"] == "historical_scope_uncertain",
            "Historical debt basis/scope unsupported by Contents!D63")
    # Read the two supplier names from the reopened historical note, rather
    # than accepting a producer-supplied or rehashed provenance assignment.
    expected = note.split(" sourced from ", 1)[1].split(" from ", 1)[0] if start < 1900 else note.split("then from ", 1)[1].split(" for ", 1)[0]
    require(record["source_regime"] == expected,
            "Historical debt source regime disagrees with Contents!D63")


def validate(data=None, root=ROOT):
    root = Path(root)
    require(digest(root / "data/sources.json") == CATALOGUE_HASH, "Source catalogue hash changed")
    catalogue = read_json(root / "data/sources.json")
    if data is None:
        path = root / "data/receipts.json"
        digest(path)
        data = read_json(path)
    fields(data, {"schema_version", "sources", "tables", "limitations"}, "receipts root")
    require(type(data["schema_version"]) is int and data["schema_version"] == 1, "Receipt schema version changed")
    fields(data["sources"], SOURCES, "receipt sources")
    for sid in SOURCES:
        require(data["sources"][sid] == catalogue[sid], f"Source metadata changed: {sid}")
    fields(data["tables"], TABLES, "receipt tables")
    check_limitations(data["limitations"])
    raw = Raw(root)
    count = 0
    try:
        for tid, spec in TABLES.items():
            sid, sheet, unit, year_col, first, last, first_row, columns, label_row, code_row = spec
            table = data["tables"][tid]
            fields(table, {"source_id", "sheet", "unit", "year_column", "notes", "series", "derived", "reconciliations"}, tid)
            for key, expected in {"source_id": sid, "sheet": sheet, "unit": unit, "year_column": year_col}.items():
                require(table[key] == expected, f"{tid}: {key} changed")
            notes = note_refs(tid, sheet)
            fields(table["notes"], notes, f"{tid} notes")
            for ref in notes:
                raw.check_cell(table["notes"][ref], sid, ref)
            expected_columns = [get_column_letter(c) for c in columns]
            fields(table["series"], expected_columns, f"{tid} series")
            years = [year_name(start) for start in range(first, last + 1)]
            for col in expected_columns:
                series = table["series"][col]
                fields(series, {"unit", "label", "label_ref", "code", "code_ref", "role", "values"}, f"{tid}/{col}")
                label_ref = f"{sheet}!{col}{label_row}"
                code_ref = f"{sheet}!{col}{code_row}" if code_row is not None else None
                expected_label = raw.cell(sid, label_ref)[1]
                expected_code = raw.cell(sid, code_ref)[1] if code_ref else None
                for key, expected in {"label": expected_label, "label_ref": label_ref, "code": expected_code, "code_ref": code_ref,
                                      "role": role(tid, col), "unit": series_unit(tid, col, unit)}.items():
                    require(series[key] == expected, f"{tid}/{col}: {key} disagrees with independent source mapping")
                fields(series["values"], years, f"{tid}/{col} years")
                for start, year in zip(range(first, last + 1), years):
                    row = first_row + start - first
                    ref, year_ref = f"{sheet}!{col}{row}", f"{sheet}!{year_col}{row}"
                    require(raw.cell(sid, year_ref)[1] == year, f"{tid}: source fiscal-year alignment changed")
                    record = series["values"][year]
                    debt_history = tid.startswith("historical_aggregates") and col == "D"
                    expected_fields = {"v", "ref", "year_ref", "kind", "raw", "format", "source_formula", "status", "basis", "geography", "scope"}
                    if debt_history:
                        expected_fields.add("source_regime")
                    fields(record, expected_fields, f"{tid}/{col}/{year}")
                    require(record["ref"] == ref and record["year_ref"] == year_ref, f"{tid}/{col}/{year}: wrong source/year cell")
                    value = raw.check_cell({k: record[k] for k in ("kind", "raw", "format", "source_formula")}, sid, ref)
                    same_number(record["v"], value, ref)
                    for key, expected in context(tid, col, start).items():
                        require(record[key] == expected, f"{ref}: wrong {key}")
                    if debt_history:
                        check_historical_debt(record, raw, start)
                    count += 1
            specs = derived_specs(tid.startswith("current")) if "receipts" in tid else {}
            fields(table["derived"], specs, f"{tid} derived")
            for name, terms in specs.items():
                fields(table["derived"][name], years, f"{tid}/{name} derived years")
                for start, year in zip(range(first, last + 1), years):
                    record = table["derived"][name][year]
                    location = f"{tid}/{name}/{year}"
                    fields(record, {"v", "formula", "operands", "unit", "status", "basis", "geography", "scope", "missing_operands"}, location)
                    expected_ops = operands(sheet, first_row + start - first, terms)
                    check_operands(record["operands"], expected_ops, location)
                    value, missing = linear(raw, sid, expected_ops)
                    same_number(record["v"], value, location)
                    require(record["missing_operands"] == missing, f"{location}: missing operand list changed")
                    require(record["formula"] == "linear_combination" and record["unit"] == unit, f"{location}: formula/unit changed")
                    for key, expected in context(tid, "C", start).items():
                        require(record[key] == expected, f"{location}: wrong {key}")
            check_reconciliations(raw, tid, table, spec)
    finally:
        raw.close()
    print(f"Raw-source receipt product check: {count} source values, seven tables, pinned workbooks and declared formulas checked; fiscal review remains separate")
    return count


# Exact scope statements and report definitions are kept below, separate from
# source reading and direct/derived verification.
LIMITATIONS = [
    "Receipts are not all tax. Non-tax is the difference between PSCR and National Accounts taxes, not the mixed residual column.",
    "Other taxes are an explicit residual after named taxes; retained notes do not separately establish refund classification within National Accounts taxes.",
    "Historical receipts are cash through 1998-99 and accruals thereafter; do not splice vintages or compare across this break without a bridge.",
    "Historical central-government components can overlap licence fees before 1999-00 despite the U6 derivation; unresolved differences are retained, not assigned a rounding tolerance.",
    "In the October 2026 databank debt is a cash stock at end March, borrowing an annual accrual flow. Changes in debt need not equal borrowing.",
    "Debt shares use March-centred GDP; separately sourced published shares need not reproduce currency-unit stock ratios exactly. No discrepancy error bound is established.",
    "Historical actual/estimate status is uncertain. May 2023 series are not October 2026 forecasts; no next release date is established here.",
    "Historical borrowing uses a central-government proxy before 1900-01; the retained notes do not establish its accounting basis, so historical borrowing basis remains uncertain.",
    "Historical debt remains a stock with uncertain accounting basis and scope in both source regimes: Bank of England (2017) through 1899-00 and OBR (2023) from 1900-01, as named in Contents!D63. The October 2026 glossary is not evidence for this historical series.",
    "The historical geography note overlaps at 1800-01; that year is marked uncertain rather than choosing one boundary.",
]


def check_limitations(value):
    require(value == LIMITATIONS, "Receipt limitations changed or are missing")


def report_specs(tid):
    if tid == "current_receipts":
        return {"receipt_components": [(get_column_letter(c), 1) for c in range(3, 33)] + [("AG", -1)]}
    if "historical_receipts" in tid:
        return {
            "personal": [(c, 1) for c in ("C", "D", "E", "F")] + [("B", -1)],
            "business": [(c, 1) for c in ("H", "I", "J", "K", "L", "M", "N", "O")] + [("G", -1)],
            "consumption": [(c, 1) for c in ("Q", "R", "S")] + [("P", -1)],
            "central": [(c, 1) for c in ("B", "G", "P", "T", "U")] + [("V", -1)],
            "public": [(c, 1) for c in ("V", "W", "X")] + [("Y", -1)],
        }
    if tid.startswith("current_aggregates"):
        return {"borrowing": [("D", 1), ("C", -1), ("O", -1)]}
    return {}


def check_reconciliations(raw, tid, table, spec):
    sid, sheet, _, _, first, last, first_row, _, _, _ = spec
    reports = table["reconciliations"]
    require(isinstance(reports, list), f"{tid}: reconciliation reports must be a list")
    specs = report_specs(tid)
    expected = {(name, year_name(start)) for name in specs for start in range(first, last + 1)}
    observed = set()
    for report in reports:
        fields(report, {"id", "year", "operands", "residual", "budget", "outcome", "missing_operands", "explanation"},
               f"{tid} reconciliation")
        require(isinstance(report["id"], str) and isinstance(report["year"], str), f"{tid}: invalid report identity")
        key = report["id"], report["year"]
        require(key in expected and key not in observed, f"{tid}: duplicate or unknown reconciliation")
        observed.add(key)
        start = int(report["year"][:4])
        ops = operands(sheet, first_row + start - first, specs[report["id"]])
        location = f"{tid}/{report['id']}/{report['year']}"
        check_operands(report["operands"], ops, location)
        residual, missing = linear(raw, sid, ops)
        require(report["missing_operands"] == missing, f"{location}: reconciliation missing operands changed")
        if missing:
            budget, outcome = None, "not_testable_missing"
        else:
            # Fixed empirical allowance; not derived from source summation
            # order, display precision or an established source error bound.
            budget = 4 * sum(abs(o["coefficient"]) * math.ulp(float(raw.value(sid, o["ref"]))) for o in ops)
            if abs(residual) <= budget:
                outcome = "reconciled_storage_precision"
            else:
                require(not tid.startswith("current"), f"{location}: current source identity fails")
                outcome = "unresolved_source_difference"
        same_number(report["residual"], residual, location + " residual")
        same_number(report["budget"], budget, location + " storage arithmetic allowance")
        require(report["outcome"] == outcome, f"{location}: reconciliation outcome changed")
        explanation = ("Joined historical source identity; differences outside the chosen empirical storage arithmetic allowance remain unresolved."
                       if tid.startswith("historical") else
                       "Chosen empirical storage arithmetic allowance only; not a derived source error bound. Displayed formats are not source error bounds.")
        require(report["explanation"] == explanation, f"{location}: reconciliation explanation changed")
    require(observed == expected, f"{tid}: reconciliation report omitted")



if __name__ == "__main__":
    validate()
