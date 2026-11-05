"""The recorded random-sample accuracy check stays complete and readable."""

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "docs/accuracy-check"
spec = importlib.util.spec_from_file_location("accuracy_check", ROOT / "scripts/accuracy_check.py")
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)


class RecordedCheck(unittest.TestCase):
    def test_results_cover_the_sample_and_all_match(self):
        sample = json.loads((DIR / "sample.json").read_text())
        results = json.loads((DIR / "results.json").read_text())
        self.assertGreaterEqual(len(sample["items"]), 40)
        self.assertEqual([i["id"] for i in sample["items"]], [r["id"] for r in results["results"]])
        for r in results["results"]:
            self.assertTrue(r["page_matches_fresh_source"], r["id"])
            self.assertTrue(all(c["match"] for c in r["cells"]), r["id"])


class JsonReader(unittest.TestCase):
    IMF = json.dumps(
        {"values": {"GG_DEBT_GDP": {"GBR": {"2023": 100.1, "2024": 101.28941}}}, "api": {}}
    ).encode()

    def test_imf_datamapper_value_is_read_by_indicator_country_and_year(self):
        self.assertEqual(ac.read_cell(self.IMF, "x.json", "values.GG_DEBT_GDP.GBR.2024"), 101.28941)

    def test_missing_imf_year_is_an_error_not_a_zero(self):
        with self.assertRaises(ValueError):
            ac.read_cell(self.IMF, "x.json", "values.GG_DEBT_GDP.GBR.2030")

    def test_recorded_imf_cell_reads_from_the_repository_copy(self):
        body = (ROOT / "data/fetched/imf/weo-gg-debt-gdp.json").read_bytes()
        value = ac.read_cell(
            body, "data/fetched/imf/weo-gg-debt-gdp.json", "values.GG_DEBT_GDP.GBR.2024"
        )
        self.assertAlmostEqual(value, 101.28941)


class Calculations(unittest.TestCase):
    def test_formula_text_is_evaluated(self):
        self.assertAlmostEqual(ac.evaluate("100 × a.1 ÷ a.10", {"a.1": 5, "a.10": 20}), 25)
        self.assertAlmostEqual(
            ac.evaluate(
                "t − sum of the two named groups", {"t": 10, "x": 3, "y": 2}, ["t", "x", "y"]
            ),
            5,
        )

    def test_formula_ending_with_its_period_is_evaluated(self):
        values = {"a.2025-26": 1, "b.2025-26": 2, "c.2025-26": 6}
        self.assertAlmostEqual(ac.evaluate("100 × (a + b) ÷ c, 2025-26", values, list(values)), 50)

    def test_total_less_named_taxes_is_evaluated(self):
        values = {"t.2025-26": 10, "x.2025-26": 3, "y.2025-26": 2}
        self.assertAlmostEqual(
            ac.evaluate("t.2025-26 − sum of the named taxes", values, list(values)), 5
        )

    def test_page_rounding(self):
        self.assertTrue(ac.page_matches({"text": "£44.2bn", "value": 44.24, "kind": "bn"})[0])
        self.assertFalse(ac.page_matches({"text": "£44.2bn", "value": 44.26, "kind": "bn"})[0])
        self.assertTrue(
            ac.page_matches({"text": "32.9 million", "value": 32912.0, "kind": "millions"})[0]
        )


if __name__ == "__main__":
    unittest.main()
