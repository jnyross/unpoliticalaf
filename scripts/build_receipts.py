"""Build private receipt/debt data from the independently verified OBR evidence.

No receipt evidence is added to the public spending payload. The controller
runs this transformation and its separate raw-workbook checker in Boat.
"""
import csv
import json
import math
import re
from pathlib import Path

from check_receipt_audit import validate as validate_audit

ROOT = Path(__file__).resolve().parent.parent
YEAR = re.compile(r"^\d{4}-\d{2}$")
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


def columns(first, last):
    """Inclusive Excel columns, without inferring a fiscal grouping."""
    def index(value):
        result = 0
        for char in value:
            result = result * 26 + ord(char) - 64
        return result
    def label(value):
        result = ""
        while value:
            value, rem = divmod(value - 1, 26)
            result = chr(65 + rem) + result
        return result
    return [label(i) for i in range(index(first), index(last) + 1)]


def load_evidence(root):
    directory = root / "data/audit/receipts"
    index = json.loads((directory / "index.json").read_text())
    cells = {}
    for entry in index["sheets"]:
        with (directory / entry["file"]).open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream, delimiter="\t"):
                cells[entry["source_id"], entry["sheet"], row["cell"]] = {
                    "kind": row["kind"], "raw": json.loads(row["raw_value_json"]),
                    "format": entry["formats"][int(row["format_id"])],
                    "source_formula": json.loads(row["formula_json"]),
                }
    return cells


def numeric(cell):
    if cell["kind"] == "blank" or cell["kind"] == "text" and cell["raw"] in ("", "-"):
        return None
    if cell["kind"] != "number" or not isinstance(cell["raw"], str):
        raise ValueError("Receipt operand is neither numeric nor explicit missing data")
    value = float(cell["raw"])
    if not math.isfinite(value):
        raise ValueError("Non-finite receipt operand")
    return value


def context(historical, year, role, column):
    status = ("historical_status_uncertain" if historical else
              "forecast" if year >= "2026-27" else "outturn")
    geography = ("Great Britain" if year < "1800-01" else
                 "Great Britain and Ireland" if year < "1922-23" else "UK") if historical else "UK"
    if historical and year == "1800-01":
        geography = "Uncertain: Great Britain or Great Britain and Ireland"
    if historical and role in ("borrowing_flow", "debt_stock"):
        basis = "historical_basis_uncertain"
    elif role == "debt_stock":
        basis = "cash_stock"
    elif role == "gdp_denominator":
        basis = "march_centred" if column in ("AF", "F") else "financial_year"
    else:
        basis = "cash" if historical and role != "borrowing_flow" and year <= "1998-99" else "annual_accrual"
    return status, basis, geography


def scope(historical, year, role, column, receipts):
    if role == "gdp_denominator":
        return "whole_economy"
    if historical and role == "debt_stock":
        return "historical_scope_uncertain"
    if historical and role == "borrowing_flow" and year < "1900-01":
        return "central_government_proxy"
    if historical and receipts and column in ("U", "V"):
        return "central_government"
    if historical and receipts and column == "X":
        return "non_central_government"
    return "public_sector"


def receipt_role(column, historical):
    if historical:
        return ("subtotal" if column in ("B", "G", "P", "V") else
                "mixed_residual" if column in ("U", "X") else
                "receipts_total" if column == "Y" else
                "tax_total" if column == "Z" else "tax_component")
    return ("refund_component" if column == "D" else
            "non_tax_component" if column in ("AD", "AE") else
            "mixed_residual" if column == "AF" else
            "receipts_total" if column == "AG" else
            "tax_total" if column == "AH" else "tax_component")


def note_refs(kind, sheet):
    glossary = [("Glossary", "C" + str(r)) for r in (5, 6, 11, 14, 15)]
    if kind == "current_receipts":
        return [(sheet, "C" + str(r)) for r in (1, 40, 41, 42, 43)] + [x for x in glossary if x[1] != "C6"]
    if kind == "current_aggregates_cash":
        return [(sheet, c) for c in ("C1", "D7", "O7", "C94", "C95")] + glossary
    if kind == "current_aggregates_gdp":
        return [(sheet, "C" + str(r)) for r in (1, 89, 90, 91, 92)] + glossary
    rows = [4, 31, 62, 63, 64, 73, 74]
    own = []
    if "receipts" in kind:
        rows = [4, 31, *range(34, 44), 62, 63, 64, 73, 74]
        own = [(sheet, c) for c in ("B1", "B6", "G6", "P6", "U6", "X6",
                                    "B332", "C332", "D332", "E332", "F332", "I332")]
    return own + [("Contents", "D" + str(r)) for r in rows]


def specifications():
    yield "current_receipts", "obr_databank", "Receipts (£bn)", "GBP billion", "B", columns("C", "AH"), True
    yield "historical_receipts_cash", "obr_hist", "Receipts (£m)", "GBP million", "A", columns("B", "Z"), True
    yield "historical_receipts_gdp", "obr_hist", "Receipts (per cent of GDP)", "percent GDP", "A", columns("B", "Z"), True
    yield "current_aggregates_cash", "obr_databank", "Aggregates (£bn)", "GBP billion", "B", ["C", "D", "I", "O", "X", "AE", "AF"], False
    yield "current_aggregates_gdp", "obr_databank", "Aggregates (per cent of GDP)", "percent GDP", "B", ["C", "D", "I", "O", "X", "AE", "AF"], False
    yield "historical_aggregates_cash", "obr_hist", "Aggregates (£m)", "GBP million", "B", ["C", "D", "E", "F"], False
    yield "historical_aggregates_gdp", "obr_hist", "Aggregates (per cent of GDP)", "percent GDP", "B", ["C", "D", "E", "F"], False


def derived_specs(historical):
    if historical:
        return {
            "income_tax": [("C", 1)], "nic": [("D", 1)],
            "vat": [("Q", 1)], "corporation_tax": [("I", 1)],
            "other_taxes": [("Z", 1), ("C", -1), ("D", -1), ("Q", -1), ("I", -1)],
            "non_tax": [("Y", 1), ("Z", -1)],
        }
    return {
        "income_tax": [("Q", 1), ("R", 1), ("S", 1)], "nic": [("AB", 1)],
        "vat": [("C", 1), ("D", 1)], "corporation_tax": [("U", 1), ("V", 1)],
        "other_taxes": [("AH", 1), ("Q", -1), ("R", -1), ("S", -1), ("AB", -1),
                        ("C", -1), ("D", -1), ("U", -1), ("V", -1)],
        "non_tax": [("AG", 1), ("AH", -1)],
    }


def report_specs(kind):
    if kind == "current_receipts":
        return {"receipt_components": [(c, 1) for c in columns("C", "AF")] + [("AG", -1)]}
    if kind.startswith("current_aggregates"):
        return {"borrowing": [("D", 1), ("C", -1), ("O", -1)]}
    if kind.startswith("historical_receipts"):
        return {
            "personal": [(c, 1) for c in columns("C", "F")] + [("B", -1)],
            "business": [(c, 1) for c in columns("H", "O")] + [("G", -1)],
            "consumption": [(c, 1) for c in ("Q", "R", "S")] + [("P", -1)],
            "central": [(c, 1) for c in ("B", "G", "P", "T", "U")] + [("V", -1)],
            "public": [(c, 1) for c in ("V", "W", "X")] + [("Y", -1)],
        }
    return {}


def operands(table, terms, year):
    return [{"ref": table["series"][c]["values"][year]["ref"], "coefficient": coefficient}
            for c, coefficient in terms]


def arithmetic(table, terms, year):
    values = [(table["series"][c]["values"][year], coefficient) for c, coefficient in terms]
    missing = [v["ref"] for v, _ in values if v["v"] is None]
    if missing:
        return None, None, missing
    residual = math.fsum(v["v"] * coefficient for v, coefficient in values)
    # Chosen empirical binary64 storage/arithmetic allowance, not a bound
    # derived from the source's summation order or a fiscal/source tolerance.
    # Keep the factor fixed; never widen it to make an identity reconcile.
    budget = 4 * sum(abs(coefficient) * math.ulp(v["v"]) for v, coefficient in values)
    return residual, budget, []


def build_receipts(root=ROOT):
    validate_audit(root)
    evidence = load_evidence(root)
    catalogue = json.loads((root / "data/sources.json").read_text())
    data = {"schema_version": 1, "sources": {sid: catalogue[sid] for sid in ("obr_databank", "obr_hist")},
            "tables": {}, "limitations": LIMITATIONS.copy()}
    for kind, sid, sheet, unit, year_column, selected, receipts in specifications():
        historical = sid == "obr_hist"
        read = lambda coord: evidence[sid, sheet, coord]
        years = {}
        for (source, title, coord), cell in evidence.items():
            if source == sid and title == sheet and re.fullmatch(year_column + r"\d+", coord) and cell["kind"] == "text" and YEAR.fullmatch(cell["raw"]):
                if cell["raw"] in years:
                    raise ValueError("Duplicate receipt fiscal year")
                years[cell["raw"]] = int(re.search(r"\d+", coord).group())
        if not years:
            raise ValueError("Receipt table has no fiscal years")
        table = {"source_id": sid, "sheet": sheet, "unit": unit, "year_column": year_column,
                 "notes": {s + "!" + c: evidence[sid, s, c].copy() for s, c in note_refs(kind, sheet)},
                 "series": {}, "derived": {}, "reconciliations": []}
        for column in selected:
            header_row = 4 if receipts or not historical else 6
            code_row = 5 if receipts or not historical else 7
            label_ref = column + str(header_row)
            label = read(label_ref)
            if label["kind"] != "text" or not label["raw"]:
                raise ValueError("Missing receipt series identity")
            code_ref = None if kind == "current_aggregates_gdp" else column + str(code_row)
            role = receipt_role(column, historical) if receipts else (
                {"C": "borrowing_flow", "D": "debt_stock", "E": "gdp_denominator", "F": "gdp_denominator"} if historical else
                {"C": "receipts_total", "D": "spending_total", "I": "tax_total", "O": "borrowing_flow",
                 "X": "debt_stock", "AE": "gdp_denominator", "AF": "gdp_denominator"})[column]
            series_unit = ("GBP million" if historical else "GBP billion") if role == "gdp_denominator" else unit
            series = {"label": label["raw"], "label_ref": sheet + "!" + label_ref,
                      "code": read(code_ref)["raw"] if code_ref else None,
                      "code_ref": sheet + "!" + code_ref if code_ref else None,
                      "role": role, "unit": series_unit, "values": {}}
            for year, row in years.items():
                cell = read(column + str(row))
                status, basis, geography = context(historical, year, role, column)
                series["values"][year] = dict(cell, v=numeric(cell), ref=sheet + "!" + column + str(row),
                    year_ref=sheet + "!" + year_column + str(row), status=status, basis=basis, geography=geography,
                    scope=scope(historical, year, role, column, receipts))
                if historical and role == "debt_stock":
                    # D63 establishes this provenance split, not a basis or
                    # scope bridge. Do not borrow the current glossary.
                    series["values"][year]["source_regime"] = (
                        "Bank of England (2017)" if year < "1900-01" else "OBR (2023)")
            table["series"][column] = series
        if receipts:
            for name, terms in derived_specs(historical).items():
                table["derived"][name] = {}
                for year in years:
                    value, _, missing = arithmetic(table, terms, year)
                    status, basis, geography = context(historical, year, "tax_component", "")
                    table["derived"][name][year] = {
                        "v": value, "formula": "linear_combination", "operands": operands(table, terms, year),
                        "unit": unit, "status": status, "basis": basis, "geography": geography, "scope": "public_sector",
                        "missing_operands": missing,
                    }
        for name, terms in report_specs(kind).items():
            for year in years:
                residual, budget, missing = arithmetic(table, terms, year)
                outcome = ("not_testable_missing" if missing else "reconciled_storage_precision"
                           if abs(residual) <= budget else "unresolved_source_difference")
                if not historical and outcome == "unresolved_source_difference":
                    raise ValueError("Current OBR receipt/borrowing identity failed: " + year)
                table["reconciliations"].append({
                    "id": name, "year": year, "operands": operands(table, terms, year),
                    "residual": residual, "budget": budget, "outcome": outcome, "missing_operands": missing,
                    "explanation": ("Joined historical source identity; differences outside the chosen empirical storage arithmetic allowance remain unresolved."
                                    if historical else "Chosen empirical storage arithmetic allowance only; not a derived source error bound. Displayed formats are not source error bounds."),
                })
        data["tables"][kind] = table
    return data


def encode(data):
    return (json.dumps(data, indent=1, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
