"""Source-format contracts and the fail-fast guards enforced by mypy."""
import csv
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import openpyxl

from builder import downloads, rates, readers


class SourceReaders(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(readers.xlsx.cache_clear)
        self.addCleanup(readers.ods.cache_clear)

    def ods_file(self, cells: str, name: str = 'table:name="Sheet"') -> Path:
        path = self.root / "source.ods"
        xml = (
            '<office:document-content '
            'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
            'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
            'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">'
            f'<table:table {name}><table:table-row table:number-rows-repeated="2">'
            f'{cells}</table:table-row></table:table></office:document-content>'
        )
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("content.xml", xml)
        return path

    def test_ods_preserves_numbers_text_blanks_and_repeats(self) -> None:
        path = self.ods_file(
            '<table:table-cell office:value-type="float" office:value="12.5" '
            'table:number-columns-repeated="2"/>'
            '<table:covered-table-cell/>'
            '<table:table-cell office:value-type="string"><text:p>Estimate</text:p></table:table-cell>'
            '<table:table-cell/>'
        )
        self.assertEqual(readers.ods(path), {"Sheet": [
            [12.5, 12.5, None, "Estimate"], [12.5, 12.5, None, "Estimate"],
        ]})

    def test_ods_numeric_cell_requires_stored_value(self) -> None:
        path = self.ods_file('<table:table-cell office:value-type="float"/>')
        with self.assertRaisesRegex(ValueError, "missing office:value"):
            readers.ods(path)

    def test_ods_requires_sheet_name(self) -> None:
        path = self.ods_file('<table:table-cell/>', name="")
        with self.assertRaisesRegex(ValueError, "missing table:name"):
            readers.ods(path)

    def test_xlsx_cell_and_row_values(self) -> None:
        path = self.root / "source.xlsx"
        book = openpyxl.Workbook()
        sheet = book.active
        assert sheet is not None
        sheet.append(["Year", "Estimate", "Missing"])
        sheet.append([2025, 12.5, None])
        book.save(path)
        book.close()
        self.assertEqual(readers.cell(path, "Sheet", "B2"), 12.5)
        self.assertIsNone(readers.cell(path, "Sheet", "C2"))
        self.assertEqual(readers.xlsx_rows(path, "Sheet")[1], [2025, 12.5, None])
        with self.assertRaisesRegex(ValueError, "single cell"):
            readers.cell(path, "Sheet", "A1:B2")

    def test_ons_series_keeps_missing_values_distinct_from_zero(self) -> None:
        path = self.root / "series.csv"
        path.write_text("Title,Employment\n2024,0\n2025,x\n2026 Q1,..\n2026 JAN,1.5\n",
                        encoding="utf-8-sig")
        meta, values = readers.ons_series(path)
        self.assertEqual(meta, {"Title": "Employment"})
        self.assertEqual(values, {"2024": 0.0, "2025": None, "2026 Q1": None, "2026 JAN": 1.5})

    def test_csv_rows_reports_missing_and_extra_fields(self) -> None:
        path = self.root / "rows.csv"
        path.write_text("Year,Value\n2024\n2025,2,extra\n", encoding="utf-8-sig")
        self.assertEqual(readers.csv_rows(path), [
            {"Year": "2024", "Value": None},
            {"Year": "2025", "Value": "2", None: ["extra"]},
        ])

    def test_pdf_locator_reads_a_number_and_rejects_bad_syntax(self) -> None:
        with patch.object(readers, "pdf_pages", return_value=["Heading\nVisits 1,234 5.6"]):
            self.assertEqual(readers.pdf_number("unused.pdf", "p1 after 'Heading' line 'Visits' number 2"), 5.6)
        with patch.object(readers, "pdf_pages") as pages:
            with self.assertRaisesRegex(ValueError, "Invalid PDF number locator"):
                readers.pdf_number("unused.pdf", "not a locator")
            pages.assert_not_called()


class TypedOutputs(unittest.TestCase):
    def test_saved_tax_rates_keep_numeric_results_and_source_dates(self) -> None:
        sources: dict[str, rates.SourceDates] = {
            "gov-income-tax-rates": {"retrieved": "2026-11-01"},
            "gov-self-employed-ni": {"retrieved": "2026-11-02"},
        }
        result = rates.read_rates(sources)
        employee = result["illustration"]
        self.assertEqual(employee["salary"], 30000)
        self.assertEqual(employee["income_tax"], (30000 - employee["allowance"]) * employee["basic_rate"])
        self.assertAlmostEqual(employee["total"], employee["income_tax"] + employee["ni"])
        self.assertEqual(result["retrieved"], "2026-11-01")
        self.assertEqual(result["self_employed"]["retrieved"], "2026-11-02")

    def test_comparison_csv_handles_a_missing_label_and_escapes_fields(self) -> None:
        rows = downloads.list_rows(
            "cmp-list",
            '<li><span class="cmp-y">2024</span><span class="cmp-y">2025</span>'
            '<span class="cmp-v">£1,234</span></div>'
            '<p class="cmp-change">Change: £2</p></li>',
        )
        self.assertEqual(rows, [["Measure", "2024", "2025", "Change"], ["", "£1,234", "£2"]])
        encoded = downloads.to_csv(rows)
        self.assertTrue(encoded.startswith("\ufeff"))
        self.assertEqual(list(csv.reader(io.StringIO(encoded.lstrip("\ufeff")))), rows)
