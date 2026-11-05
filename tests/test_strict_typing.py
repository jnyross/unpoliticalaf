"""Regression tests for the shared modules migrated to strict typing."""
import csv
import io
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference

from builder import downloads, rates, readers, version


class Readers(unittest.TestCase):
    def test_xlsx_values_and_single_cell_references(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            book = Workbook()
            sheet = book.active
            assert sheet is not None
            sheet.title = "Figures"
            sheet.append(["Year", "Estimate"])
            sheet.append([2025, 12.5])
            sheet.append([2026, None])
            chart = BarChart()
            chart.add_data(Reference(sheet, min_col=2, min_row=1, max_row=3), titles_from_data=True)
            book.create_chartsheet("Chart").add_chart(chart)
            book.save(root / "figures.xlsx")
            with patch.object(readers, "ROOT", root):
                readers.xlsx.cache_clear()
                try:
                    self.assertEqual(readers.cell("figures.xlsx", "Figures", "B2"), 12.5)
                    self.assertIsNone(readers.cell("figures.xlsx", "Figures", "B3"))
                    self.assertEqual(readers.xlsx_rows("figures.xlsx", "Figures")[1], [2025, 12.5])
                    with self.assertRaisesRegex(ValueError, "single cell"):
                        readers.cell("figures.xlsx", "Figures", "A1:B2")
                    with self.assertRaisesRegex(ValueError, "not a worksheet"):
                        readers.xlsx_rows("figures.xlsx", "Chart")
                finally:
                    readers.xlsx.cache_clear()
        self.assertEqual(readers.ref(4, 26), "AA5")

    def read_ods(self, table: str) -> dict[str, list[list[readers.ODSValue]]]:
        xml = (
            '<document xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
            'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
            'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">'
            + table + "</document>"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with zipfile.ZipFile(root / "figures.ods", "w") as archive:
                archive.writestr("content.xml", xml)
            with patch.object(readers, "ROOT", root):
                readers.ods.cache_clear()
                try:
                    return readers.ods("figures.ods")
                finally:
                    readers.ods.cache_clear()

    def test_ods_repeats_numbers_text_and_missing_values(self) -> None:
        result = self.read_ods(
            '<table:table table:name="Figures">'
            '<table:table-row table:number-rows-repeated="2">'
            '<table:table-cell office:value-type="float" office:value="12.5"/>'
            '<table:table-cell table:number-columns-repeated="2"/>'
            '<table:table-cell><text:p>not available</text:p></table:table-cell>'
            '</table:table-row>'
            '<table:table-row table:number-rows-repeated="100"><table:table-cell/></table:table-row>'
            '</table:table>'
        )
        self.assertEqual(result, {"Figures": [[12.5, None, None, "not available"]] * 2})

    def test_ods_rejects_missing_numeric_value_or_sheet_name(self) -> None:
        with self.assertRaisesRegex(ValueError, "office:value"):
            self.read_ods(
                '<table:table table:name="Figures"><table:table-row>'
                '<table:table-cell office:value-type="float"/>'
                '</table:table-row></table:table>'
            )
        with self.assertRaisesRegex(ValueError, "no name"):
            self.read_ods("<table:table/>")

    def test_csv_and_ons_keep_missing_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ons.csv").write_text(
                "\ufeffTitle,Employment rate\n2024,75.5\n2025,x\n2025 Q1,..\n2025 JAN,\n",
                encoding="utf-8",
            )
            (root / "rows.csv").write_text("Year,Estimate\n2025,12.5\n2026,\n", encoding="utf-8")
            with patch.object(readers, "ROOT", root):
                metadata, periods = readers.ons_series("ons.csv")
                self.assertEqual(metadata, {"Title": "Employment rate"})
                self.assertEqual(periods, {"2024": 75.5, "2025": None, "2025 Q1": None, "2025 JAN": None})
                self.assertEqual(readers.csv_rows("rows.csv")[1], {"Year": "2026", "Estimate": ""})

    def test_pdf_locator_selects_the_requested_number(self) -> None:
        with patch.object(readers, "pdf_pages", return_value=["Heading\nVisits 1,234.5 -6.2\n"]):
            self.assertEqual(readers.pdf_number("figures.pdf", "p1 after 'Heading' line 'Visits' number 2"), -6.2)

    def test_pdf_rejects_invalid_or_zero_based_locators(self) -> None:
        for locator in ("not a locator", "p0 after 'Heading' line 'Visits' number 1",
                        "p1 after 'Heading' line 'Visits' number 0"):
            with self.subTest(locator=locator), self.assertRaises(ValueError):
                readers.pdf_number("unused.pdf", locator)


class RateCalculations(unittest.TestCase):
    SOURCES = {
        "gov-income-tax-rates": {"retrieved": "retained date"},
        "gov-self-employed-ni": {"retrieved": "retained date"},
    }

    def test_employee_and_self_employed_values_remain_numeric(self) -> None:
        result = rates.read_rates(self.SOURCES)
        employee = result["illustration"]
        own_business = result["self_employed"]
        self.assertEqual(employee["allowance"], 12570)
        self.assertAlmostEqual(employee["income_tax"], 3486.0)
        self.assertAlmostEqual(employee["total"], employee["income_tax"] + employee["ni"])
        self.assertAlmostEqual(own_business["class4"], (30000 - 12570) * 0.06)
        self.assertLess(employee["average_rate"], employee["marginal"])
        self.assertEqual(result["retrieved"], "retained date")
        self.assertEqual(own_business["retrieved"], "retained date")

    def test_changed_source_wording_fails_instead_of_inventing_rates(self) -> None:
        with patch.object(rates, "_text", return_value="New page layout"):
            with self.assertRaisesRegex(SystemExit, "pages changed"):
                rates.read_rates(self.SOURCES)

    def test_salary_outside_supported_band_is_rejected(self) -> None:
        with self.assertRaisesRegex(SystemExit, "basic-rate band"):
            rates.read_rates(self.SOURCES, salary=100000)


class Downloads(unittest.TestCase):
    def setUp(self) -> None:
        downloads.FILES.clear()

    def tearDown(self) -> None:
        downloads.FILES.clear()

    def test_chart_json_keeps_numbers_and_missing_values(self) -> None:
        comment = downloads.chart_data(["Amount"], [["2025", 12.5], ["2026", None], ["2027", "no figure"]])
        self.assertEqual(downloads.figure_rows(comment),
                         [["Period", "Amount"], ["2025", 12.5], ["2026", None], ["2027", ""]])
        self.assertEqual(downloads.raw(None), "")
        self.assertEqual(downloads.raw(12.5000000001), "12.5")
        self.assertIsNone(downloads.figure_rows("<p>No data attached</p>"))

    def test_malformed_chart_data_is_rejected_at_the_json_boundary(self) -> None:
        payloads: list[object] = [
            [], {"names": "Amount", "rows": []}, {"names": [1], "rows": []},
            {"names": [], "rows": None}, {"names": [], "rows": [[]]},
            {"names": [], "rows": [["2025", {}]]},
        ]
        for payload in payloads:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                downloads.figure_rows("<!--csv:" + json.dumps(payload) + "-->")

    def test_chart_comment_does_not_close_early(self) -> None:
        comment = downloads.chart_data(["A--B"], [["2025", 1.0]])
        self.assertNotIn("--", comment[len("<!--csv:"):-len("-->")])
        self.assertEqual(downloads.figure_rows(comment), [["Period", "A--B"], ["2025", 1.0]])

    def test_download_links_keep_page_order_and_unique_relative_paths(self) -> None:
        table = (
            '<div class="tablewrap"><table><caption>Tax</caption>'
            '<tr><th>Year</th><th>Amount</th></tr>'
            '<tr><td>2025</td><td>£12.5</td></tr></table></div>'
        )
        html = downloads.add_links(table + table, "life/tax.html")
        self.assertIn('href="../csv/life/tax/tax.csv"', html)
        self.assertIn('href="../csv/life/tax/tax-2.csv"', html)
        exported = downloads.FILES["csv/life/tax/tax.csv"]
        self.assertTrue(exported.startswith("\ufeff"))
        self.assertEqual(list(csv.reader(io.StringIO(exported.lstrip("\ufeff")))),
                         [["Year", "Amount"], ["2025", "£12.5"]])

    def test_missing_comparison_label_stays_empty(self) -> None:
        self.assertEqual(downloads.list_rows("cmp-list", "<li><p>Missing label</p></li>"),
                         [["Measure", "Change"], ["", ""]])


class BuildVersion(unittest.TestCase):
    def tearDown(self) -> None:
        version.commit.cache_clear()

    def test_vercel_commit_takes_precedence(self) -> None:
        version.commit.cache_clear()
        with patch.dict("os.environ", {"VERCEL_GIT_COMMIT_SHA": " abcdef012345 "}):
            self.assertEqual(version.commit(), "abcdef012345")
            self.assertEqual(version.short(), "abcdef0")

    def test_unavailable_git_is_explicitly_unknown(self) -> None:
        version.commit.cache_clear()
        with patch.dict("os.environ", {"VERCEL_GIT_COMMIT_SHA": ""}):
            with patch.object(subprocess, "run", side_effect=OSError("git unavailable")):
                self.assertEqual(version.commit(), "unknown")
                self.assertEqual(version.short(), "unknown")


if __name__ == "__main__":
    unittest.main()
