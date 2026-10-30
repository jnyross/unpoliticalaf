"""Recovery boundary tests: readable evidence must agree with retained raw data.

These do not claim completion of issue #4's broader fiscal-schema acceptance.
"""
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


if __name__ == "__main__":
    unittest.main()
