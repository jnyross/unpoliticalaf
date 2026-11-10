"""Focused regressions for fiscal downloads, status and source populations."""

import unittest

import openpyxl

from builder.data import Fact, Facts, who_pays
from builder.check_calculations import check_input_statuses
from builder.downloads import figure_rows
from builder.html import line_chart
from builder.readers import ROOT
from builder.trace import add_trace, figure_pages


class FiscalConformance(unittest.TestCase):
    def test_chart_csv_retains_forecast_and_projection_periods(self):
        for future in ("forecast", "projection"):
            chart = line_chart(
                "Tax over time",
                ["2023", "2024", "2025"],
                [("Tax", [1, None, 3], "a")],
                "£ billion",
                kind="bn",
                forecast_from=1,
                future=future,
            )
            rows = figure_rows(chart)
            self.assertEqual(
                rows[1:],
                [["2023", "£1.0bn"], [f"2024 ({future})", ""], [f"2025 ({future})", "£3.0bn"]],
            )

    def test_calculated_download_retains_transitive_input_statuses(self):
        facts = Facts()
        facts.add(Fact("actual", 1, "£bn", "2025", "s", "A1", "outturn"))
        facts.add(Fact("future", 2, "£bn", "2026", "s", "A2", "forecast"))
        for fid, inputs, value in (
            ("derived", ["actual", "future"], 3),
            ("nested", ["derived"], 3),
        ):
            facts.add(
                Fact(
                    fid,
                    value,
                    "£bn",
                    "2026",
                    "s",
                    "",
                    "calculated",
                    formula=" + ".join(inputs),
                    inputs=inputs,
                )
            )
        rows = {f["id"]: f for f in facts.to_json()}
        self.assertEqual(rows["nested"]["input_statuses"], ["forecast", "outturn"])
        errors = []
        check_input_statuses(rows, errors.append)
        self.assertEqual(errors, [])
        rows["nested"]["input_statuses"] = ["outturn"]
        check_input_statuses(rows, errors.append)
        self.assertTrue(any("nested: input_statuses" in error for error in errors))
        source = {
            "s": dict(
                title="Source",
                publisher="Publisher",
                geography="UK",
                population="UK",
                published="2026",
                page="https://example.org",
                file="data/example",
                licence="OGL",
                retrieved="2026",
                sha256="a",
            )
        }
        records = figure_pages(facts, source, {"nested"})["figures/s.html"]
        self.assertIn("Forecast by the publisher", records)
        traced = add_trace('<data data-fact="nested">3</data></body>', "taxes.html", facts, source)
        self.assertIn("Forecast by the publisher", traced)

    def test_retired_population_matches_current_original_not_old_bulletin(self):
        wb = openpyxl.load_workbook(
            ROOT / "data/payers/raw/ons-etb-fye2024.xlsx", read_only=True, data_only=True
        )
        try:
            notes = {
                row[0]: " ".join(str(v) for v in row if v is not None)
                for row in wb["Notes"].iter_rows(values_only=True)
                if row[0]
            }
            self.assertIn("more than 50%", notes["note 12"])
            self.assertIn("aged over 50", notes["note 12"])
            for sheet in ("Table 3a", "Table 4a"):
                self.assertIn("individuals", wb[sheet]["A1"].value)
        finally:
            wb.close()
        facts = Facts()
        who_pays(facts)
        for group in ("ret", "nonret"):
            for measure in ("gross", "direct", "indirect", "alltax"):
                self.assertIn("person-weighted", facts[f"etb.{group}.{measure}.all"].note)
