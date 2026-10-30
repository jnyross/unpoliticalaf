"""Bounded corruption tests for private payer source evidence."""
import csv
from io import BytesIO
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_payer_sources as checker
from build import PUBLIC_FILES, validate_output


class PayerSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root / checker.DIRECTORY
        shutil.copytree(ROOT / checker.DIRECTORY, self.base)

    def mutate_csv(self, filename, change):
        path = self.base / "audit" / filename
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            fields, rows = reader.fieldnames, list(reader)
        change(rows)
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        # The mutable index now agrees with the forgery. Raw source comparison,
        # rather than a trusted researcher extract hash, must still reject it.
        index_path = self.base / "audit/index.json"
        index = json.loads(index_path.read_text())
        index["audits"][filename] = checker.digest(path.read_bytes())
        index_path.write_text(json.dumps(index))

    def test_every_retained_cell_and_source_without_writes(self):
        before = {p.relative_to(self.base): p.read_bytes()
                  for p in self.base.rglob("*") if p.is_file()}
        self.assertEqual(checker.validate(self.root), 793)
        self.assertEqual(before, {p.relative_to(self.base): p.read_bytes()
                                  for p in self.base.rglob("*") if p.is_file()})

    def test_changed_raw_workbook_hash_rejected(self):
        for name in (checker.HMRC, checker.ONS):
            with self.subTest(source=name):
                path = self.base / "raw" / name
                original = path.read_bytes()
                path.write_bytes(original + b"altered")
                try:
                    with self.assertRaisesRegex(ValueError, "original response hash/length mismatch"):
                        checker.validate(self.root)
                finally:
                    path.write_bytes(original)

    def test_tampered_html_body_and_envelope_rejected(self):
        path = self.base / "raw/hmrc-latest-release.html.json"
        original = path.read_bytes()
        for kind in ("body", "envelope"):
            with self.subTest(kind=kind):
                envelope = json.loads(original)
                if kind == "body":
                    envelope["original_response"] += "altered"
                    path.write_text(json.dumps(envelope, ensure_ascii=True))
                else:
                    # Whitespace-only envelope edits preserve the decoded body.
                    path.write_bytes(original + b" ")
                with self.assertRaisesRegex(ValueError, "stored envelope hash/length mismatch"):
                    checker.validate(self.root)
        path.write_bytes(original)

    def test_recovered_html_body_checked_even_if_envelope_hash_updated(self):
        path = self.base / "raw/hmrc-latest-release.html.json"
        envelope = json.loads(path.read_bytes())
        envelope["original_response"] += "altered"
        path.write_text(json.dumps(envelope, ensure_ascii=True))
        register_path = self.base / "sources.json"
        register = json.loads(register_path.read_bytes())
        entry = next(e for e in register["sources"] if e["file"].endswith(path.name))
        entry["stored_sha256"] = checker.digest(path.read_bytes())
        entry["stored_bytes"] = path.stat().st_size
        register_path.write_text(json.dumps(register))
        with self.assertRaisesRegex(ValueError, "Pinned payer source register hash changed"):
            checker.validate(self.root)
        # Isolate the second hash layer: even an accepted new envelope still
        # must recover exactly the recorded original response, without trimming.
        with patch.object(checker, "REGISTER_SHA256", checker.digest(register_path.read_bytes())):
            with self.assertRaisesRegex(ValueError, "original response hash/length mismatch"):
                checker.validate(self.root)

    def test_rehashed_wrong_numeric_cells_rejected_by_originals(self):
        for filename, sheet, cell, field in (
                ("hmrc-cells.csv", "2_4_Taxpayer_share_tax", "F27", "published_text"),
                ("ons-cells.csv", "Table 8", "D15", "published_value")):
            with self.subTest(filename=filename):
                def change(rows):
                    next(r for r in rows if r["sheet"] == sheet and r["cell"] == cell)[field] = "0"
                self.mutate_csv(filename, change)
                with self.assertRaisesRegex(ValueError, "Payer source cell mismatch"):
                    checker.validate(self.root)
                # Restore the first file before exercising the other source reader.
                shutil.copy2(ROOT / checker.DIRECTORY / "audit" / filename, self.base / "audit" / filename)
                shutil.copy2(ROOT / checker.DIRECTORY / "audit/index.json", self.base / "audit/index.json")

    def test_rehashed_note_change_rejected_by_original(self):
        def change(rows):
            next(r for r in rows if r["sheet"] == "Notes" and r["cell"] == "B16")["published_value"] = "Expenditure equals gross income"
        self.mutate_csv("ons-cells.csv", change)
        with self.assertRaisesRegex(ValueError, "Payer source cell mismatch: .*Notes!B16"):
            checker.validate(self.root)

    def test_missing_duplicate_and_equal_value_wrong_coordinate_rejected(self):
        path = self.base / "audit/hmrc-cells.csv"
        original = path.read_bytes()
        index_path = self.base / "audit/index.json"
        index = index_path.read_bytes()
        for mode in ("missing", "duplicate", "wrong-coordinate", "wrong-source"):
            with self.subTest(mode=mode):
                def change(rows):
                    if mode == "missing":
                        rows.pop()
                    elif mode == "duplicate":
                        rows.append(rows[-1].copy())
                    elif mode == "wrong-coordinate":
                        # Both published quantile breakpoints are 29,700.
                        next(r for r in rows if r["sheet"] == "2_4_Taxpayer_inc_quantiles"
                             and r["cell"] == "F27")["cell"] = "G27"
                    else:
                        rows[0]["snapshot"] = checker.ONS
                self.mutate_csv("hmrc-cells.csv", change)
                with self.assertRaisesRegex(ValueError, "wrong cell identity"):
                    checker.validate(self.root)
                path.write_bytes(original)
                index_path.write_bytes(index)

    def test_csv_hash_and_symlink_rejected(self):
        path = self.base / "audit/hmrc-cells.csv"
        original = path.read_bytes()
        path.write_bytes(original + b"changed")
        with self.assertRaisesRegex(ValueError, "CSV hash mismatch"):
            checker.validate(self.root)
        path.write_bytes(original)
        index_path = self.base / "audit/index.json"
        target = index_path.with_name("linked.json")
        index_path.rename(target)
        index_path.symlink_to(target.name)
        with self.assertRaisesRegex(ValueError, "without symlinks"):
            checker.validate(self.root)

    def test_verify_calls_payer_checker(self):
        import verify
        # Halt at this gate; this test does not run other fiscal checks.
        with patch.object(verify, "validate_audit"), patch.object(verify, "validate_receipt_audit"):
            with patch.object(verify, "validate_payer_sources", side_effect=ValueError("payer gate failed")) as gate:
                with self.assertRaisesRegex(ValueError, "payer gate failed"):
                    verify.main()
                gate.assert_called_once_with()

    def test_private_paths_remain_outside_public_manifest(self):
        for name in ("data/payers/audit/ons-cells.csv", "data/payers/sources.json",
                     "data/payers/raw/ons-etb-fye2024.xlsx", "docs/payer-source-seed.md"):
            with self.subTest(path=name):
                self.assertNotIn(name, PUBLIC_FILES)
                output = self.root / "public"
                path = output / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"private")
                with self.assertRaisesRegex(ValueError, "unexpected file"):
                    validate_output(output)
                shutil.rmtree(output)


class SourceReaderTests(unittest.TestCase):
    def ods(self, rows):
        stream = BytesIO()
        xml = ('<office:document-content '
               'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
               'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
               'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">'
               '<office:body><office:spreadsheet><table:table table:name="S">'
               + rows + '</table:table></office:spreadsheet></office:body></office:document-content>')
        with ZipFile(stream, "w") as archive:
            archive.writestr("content.xml", xml)
        stream.seek(0)
        return stream

    def test_large_ods_repeats_do_not_expand_grid(self):
        source = self.ods(
            '<table:table-row table:number-rows-repeated="1000000">'
            '<table:table-cell table:number-columns-repeated="16384">'
            '<text:p>suppressed</text:p></table:table-cell></table:table-row>')
        self.assertEqual(checker.ods_cells(source, {"S": ["A1", "XFD999999"]}),
                         {"S": {"A1": "suppressed", "XFD999999": "suppressed"}})

    def test_ods_text_blanks_and_suppression_are_preserved(self):
        source = self.ods(
            '<table:table-row><table:table-cell><text:p>a<text:s text:c="2"/>b'
            '<text:tab/>c<text:line-break/>d</text:p><text:p>last</text:p></table:table-cell>'
            '<table:table-cell/><table:table-cell><text:p>..</text:p></table:table-cell>'
            '<table:table-cell><text:p>0.0</text:p></table:table-cell></table:table-row>')
        self.assertEqual(checker.ods_cells(source, {"S": ["A1", "B1", "C1", "D1", "E1"]}),
                         {"S": {"A1": "a  b\tc\nd\nlast", "B1": "", "C1": "..", "D1": "0.0", "E1": ""}})

    def test_invalid_ods_repeats_fail_closed(self):
        for count in ("0", "-1", "1048577", "99999999999999999"):
            with self.subTest(count=count):
                source = self.ods('<table:table-row table:number-rows-repeated="' + count
                                  + '"><table:table-cell/></table:table-row>')
                with self.assertRaisesRegex(ValueError, "Unsafe ODS repeat count"):
                    checker.ods_cells(source, {"S": ["A1"]})

    def test_xlsx_cached_scalars_do_not_coerce_blank_or_suppression(self):
        from openpyxl import Workbook
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "S"
        sheet["A1"] = 0
        sheet["C1"] = ".."
        sheet["D1"] = "#N/A"
        sheet["E1"] = "=1+1"  # No cached result: never evaluated as 2 or filled with 0.
        stream = BytesIO()
        workbook.save(stream)
        workbook.close()
        stream.seek(0)
        self.assertEqual(checker.xlsx_cells(stream, {"S": ["A1", "B1", "C1", "D1", "E1"]}),
                         {"S": {"A1": "0", "B1": "", "C1": "..", "D1": "#N/A", "E1": ""}})


if __name__ == "__main__":
    unittest.main()
