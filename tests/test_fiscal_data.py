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
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from audit_scope import SHEETS, filename
from check_audit import validate
from build_data import grid, pesa_context, aggregates
from check_site import cells, independent_data_checks
from check_fiscal import RawReader, validate_fiscal, check_reports
from fiscal_schema import missingness, numeric, partition, enrich, reconciliation_specs
import build_site
import build as builder


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

    def test_producer_metadata_bug_cannot_supply_checker_expectations(self):
        import fiscal_schema
        original = fiscal_schema.metadata
        def wrong(contract, read):
            return dict(original(contract, read), scale=1000)
        with patch("fiscal_schema.metadata", side_effect=wrong):
            enrich(self.data)
            with self.assertRaisesRegex(ValueError, "unit/status/scope/period mismatch"):
                self.check()

    def test_producer_equal_valued_wrong_ledger_cell_is_independently_rejected(self):
        specs = list(reconciliation_specs())
        index = next(i for i, s in enumerate(specs) if s[0] == "functions/2025-26")
        name, year, unit, terms, exclusions, basis = specs[index]
        terms = [("4_3!X20" if ref == "4_2!X20" else ref, coef, quantum)
                 for ref, coef, quantum in terms]
        self.assertEqual(self.read("4_2!X20")["value"], self.read("4_3!X20")["value"])
        specs[index] = name, year, unit, terms, exclusions, basis
        with patch("fiscal_schema.reconciliation_specs", return_value=iter(specs)):
            enrich(self.data)
            with self.assertRaisesRegex(ValueError, "Wrong or overlapping reconciliation source cells"):
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

    def test_scope_notes_remain_attached_to_fiscal_values(self):
        education = self.data["provenance"]["function.education.real/2005-06"]
        self.assertIn("4_3!A34", education["scope_refs"])
        self.assertIn("not directly comparable", self.data["source_cells"]["4_3!A34"]["value"])
        self.assertIn("5_2!B143", self.data["provenance"]["detail.secondary/2025-26"]["scope_refs"])
        self.assertIn("academy", self.data["source_cells"]["5_2!B143"]["value"])
        education["scope_refs"].remove("4_3!A34")
        with self.assertRaisesRegex(ValueError, "unit/status/scope/period mismatch"):
            self.check()

    def test_definition_breaks_do_not_produce_percentage_changes(self):
        for area, refs in (("education", ["4_3!A34"]),
                           ("economic", ["4_3!A33", "4_3!A32"]),
                           ("eu", ["4_3!A35"])):
            key = f"change:function.{area}.real/2005-06:function.{area}.real/2025-26"
            record = self.data["derived"][key]
            self.assertIsNone(record["v"])
            self.assertEqual(record["comparability"], "definition_break")
            self.assertEqual(record["comparison_refs"], refs)
            self.assertEqual(record["missingness"], "not_comparable_definition_break")
        recent = "change:function.education.real/2015-16:function.education.real/2025-26"
        self.assertIsNotNone(self.data["derived"][recent]["v"])
        self.assertEqual(self.data["derived"][recent]["comparison_refs"], [])
        area = next(a for a in self.data["functions"] if a["id"] == "education")
        build_site.configure(self.data)
        rendered = build_site.change(area["series"]["2005-06"]["real"], area["series"]["2025-26"]["real"])
        self.assertIn("not comparable: the definition changed", rendered)
        self.assertIn("cell A34", rendered)
        self.assertNotIn("<data", rendered)


    def test_known_transport_breaks_split_the_history_chart(self):
        economic = next(a for a in self.data["functions"] if a["id"] == "economic")
        years = self.data["years"]
        values = [economic["series"][year]["real"]["v"] for year in years]
        boundaries = build_site.BREAKS["economic"]
        self.assertEqual([year for year, _ in boundaries], ["2011-12", "2015-16"])
        chart = build_site.line(years, values, breaks=[(years.index(y), label) for y, label in boundaries])
        self.assertEqual(chart.count("<polyline"), 3)
        build_site.configure(self.data)
        section = build_site.section_areas()
        self.assertIn("TfL added", section)
        self.assertIn("Rail added", section)
        self.assertIn("changed in 2011-12 and 2015-16", section)

    def test_definition_break_cannot_be_hidden_by_correct_arithmetic(self):
        key = "change:function.education.real/2005-06:function.education.real/2025-26"
        area = next(a for a in self.data["functions"] if a["id"] == "education")
        old, new = (area["series"][y]["real"]["v"] for y in ("2005-06", "2025-26"))
        self.data["derived"][key]["v"] = (new - old) / old * 100
        with self.assertRaisesRegex(ValueError, "missing is not zero"):
            self.check()
        self.data = copy.deepcopy(self.original)
        self.data["derived"][key]["comparison_refs"] = []
        with self.assertRaisesRegex(ValueError, "Wrong derived formula"):
            self.check()

    def test_public_download_rejects_undeclared_fields_before_rendering(self):
        locations = ("root", "function", "leaf", "report", "context", "source", "provenance",
                     "derived", "cell", "status", "formulae", "status_notes", "checks")
        for location in locations:
            with self.subTest(location=location):
                data = copy.deepcopy(self.original)
                if location == "checks":
                    data["checks"].append({"private_audit_payload": "private sentinel"})
                else:
                    target = {"root": data, "function": data["functions"][0],
                              "leaf": data["services_total"]["2025-26"],
                              "report": data["reconciliations"][0], "context": data["pesa_context"],
                              "source": data["sources"]["pesa_ch4"],
                              "provenance": next(iter(data["provenance"].values())),
                              "derived": next(iter(data["derived"].values())),
                              "cell": next(iter(data["source_cells"].values())),
                              "status": data["status_definitions"]["pesa_outturn"],
                              "formulae": data["formulae"], "status_notes": data["status_notes"]}[location]
                    target["private_audit_payload"] = {"path": "private sentinel"}
                with patch.object(build_site, "configure") as render:
                    with self.assertRaisesRegex(ValueError, "missing or extra|undeclared public"):
                        builder.payloads(data)
                    render.assert_not_called()
                with self.assertRaises(ValueError):
                    validate_fiscal(data, self.read)

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
        report = next(r for r in self.data["reconciliations"] if r["id"] == "history-functions/2022-23")
        self.assertIn("obr_extrapolated", report["statuses"])
        self.assertIn("Spending (per cent of GDP)!N6", report["status_refs"])

    def test_retained_missing_value_and_raw_unit_cannot_be_fabricated(self):
        cell = self.data["source_cells"]["Public finances since 1900!E82"]
        cell.update(kind="number", value="0")
        with self.assertRaisesRegex(ValueError, "Independent reconciliation failed|Wrong retained source kind"):
            self.check()
        self.data = copy.deepcopy(self.original)
        self.data["source_cells"]["4_2!X3"]["value"] = "£ million"
        with self.assertRaisesRegex(ValueError, "Changed retained raw value"):
            self.check()


class ReceiptProductBoundaryTests(unittest.TestCase):
    """Product corruptions must fail independently of producer metadata."""

    @classmethod
    def setUpClass(cls):
        import check_receipts
        cls.receipt_checker = check_receipts
        cls.original = check_receipts.read_json(ROOT / "data/receipts.json")
        cls.reader = check_receipts.Raw(ROOT)

    @classmethod
    def tearDownClass(cls):
        cls.reader.close()

    def setUp(self):
        self.data = copy.deepcopy(self.original)

    def check(self):
        # Share independently reopened, pinned raw sheets across corruption
        # cases; production validate() constructs and closes its own reader.
        with patch.object(self.receipt_checker, "Raw", return_value=self.reader):
            with patch.object(self.reader, "close"):
                return self.receipt_checker.validate(self.data)

    def table(self, key="current_receipts"):
        return self.data["tables"][key]

    def leaf(self, column, year="2025-26", key="current_receipts"):
        return self.table(key)["series"][column]["values"][year]

    def test_all_receipt_and_debt_values_match_independent_raw_sources(self):
        self.assertGreater(self.check(), 20000)

    def test_equal_numeric_value_cannot_move_to_another_source_cell(self):
        values = self.table()["series"]
        seen = {}
        for series in values.values():
            for leaf in series["values"].values():
                if leaf["v"] is None:
                    continue
                if leaf["v"] in seen:
                    # Both references are real and numerically equal. Identity
                    # must still bind the particular tax, period and unit.
                    leaf["ref"] = seen[leaf["v"]]
                    with self.assertRaisesRegex(ValueError, "wrong source/year cell"):
                        self.check()
                    return
                seen[leaf["v"]] = leaf["ref"]
        self.fail("Pinned evidence has no equal-valued cells for this probe")

    def test_self_consistent_changed_raw_and_product_number_is_rejected(self):
        leaf = self.leaf("Q")
        leaf["v"] += 1
        leaf["raw"] = str(leaf["v"])
        with self.assertRaisesRegex(ValueError, "raw value differs"):
            self.check()

    def test_units_roles_accounting_scope_and_status_are_independently_bound(self):
        mutations = (
            ("unit", "GBP million", "series"),
            ("role", "receipts_total", "series"),
            ("status", "forecast", "leaf"),
            ("basis", "cash", "leaf"),
            ("scope", "central_government", "leaf"),
            ("geography", "Great Britain", "leaf"),
        )
        for field, wrong, target in mutations:
            with self.subTest(field=field):
                self.data = copy.deepcopy(self.original)
                record = self.table()["series"]["Q"] if target == "series" else self.leaf("Q")
                record[field] = wrong
                with self.assertRaises(ValueError):
                    self.check()

    def test_dash_missing_negative_and_zero_remain_distinct(self):
        missing = self.leaf("K", "2022-23", "historical_receipts_cash")
        self.assertEqual((missing["kind"], missing["raw"], missing["v"]), ("text", "-", None))
        self.assertLess(self.leaf("J", "2022-23", "historical_receipts_cash")["v"], 0)
        self.assertTrue(any(v["v"] == 0 for s in self.table()["series"].values()
                            for v in s["values"].values() if v["kind"] == "number"))
        missing.update(kind="number", raw="0", v=0)
        with self.assertRaisesRegex(ValueError, "kind changed"):
            self.check()

    def test_forecast_boundary_last_forecast_and_historical_vintage_are_preserved(self):
        self.assertEqual(self.leaf("AG")["status"], "outturn")
        self.assertEqual(self.leaf("AG", "2026-27")["status"], "forecast")
        self.assertEqual(self.leaf("AG", "2031-32")["status"], "forecast")
        hist = self.leaf("Y", "2022-23", "historical_receipts_cash")
        self.assertEqual(hist["status"], "historical_status_uncertain")
        hist["status"] = "forecast"
        with self.assertRaisesRegex(ValueError, "wrong status"):
            self.check()

    def test_year_alignment_and_missing_year_cannot_be_hidden(self):
        debt = self.leaf("D", "2022-23", "historical_aggregates_cash")
        self.assertEqual(debt["ref"], "Aggregates (£m)!D331")
        debt["year_ref"] = "Aggregates (£m)!B329"
        with self.assertRaisesRegex(ValueError, "wrong source/year cell"):
            self.check()
        self.data = copy.deepcopy(self.original)
        del self.table()["series"]["AG"]["values"]["2031-32"]
        with self.assertRaisesRegex(ValueError, "unexpected or missing fields"):
            self.check()

    def test_refunds_and_income_tax_subtypes_are_not_double_counted(self):
        vat = self.table()["derived"]["vat"]["2025-26"]
        self.assertEqual([o["ref"] for o in vat["operands"]],
                         ["Receipts (£bn)!C33", "Receipts (£bn)!D33"])
        income = self.table()["derived"]["income_tax"]["2025-26"]
        self.assertEqual(len(income["operands"]), 3)
        vat["operands"].append(copy.deepcopy(vat["operands"][1]))
        with self.assertRaisesRegex(ValueError, "operand count changed"):
            self.check()

    def test_parent_total_or_mixed_residual_cannot_replace_a_tax_operand(self):
        self.table()["derived"]["other_taxes"]["2025-26"]["operands"][0]["ref"] = "Receipts (£bn)!AG33"
        with self.assertRaisesRegex(ValueError, "wrong, duplicate or overlapping"):
            self.check()
        self.data = copy.deepcopy(self.original)
        self.table()["series"]["AF"]["role"] = "non_tax_component"
        with self.assertRaisesRegex(ValueError, "role disagrees"):
            self.check()

    def test_derived_result_and_operand_order_are_checked_against_raw_data(self):
        self.table()["derived"]["non_tax"]["2025-26"]["v"] += 1
        with self.assertRaisesRegex(ValueError, "numeric value mismatch"):
            self.check()
        self.data = copy.deepcopy(self.original)
        self.table()["derived"]["non_tax"]["2025-26"]["operands"].reverse()
        with self.assertRaisesRegex(ValueError, "wrong, duplicate or overlapping"):
            self.check()

    def test_real_historical_overlap_is_unresolved_with_no_invented_error_bound(self):
        reports = self.table("historical_receipts_cash")["reconciliations"]
        report = next(r for r in reports if r["id"] == "central" and r["year"] == "1998-99")
        self.assertAlmostEqual(report["residual"], 2179)
        self.assertEqual(report["outcome"], "unresolved_source_difference")
        self.assertLess(report["budget"], 0.000001)
        report["outcome"] = "reconciled_storage_precision"
        with self.assertRaisesRegex(ValueError, "outcome changed"):
            self.check()

    def test_missing_business_operands_never_earn_a_reconciliation_pass(self):
        reports = self.table("historical_receipts_cash")["reconciliations"]
        report = next(r for r in reports if r["id"] == "business" and r["year"] == "2022-23")
        self.assertEqual(report["outcome"], "not_testable_missing")
        self.assertIsNone(report["residual"])
        self.assertTrue(report["missing_operands"])
        report.update(residual=0, budget=0, outcome="reconciled_storage_precision", missing_operands=[])
        with self.assertRaises(ValueError):
            self.check()

    def test_report_omissions_duplicates_and_inflated_budget_fail(self):
        reports = self.table()["reconciliations"]
        reports[0]["budget"] = 1
        with self.assertRaisesRegex(ValueError, "storage arithmetic allowance"):
            self.check()
        self.data = copy.deepcopy(self.original)
        self.table()["reconciliations"].append(copy.deepcopy(self.table()["reconciliations"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate or unknown"):
            self.check()
        self.data = copy.deepcopy(self.original)
        self.table()["reconciliations"].pop()
        with self.assertRaisesRegex(ValueError, "report omitted"):
            self.check()

    def test_debt_stock_denominator_and_historical_scope_are_explicit(self):
        debt = self.leaf("X", "2025-26", "current_aggregates_cash")
        borrow = self.leaf("O", "2025-26", "current_aggregates_cash")
        self.assertEqual((debt["basis"], borrow["basis"]), ("cash_stock", "annual_accrual"))
        gdp = self.leaf("AF", "2025-26", "current_aggregates_gdp")
        self.assertEqual(gdp["basis"], "march_centred")
        self.assertEqual(self.table("current_aggregates_gdp")["series"]["AF"]["unit"], "GBP billion")
        early = self.leaf("C", "1899-00", "historical_aggregates_cash")
        self.assertEqual((early["scope"], early["basis"]),
                         ("central_government_proxy", "historical_basis_uncertain"))
        self.assertIn("Uncertain", self.leaf("Y", "1800-01", "historical_receipts_cash")["geography"])
        debt["basis"] = "annual_accrual"
        with self.assertRaisesRegex(ValueError, "wrong basis"):
            self.check()

    def test_unknown_fields_and_removed_limitations_fail(self):
        self.table()["private_runtime_data"] = "sentinel"
        with self.assertRaisesRegex(ValueError, "unexpected or missing fields"):
            self.check()
        self.data = copy.deepcopy(self.original)
        self.data["limitations"].pop()
        with self.assertRaisesRegex(ValueError, "limitations changed"):
            self.check()

    def test_duplicate_json_keys_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
            json.loads('{"v": 0, "v": 1}', object_pairs_hook=self.receipt_checker.unique_object)


if __name__ == "__main__":
    unittest.main()
