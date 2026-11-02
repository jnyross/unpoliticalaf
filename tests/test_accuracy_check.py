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


class Calculations(unittest.TestCase):
    def test_formula_text_is_evaluated(self):
        self.assertAlmostEqual(ac.evaluate("100 × a.1 ÷ a.10", {"a.1": 5, "a.10": 20}), 25)
        self.assertAlmostEqual(ac.evaluate("t − sum of the two named groups", {"t": 10, "x": 3, "y": 2}, ["t", "x", "y"]), 5)

    def test_page_rounding(self):
        self.assertTrue(ac.page_matches({"text": "£44.2bn", "value": 44.24, "kind": "bn"})[0])
        self.assertFalse(ac.page_matches({"text": "£44.2bn", "value": 44.26, "kind": "bn"})[0])
        self.assertTrue(ac.page_matches({"text": "32.9 million", "value": 32912.0, "kind": "millions"})[0])


if __name__ == "__main__":
    unittest.main()
