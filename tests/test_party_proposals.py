"""Real retained proposal boundaries; these checks are NOT fiscal/editorial review."""
import copy
from datetime import date
import hashlib
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from party_data import load_json, retained_bytes, validate, validate_files
from party_proposals import pinned_source


class ExtractedProposalTests(unittest.TestCase):
    def setUp(self):
        self.data = load_json((ROOT / "data/parties.json").read_bytes())
        self.manifest = load_json((ROOT / "data/party-sources.json").read_bytes())
        self.proposals = {p["id"]: p for party in self.data["parties"] for p in party["proposals"]}

    def check(self, **kwargs):
        return validate(self.data, self.manifest, as_of=date(2026, 10, 30), **kwargs)

    def test_all_numbered_libdem_costs_notes_years_and_revenue(self):
        # Independently transcribed from retained physical pages 3 and 6,
        # not derived from the implementation's extraction regex.
        expected = ["8350", "1450", "2960", "2170", "1500", "4060", "970", "570", "6700",
                    "100", "2890", "-4290", "-630", "4250", "5210", "2120", "2090", "1420",
                    "260", "290", "380", "3620", "7230"]
        for number, amount in enumerate(expected, 1):
            p = self.proposals[f"libdem-2024-costings-row-{number}"]
            field = "costs_claimed" if number <= 13 else "funding_claimed"
            self.assertEqual(p[field]["items"][0]["amount"], amount)
            self.assertEqual(p[field]["items"][0]["unit"], "GBP million")
            self.assertEqual(p[field]["items"][0]["basis"], "annual")
            self.assertTrue(p["evidence"]["quote"].startswith(f"{number}. "))
            self.assertEqual(p["fiscal_year"], "2028-29")
            self.assertIsNone(p["proposal_date"])
        self.assertEqual(self.proposals["libdem-2024-costings-current-spending-total"]["costs_claimed"]["items"][0]["amount"], "26800")
        self.assertEqual(self.proposals["libdem-2024-costings-revenue-total"]["funding_claimed"]["items"][0]["amount"], "26870")
        self.assertNotIn("libdem-2024-plain-text", {s["id"] for s in self.manifest["sources"]})

    def test_capital_total_components_and_reallocation_are_distinct(self):
        p = self.proposals["libdem-2024-costings-capital"]
        self.assertEqual([i["amount"] for i in p["costs_claimed"]["items"]],
                         ["19.7", "1.1", "1.9", "8.4", "1.2", "6.2", "1.9"])
        self.assertEqual(p["funding_claimed"]["items"][0]["amount"], "0.9")
        self.assertIsNone(p["fiscal_year"])
        self.assertIn("average", p["evidence"]["quote"])
        self.assertIn("reallocation", p["baseline"])

    def test_green_appendix_complete_row_counts_units_and_final_year(self):
        records = [p for k, p in self.proposals.items() if k.startswith("green-2024-")]
        self.assertEqual(len(records), 20)  # 19 fiscal rows including subtotals/debt + notes.
        for p in records:
            if p["id"].endswith("appendix-notes"):
                continue
            self.assertEqual(p["fiscal_year"], "2029-30")
            for field in ("costs_claimed", "funding_claimed"):
                for item in p[field]["items"]:
                    self.assertEqual(item["unit"], "GBP billion")
                    self.assertEqual(item["basis"], "annual")
        p = self.proposals["green-2024-borrowing-1"]
        self.assertEqual(p["funding_claimed"]["items"][0]["amount"], "79.5")
        self.assertIn("85.3", p["evidence"]["quote"])  # Preserve first-year value too.

    def test_reform_annualised_totals_and_each_component_not_outturn(self):
        costs = self.proposals["reform-2024-pdf-costs"]
        savings = self.proposals["reform-2024-pdf-savings"]
        self.assertEqual([i["amount"] for i in costs["costs_claimed"]["items"]],
                         ["141", "70", "18", "17", "3", "2", "5", "14", "8", "2", "2"])
        self.assertEqual([i["amount"] for i in savings["funding_claimed"]["items"]],
                         ["150", "5", "4", "30", "15", "5", "50", "35", "6"])
        self.assertIsNone(costs["fiscal_year"])
        self.assertIn("Historical 2024", costs["scope"])

    def test_restore_differences_remain_visible_not_silently_reconciled(self):
        summary = self.proposals["restore-economic-plan-pdf-income-tax"]
        detail = self.proposals["restore-economic-plan-pdf-income-detail"]
        self.assertEqual(summary["costs_claimed"]["items"][0]["amount"], "49")
        self.assertEqual(detail["costs_claimed"]["items"][0]["amount"], "49.2")
        self.assertIn("around £50 billion", detail["evidence"]["quote"])
        self.assertIn(detail["id"], summary["overlaps_with"])
        welfare = self.proposals["restore-economic-plan-pdf-welfare"]
        self.assertIn("£70-80 billion per annum", welfare["evidence"]["quote"])
        self.assertEqual(welfare["funding_claimed"]["items"], [])  # No invented range midpoint.

    def test_unknown_date_and_unresolved_provenance_cannot_be_promoted(self):
        for key in ("uup-2024", "sdlp-2024", "libdem-2024-plain-text"):
            with self.assertRaises(ValueError):
                pinned_source(key)
        src = next(s for s in self.manifest["sources"] if s["id"] == "libdem-2024-costings")
        for field, value in (("published_on", "2024-06-10"), ("party_id", "4"),
                             ("url", "https://example.invalid/plan.pdf")):
            altered = copy.deepcopy(self.manifest)
            next(s for s in altered["sources"] if s["id"] == src["id"])[field] = value
            with self.assertRaisesRegex(ValueError, "pinned publication provenance"):
                validate(self.data, altered, as_of=date(2026, 10, 30))
        next(p for p in self.data["parties"] if p["id"] == "17")["official_domain"] = "example.invalid"
        with self.assertRaisesRegex(ValueError, "pinned party official domain"):
            self.check()

    def test_corrupt_pinned_text_and_validly_rehashed_replacement_refused(self):
        src = next(s for s in self.manifest["sources"] if s["id"] == "green-2024")
        bad = retained_bytes(src["path"]) + b" changed"
        def read(path):
            return bad if path == src["path"] else retained_bytes(path)
        with self.assertRaisesRegex(ValueError, "pinned proposal text changed"):
            self.check(read=read)
        src["sha256"] = hashlib.sha256(bad).hexdigest()
        with self.assertRaisesRegex(ValueError, "pinned publication provenance"):
            self.check(read=read)

    def test_actual_negative_amount_quote_missingness_and_review_gates(self):
        p = self.proposals["libdem-2024-costings-row-1"]
        p["costs_claimed"]["items"][0]["amount"] = "0"
        with self.assertRaisesRegex(ValueError, "amount absent"):
            self.check()
        p["costs_claimed"]["items"][0]["amount"] = "8350"
        p["funding_claimed"]["items"] = [{"amount": "0"}]
        with self.assertRaisesRegex(ValueError, "missing is not zero"):
            self.check()
        self.setUp()
        report = self.check()
        self.assertFalse(report["public_accepted"])
        self.assertFalse(report["proposal_coverage_complete"])
        self.assertFalse(report["review_bindings_complete"])
        for option in ("require_coverage", "require_reviews"):
            with self.assertRaises(ValueError):
                validate_files(as_of=date(2026, 10, 30), **{option: True})


if __name__ == "__main__":
    unittest.main()
