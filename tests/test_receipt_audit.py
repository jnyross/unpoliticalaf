"""Receipt evidence corruption tests; no fiscal interpretation is approved here."""
import copy
import csv
import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_audit import validate as validate_spending
from check_receipt_audit import validate
from extract_receipt_audit import export, raw_cells
from receipt_audit_scope import DIRECTORY, SCOPE_ID, SHEETS, filename


class ReceiptAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "data", self.root / "data")
        dest = self.root / "reference/un-political"
        dest.mkdir(parents=True)
        shutil.copy2(ROOT / "reference/un-political/SOURCE.json", dest)

    def index(self):
        return json.loads((self.root / DIRECTORY / "index.json").read_text())

    def save_index(self, index):
        (self.root / DIRECTORY / "index.json").write_text(json.dumps(index))

    def mutate(self, source, sheet, change):
        index = self.index()
        entry = next(e for e in index["sheets"] if (e["source_id"], e["sheet"]) == (source, sheet))
        path = self.root / DIRECTORY / entry["file"]
        with path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            fields, rows = reader.fieldnames, list(reader)
        change(rows, entry)
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fields, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        # Author-controlled manifest and TSV now agree: reopening raw data must
        # still reject these mutations, including semantic labels and units.
        entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.save_index(index)

    def cell(self, coordinate, **changes):
        def change(rows, _entry):
            next(r for r in rows if r["cell"] == coordinate).update(changes)
        return change

    def reject(self, source, sheet, change, message):
        self.mutate(source, sheet, change)
        with self.assertRaisesRegex(ValueError, message):
            validate(self.root)

    def test_complete_separate_scope_and_deterministic_regeneration(self):
        self.assertEqual(validate(self.root), 30061)
        before = {p.name: p.read_bytes() for p in (self.root / DIRECTORY).glob("*") if p.suffix in (".json", ".tsv")}
        spending = {p.name: p.read_bytes() for p in (self.root / "data/audit").iterdir() if p.is_file()}
        export(self.root)
        after = {p.name: p.read_bytes() for p in (self.root / DIRECTORY).glob("*") if p.suffix in (".json", ".tsv")}
        self.assertEqual(before, after)
        self.assertEqual(spending, {p.name: p.read_bytes() for p in (self.root / "data/audit").iterdir() if p.is_file()})
        self.assertEqual(self.index()["scope"], SCOPE_ID)
        self.assertEqual(len(self.index()["sheets"]), 9)

    def test_changed_raw_workbook_and_pinned_manifest_rejected(self):
        for relative in ("data/raw/OBR_Public_finances_databank_October_2026.xlsx",
                         "data/raw/OBR_Historical_public_finances_database.xlsx",
                         "reference/un-political/SOURCE.json", "data/sources.json"):
            with self.subTest(path=relative):
                path = self.root / relative
                original = path.read_bytes()
                path.write_bytes(original + b"changed")
                try:
                    with self.assertRaisesRegex(ValueError, "hash changed|hash mismatch"):
                        validate(self.root)
                    with self.assertRaisesRegex(ValueError, "hash changed|hash mismatch"):
                        export(self.root)
                finally:
                    path.write_bytes(original)

    def test_missing_duplicate_and_extra_sheet_rejected(self):
        original = self.index()
        for mode in ("missing", "duplicate", "extra"):
            with self.subTest(mode=mode):
                index = copy.deepcopy(original)
                if mode == "missing": index["sheets"].pop()
                elif mode == "duplicate": index["sheets"][1] = copy.deepcopy(index["sheets"][0])
                else: index["sheets"].append(copy.deepcopy(index["sheets"][0]))
                self.save_index(index)
                with self.assertRaisesRegex(ValueError, "Missing or duplicate audit sheet"):
                    validate(self.root)

    def test_wrong_unit_and_total_not_income_tax_label_rejected(self):
        self.reject("obr_databank", "Receipts (£bn)",
                    self.cell("AG4", raw_value_json=json.dumps("Income tax")), "text/label/unit mismatch")
        # Restore the first extract before checking an independently wrong unit.
        export(self.root)
        self.reject("obr_hist", "Receipts (£m)",
                    self.cell("B1", raw_value_json=json.dumps("Public sector current receipts (£bn)")),
                    "text/label/unit mismatch")

    def test_refund_label_cannot_be_lost(self):
        self.reject("obr_databank", "Receipts (£bn)",
                    self.cell("D4", raw_value_json=json.dumps("VAT (net of VAT refunds)")),
                    "text/label/unit mismatch")

    def test_equal_valued_wrong_cell_is_rejected(self):
        # M7 and N7 are both numeric zero. Equal values do not prove cell identity.
        self.reject("obr_databank", "Receipts (£bn)", self.cell("M7", cell="N7"),
                    "missing, duplicate or wrong cell")

    def test_missing_and_overlapping_cells_rejected(self):
        for mode in ("missing", "overlap"):
            with self.subTest(mode=mode):
                def change(rows, _entry):
                    if mode == "missing": rows.pop()
                    else: rows.append(copy.deepcopy(rows[-1]))
                self.reject("obr_databank", "Receipts (£bn)", change,
                            "missing, duplicate or wrong cell")
                export(self.root)

    def test_negative_receipt_sign_is_preserved(self):
        self.reject("obr_hist", "Receipts (£m)",
                    self.cell("J322", raw_value_json=json.dumps("562")), "numeric cell mismatch")

    def test_missing_dash_cannot_be_zero(self):
        self.reject("obr_hist", "Receipts (£m)",
                    self.cell("C7", kind="number", raw_value_json=json.dumps("0")), "numeric cell mismatch")

    def test_explicit_blank_cannot_be_zero(self):
        self.reject("obr_databank", "Receipts (£bn)",
                    self.cell("B2", kind="number", raw_value_json=json.dumps("0")), "numeric cell mismatch")

    def test_total_value_and_reconciliation_derivation_cannot_be_changed(self):
        self.reject("obr_databank", "Receipts (£bn)",
                    self.cell("AG7", raw_value_json=json.dumps("379.518")), "numeric cell mismatch")
        export(self.root)
        # The source's derivation text is evidence, not a calculated identity
        # implemented by this seed. Adding a parent subtotal would double count.
        self.reject("obr_hist", "Receipts (£m)",
                    self.cell("B6", raw_value_json=json.dumps("b+c+d+e+f")), "text/label/unit mismatch")

    def test_source_vintage_boundary_and_cash_accrual_note_preserved(self):
        for sid, sheet, coordinate, wrong in (
                ("obr_databank", "Receipts (£bn)", "C41", "All years are observed outturn"),
                ("obr_hist", "Contents", "D35", "All receipts are accruals"),
                ("obr_hist", "Contents", "D34", "Consistent with October 2026")):
            with self.subTest(sheet=sheet, cell=coordinate):
                self.reject(sid, sheet, self.cell(coordinate, raw_value_json=json.dumps(wrong)), "text/label/unit mismatch")
                export(self.root)

    def test_debt_stock_and_borrowing_flow_definitions_preserved(self):
        self.reject("obr_databank", "Glossary",
                    self.cell("C14", raw_value_json=json.dumps("Annual borrowing flow")), "text/label/unit mismatch")

    def test_formula_cache_and_number_format_are_bound(self):
        self.reject("obr_databank", "Receipts (£bn)",
                    self.cell("AG7", formula_json=json.dumps("SUM(C7:AH7)")), "formula mismatch")
        export(self.root)
        self.reject("obr_databank", "Receipts (£bn)",
                    self.cell("AG7", format_id="999999"), "source precision mismatch")

    def test_manifest_identity_source_metadata_and_range_are_strict(self):
        original = self.index()
        for field, wrong in (("scope", "spending"), ("catalogue_sha256", "0" * 64),
                             ("pinned_manifest_sha256", "0" * 64), ("extra", "private")):
            with self.subTest(field=field):
                index = copy.deepcopy(original); index[field] = wrong; self.save_index(index)
                with self.assertRaisesRegex(ValueError, "scope/fields changed|identity changed"):
                    validate(self.root)
        for field, wrong in (("ranges", ["B1:AI52"]), ("published", "2026-03-03"),
                             ("source_file", "data/raw/wrong.xlsx"), ("source_sha256", "0" * 64),
                             ("file", "../index.json")):
            with self.subTest(field=field):
                index = copy.deepcopy(original); index["sheets"][0][field] = wrong; self.save_index(index)
                with self.assertRaisesRegex(ValueError, "source/selection mismatch"):
                    validate(self.root)

    def test_extract_hash_and_manifest_symlink_rejected(self):
        path = self.root / DIRECTORY / filename("obr_databank", "Receipts (£bn)")
        path.write_bytes(path.read_bytes() + b"changed")
        with self.assertRaisesRegex(ValueError, "extract hash mismatch"):
            validate(self.root)
        index = self.root / DIRECTORY / "index.json"
        target = index.with_name("linked.json"); index.rename(target); index.symlink_to(target.name)
        with self.assertRaisesRegex(ValueError, "symlink"):
            validate(self.root)

    def test_receipt_scope_cannot_expand_original_spending_scope(self):
        # The spending checker still accepts exactly its original eight sheets.
        index_path = self.root / "data/audit/index.json"
        old = json.loads(index_path.read_text())
        old["sheets"].append(self.index()["sheets"][0])
        index_path.write_text(json.dumps(old))
        with self.assertRaisesRegex(ValueError, "Missing or duplicate audit sheet"):
            validate_spending(self.root)

    def test_declared_verify_rejects_rehashed_receipt_corruption(self):
        self.mutate("obr_databank", "Receipts (£bn)",
                    self.cell("AG4", raw_value_json=json.dumps("Income tax")))
        shutil.copytree(ROOT / "scripts", self.root / "scripts")
        shutil.copytree(ROOT / "site", self.root / "site")
        result = subprocess.run([sys.executable, str(self.root / "scripts/verify.py")],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Audit text/label/unit mismatch: Receipts (£bn)!AG4", result.stderr)

    def test_in_scope_xml_errors_fail_closed_without_dumping_unrelated_columns(self):
        # Historical chart helper cells beyond column Z contain #N/A errors.
        # The fixed evidence scope excludes helpers; selected errors never pass.
        from openpyxl import Workbook
        w = Workbook(); s = w.active; s.title = "Example"
        s["A1"] = "definition"; s["B1"] = "#N/A"
        stream = BytesIO(); w.save(stream); stream.seek(0)
        with ZipFile(stream) as archive:
            self.assertEqual(raw_cells(archive, "Example", {"A1"})["A1"][1], "definition")
            with self.assertRaisesRegex(ValueError, "Unsupported receipt XML cell kind"):
                raw_cells(archive, "Example", {"A1", "B1"})


if __name__ == "__main__":
    unittest.main()
