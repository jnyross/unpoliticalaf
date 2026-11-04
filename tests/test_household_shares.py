"""The richest fifth's share of all household taxes (ONS Table 2a, goal gap: audit 15 item 1)."""
import unittest

from builder.data import Fact, Facts
from builder.pages_money import FIFTHS, household_tax_shares

# ONS Table 2a, financial year 2023/24: average taxes per household (£) and households (thousands).
TABLE_2A = {
    "q1": (8625, 5875), "q2": (12380, 5902), "q3": (17338, 5559), "q4": (25280, 5298), "q5": (51903, 5806),
}


def _facts():
    facts = Facts()
    for q, (tax, hh) in TABLE_2A.items():
        facts.add(Fact(f"etb.2a.alltax.{q}", tax, "£ a year per household", "2023/24", "etb", "Table 2a!x", "calculated"))
        facts.add(Fact(f"etb.2a.households.{q}", hh, "thousands of households", "2023/24", "etb", "Table 2a!y", "outturn"))
    return facts


class HouseholdTaxShares(unittest.TestCase):
    def setUp(self):
        self.facts = _facts()
        household_tax_shares(self.facts)

    def test_shares_add_up_to_one_hundred(self):
        total = sum(self.facts[f"etb.2a.taxshare.{q}"].value for q in FIFTHS)
        self.assertAlmostEqual(total, 100, places=9)

    def test_richest_fifth_share_matches_hand_calculation(self):
        # £51,903 × 5,806 thousand households = £301.3bn out of £655.3bn in all five fifths.
        self.assertAlmostEqual(self.facts["etb.2a.taxshare.q5"].value, 46.0, delta=0.05)

    def test_shares_are_labelled_as_household_taxes_not_revenue(self):
        self.assertEqual(self.facts["etb.2a.taxshare.q5"].unit, "% of all household taxes")

    def test_no_fifth_is_missing(self):
        for q in FIFTHS:
            self.assertIsNotNone(self.facts[f"etb.2a.taxshare.{q}"].value)


if __name__ == "__main__":
    unittest.main()
