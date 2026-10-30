"""Audit-cell and fiscal-schema corruption tests against reopened raw sources."""
import copy
import csv
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from audit_scope import SHEETS, filename
from check_audit import validate
from build_data import grid, pesa_context, aggregates
from check_site import cells, independent_data_checks
from check_fiscal import RawReader, validate_fiscal, check_reports
from fiscal_schema import missingness, numeric, partition
import build_site


class AuditEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "data", self.root / "data")

    def index(self):
        return json.loads((self.root / "data/audit/index.json").read_text())

    def save_index(self, index):
        (self.root / "data/audit/index.json").write_text(json.dumps(index))

    def change_extract(self, sheet, change):
        index = self.index()
        entry = next(e for e in index["sheets"] if e["sheet"] == sheet)
        path = self.root / "data/audit" / entry["file"]
        with path.open(newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            fields, rows = reader.fieldnames, list(reader)
        change(rows, entry)
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fields, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        # Rehash too: mutations must be caught by reopening raw data, rather than
        # passing because author-controlled extracts and their hashes agree.
        entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.save_index(index)

    def test_all_scoped_evidence_matches_independently_reopened_workbooks(self):
        self.assertGreater(validate(self.root), 5000)

    def test_changed_raw_hash_rejected(self):
        with (self.root / "data/raw/PESA_2026_CP_Chapter_4_tables.xlsx").open("ab") as stream:
            stream.write(b"changed")
        with self.assertRaisesRegex(ValueError, "Source hash mismatch"):
            validate(self.root)

    def test_changed_pinned_manifest_rejected(self):
        with (self.root / "data/audit/pinned-source.json").open("ab") as stream:
            stream.write(b" ")
        with self.assertRaisesRegex(ValueError, "manifest/catalogue hash changed"):
            validate(self.root)

    def test_changed_extract_hash_rejected(self):
        path = self.root / "data/audit" / filename("pesa_ch4", "4_1")
        path.write_text(path.read_text() + "changed\n")
        with self.assertRaisesRegex(ValueError, "extract hash mismatch"):
            validate(self.root)

    def test_wrong_cell_and_duplicate_cell_rejected(self):
        self.change_extract("4_1", lambda rows, _: rows[1].update(cell=rows[0]["cell"]))
        with self.assertRaisesRegex(ValueError, "missing, duplicate or wrong cell"):
            validate(self.root)

    def test_wrong_unit_rejected_even_after_rehash(self):
        def change(rows, _):
            next(r for r in rows if r["cell"] == "C5")["raw_value_json"] = json.dumps("Nominal\n£ million")
        self.change_extract("4_1", change)
        with self.assertRaisesRegex(ValueError, "text/label/unit mismatch"):
            validate(self.root)

    def test_missing_is_not_zero_even_after_rehash(self):
        def change(rows, _):
            next(r for r in rows if r["cell"] == "C1").update(kind="number", raw_value_json='"0"')
        self.change_extract("4_1", change)
        with self.assertRaisesRegex(ValueError, "numeric cell mismatch"):
            validate(self.root)

    def test_dash_is_retained_literally(self):
        def change(rows, _):
            next(r for r in rows if r["cell"] == "G11").update(kind="blank", raw_value_json="null")
        self.change_extract("5_2", change)
        with self.assertRaisesRegex(ValueError, "missing value mismatch"):
            validate(self.root)

    def test_lost_numeric_value_rejected_even_after_rehash(self):
        def change(rows, _):
            next(r for r in rows if r["cell"] == "M6").update(kind="blank", raw_value_json="null")
        self.change_extract("4_1", change)
        with self.assertRaisesRegex(ValueError, "missing value mismatch"):
            validate(self.root)

    def test_changed_formula_rejected_even_after_rehash(self):
        def change(rows, _):
            next(r for r in rows if r["cell"] == "M6")["formula_json"] = json.dumps("1+1")
        self.change_extract("4_1", change)
        with self.assertRaisesRegex(ValueError, "formula mismatch"):
            validate(self.root)

    def test_wrong_precision_rejected_even_after_rehash(self):
        def change(rows, entry):
            entry["formats"].append("0.000000")
            next(r for r in rows if r["cell"] == "M6")["format_id"] = str(len(entry["formats"]) - 1)
        self.change_extract("4_1", change)
        with self.assertRaisesRegex(ValueError, "source precision mismatch"):
            validate(self.root)

    def test_missing_or_duplicate_sheet_rejected(self):
        index = self.index()
        index["sheets"][1] = copy.deepcopy(index["sheets"][0])
        self.save_index(index)
        with self.assertRaisesRegex(ValueError, "Missing or duplicate audit sheet"):
            validate(self.root)

    def test_expanded_or_overlapping_scope_rejected(self):
        index = self.index()
        index["sheets"][0]["ranges"].append("B1:O53")
        self.save_index(index)
        with self.assertRaisesRegex(ValueError, "selection mismatch"):
            validate(self.root)

    def test_all_generated_value_refs_have_readable_audit_cells(self):
        available = set()
        for sid, sheets in SHEETS.items():
            for sheet in sheets:
                with (self.root / "data/audit" / filename(sid, sheet)).open(newline="") as stream:
                    available.update(sheet + "!" + r["cell"] for r in csv.DictReader(stream, delimiter="\t"))
        def walk(value):
            if isinstance(value, dict):
                if "v" in value and "ref" in value:
                    self.assertIn(value["ref"], available)
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        walk(json.loads((ROOT / "data/spending.json").read_text()))


class PesaNoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = grid(ROOT / "data/raw/PESA_2026_CP_Chapter_4_tables.xlsx", "4_1")

    def test_notes_drive_forecast_and_price_context(self):
        context = pesa_context(self.rows)
        self.assertEqual(context, {"last_outturn": "2025-26", "status_ref": "4_1!B3",
            "forecast_date": "3 March 2026", "forecast_ref": "4_1!B52",
            "deflator_ref": "4_1!B51", "base_year": "2025-26"})
        for row in aggregates(self.rows):
            self.assertEqual(row["forecast"], row["year"] > context["last_outturn"])

    def test_changed_boundary_or_conflicting_date_rejected(self):
        for index, old, new in ((2, "2025-26", "2024-25"), (51, "3 March 2026", "1 April 2026")):
            rows = copy.deepcopy(self.rows)
            rows[index][1] = rows[index][1].replace(old, new)
            with self.assertRaises(ValueError):
                pesa_context(rows)

    def test_independent_checker_rejects_changed_context(self):
        data = json.loads((ROOT / "data/spending.json").read_text())
        data["pesa_context"]["forecast_date"] = "1 April 2026"
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            (site / "data").mkdir()
            (site / "data/spending.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "Independent PESA status/vintage"):
                independent_data_checks(site, cells())

    def test_caption_and_total_years_follow_data(self):
        data = json.loads((ROOT / "data/spending.json").read_text())
        build_site.configure(data)
        self.assertNotIn("Largest items", build_site.section_items())
        self.assertIn("Selected items", build_site.section_items())
        data["aggregates"] = data["aggregates"][1:-1]
        build_site.configure(data)
        section = build_site.section_total()
        first, last = data["aggregates"][0]["year"], data["aggregates"][-1]["year"]
        self.assertIn(f"Total spending since {first[:4]}", section)
        self.assertIn(f"Total Managed Expenditure, {first} to {last}", section)


class FiscalBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The controller builds the exact candidate before running verification.
        cls.original = json.loads((ROOT / "data/spending.json").read_text())
        cls.read = RawReader()

    def setUp(self):
        self.data = copy.deepcopy(self.original)

    def check(self):
        return validate_fiscal(self.data, self.read)

    def test_complete_semantic_schema_against_independent_workbooks(self):
        self.assertGreater(len(self.check()), 900)
        for record in self.data["provenance"].values():
            source = self.data["sources"][record["source_id"]]
            self.assertEqual(len(source["sha256"]), 64)
            for field in ("file", "publication", "published", "downloaded"):
                self.assertTrue(source[field])
            for field in ("period", "unit", "scale", "geography", "scope", "status", "identity", "formula", "operands"):
                self.assertIsNotNone(record[field])

    def test_equal_valued_wrong_semantic_cell_is_rejected(self):
        area = next(a for a in self.data["functions"] if a["id"] == "health")
        row = area["series"]["2025-26"]
        self.assertEqual(row["nominal"]["v"], row["real"]["v"])
        # Equal numbers and an otherwise valid source cell cannot establish the
        # claimed cash/real identity. Keep the figure's declared role unchanged.
        row["nominal"]["ref"] = row["real"]["ref"]
        with self.assertRaisesRegex(ValueError, "semantic cell mismatch"):
            self.check()

    def test_wrong_unit_scale_scope_status_and_period_are_rejected(self):
        key = next(a for a in self.data["functions"] if a["id"] == "health")["series"]["2025-26"]["nominal"]["value_id"]
        for field, wrong in (("unit", "GBP million"), ("scale", 1000), ("scope", "TME"),
                             ("period", "2024-25"), ("status", "pesa_forecast"), ("geography", "England")):
            with self.subTest(field=field):
                data = copy.deepcopy(self.original)
                data["provenance"][key][field] = wrong
                with self.assertRaisesRegex(ValueError, "unit/status/scope/period mismatch"):
                    validate_fiscal(data, self.read)

    def test_missing_required_value_and_missing_period_are_rejected(self):
        y = self.data["latest_year"]
        self.data["services_total"][y]["v"] = None
        with self.assertRaisesRegex(ValueError, "Independent reconciliation failed"):
            self.check()
        self.data = copy.deepcopy(self.original)
        del self.data["services_total"][y]
        with self.assertRaisesRegex(ValueError, "missing or extra"):
            self.check()

    def test_required_source_missingness_is_not_silently_skipped(self):
        target = self.data["services_total"][self.data["latest_year"]]["ref"]
        def missing(ref):
            if ref == target:
                return dict(self.read(ref), kind="blank", value=None)
            return self.read(ref)
        with self.assertRaisesRegex(ValueError, "schema unit/status/scope/period mismatch|Missing required fiscal value"):
            validate_fiscal(self.data, missing)

    def test_changed_finite_value_and_lost_source_identity_are_rejected(self):
        self.data["services_total"]["2025-26"]["v"] += 1
        with self.assertRaisesRegex(ValueError, "Independent reconciliation failed"):
            self.check()
        self.data = copy.deepcopy(self.original)
        self.data["sources"]["pesa_ch4"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source identity/publication/hash mismatch"):
            self.check()

    def test_duplicate_categories_and_parent_total_in_function_partition_are_rejected(self):
        self.data["functions"][1] = copy.deepcopy(self.data["functions"][0])
        with self.assertRaisesRegex(ValueError, "missing, duplicate or overlapping"):
            self.check()
        self.data = copy.deepcopy(self.original)
        self.data["functions"].append({"id": "services_total", "series": self.data["services_total"]})
        with self.assertRaisesRegex(ValueError, "missing, duplicate or overlapping"):
            self.check()
        with self.assertRaisesRegex(ValueError, "Overlapping"):
            partition(["4_2!X20", "5_2!G76"])

    def test_missing_or_duplicate_selected_items_are_rejected(self):
        self.data["details"].pop()
        with self.assertRaisesRegex(ValueError, "missing, duplicate or overlapping"):
            self.check()
        self.data = copy.deepcopy(self.original)
        self.data["details"].append(copy.deepcopy(self.data["details"][0]))
        with self.assertRaisesRegex(ValueError, "missing, duplicate or overlapping"):
            self.check()

    def test_broken_reconciliation_cannot_be_hidden_with_a_zero_residual(self):
        # Alter the raw reader at the fiscal boundary, retaining a valid .1 grid.
        # The independently recomputed sum must fail even if a report claims 0.
        def changed(ref):
            cell = self.read(ref)
            return dict(cell, value=cell["value"] + 2) if ref == "4_2!B20" else cell
        with self.assertRaisesRegex(ValueError, "Independent reconciliation failed"):
            check_reports(self.data, changed)

    def test_overlapping_and_duplicated_report_operands_are_rejected(self):
        report = self.data["reconciliations"][0]
        report["operands"].append(copy.deepcopy(report["operands"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate or overlapping"):
            self.check()
        self.data = copy.deepcopy(self.original)
        self.data["reconciliations"][0]["operands"].append(
            {"ref": "5_2!G76", "coefficient": 1, "value": 247.4, "quantum": 0.001})
        with self.assertRaisesRegex(ValueError, "Wrong or overlapping|Overlapping"):
            self.check()

    def test_source_rounding_budget_and_cross_vintage_difference_cannot_be_relabelled(self):
        self.data["reconciliations"][0]["quantisation_budget"] = 1
        with self.assertRaisesRegex(ValueError, "Independent reconciliation failed"):
            self.check()
        self.data = copy.deepcopy(self.original)
        self.data["reconciliations"][-1]["quantisation_budget"] = 0.5
        with self.assertRaisesRegex(ValueError, "not a source error bound"):
            self.check()

    def test_derived_values_bind_ordered_operands_and_formula(self):
        key = next(k for k, d in self.data["derived"].items()
                   if d["formula"] == "share" and d["operands"][0] != d["operands"][1])
        self.data["derived"][key]["operands"].reverse()
        with self.assertRaisesRegex(ValueError, "Wrong derived formula"):
            self.check()
        self.data = copy.deepcopy(self.original)
        self.data["derived"][key]["v"] += 1
        with self.assertRaisesRegex(ValueError, "Independent reconciliation failed"):
            self.check()

    def test_missing_dash_zero_and_source_format_are_distinct(self):
        self.assertEqual(missingness({"kind": "text", "value": "-"}), "literal_dash")
        self.assertEqual(missingness({"kind": "blank", "value": None}), "blank")
        self.assertEqual(missingness({"kind": "number", "value": "0"}), "present")
        self.assertIsNone(numeric({"kind": "text", "value": "-"}))
        self.assertEqual(numeric({"kind": "number", "value": "0"}), 0)
        self.assertEqual(self.read("5_2!G11")["value"], "-")
        missing = next(r for r in self.data["reconciliations"] if r["id"] == "OBR-borrowing/1975-76")
        self.assertEqual(missing["outcome"], "not_testable_missing")
        self.assertIsNone(missing["residual"])
        self.assertIn("Public finances since 1900!E82", missing["missing_operands"])

    def test_obr_conflicts_and_series_specific_updates_are_retained(self):
        p = self.data["provenance"]
        debt = p["history.totals.debt/1965-66"]
        spending = p["history.totals.spending/1965-66"]
        self.assertEqual(self.data["status_definitions"][debt["status"]]["kind"], "uncertain")
        self.assertIn("Public finances since 1900!B142", debt["status_refs"])
        self.assertIn("Public finances since 1900!B143", spending["status_refs"])
        for cell in ("B2", "B139", "B144", "B148"):
            self.assertIn("Public finances since 1900!" + cell, debt["status_refs"])
        self.assertEqual(max(self.data["history"]["areas"][0]["values"]), "2015-16")
        self.assertEqual(self.data["status_definitions"]["obr_extrapolated"]["kind"], "estimate")

    def test_retained_missing_value_and_raw_unit_cannot_be_fabricated(self):
        cell = self.data["source_cells"]["Public finances since 1900!E82"]
        cell.update(kind="number", value="0")
        with self.assertRaisesRegex(ValueError, "Independent reconciliation failed|Wrong retained source kind"):
            self.check()
        self.data = copy.deepcopy(self.original)
        self.data["source_cells"]["4_2!X3"]["value"] = "£ million"
        with self.assertRaisesRegex(ValueError, "Changed retained raw value"):
            self.check()


if __name__ == "__main__":
    unittest.main()
