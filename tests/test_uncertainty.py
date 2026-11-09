"""Margins of error: shown only where the publisher gives one, and checked honestly."""

import unittest
from unittest.mock import patch

from builder import uncertainty as U
from builder.data import Fact, Facts, build_all
from builder.html import fmt, Num


class Formatting(unittest.TestCase):
    def test_margin_formats(self):
        self.assertEqual(fmt(0.4, "pm_pp"), "±0.4 points")
        self.assertEqual(fmt(1.5025, "pm_pounds"), "±£2")
        self.assertEqual(fmt(1.428, "pm_pct"), "±1.4%")
        self.assertEqual(fmt(12.3, "pm_pct"), "±12%")


class ChangeCheck(unittest.TestCase):
    def setUp(self):
        self.facts = Facts()
        for fid, v in (("a", 70.0), ("b", 71.0), ("ma", 0.6), ("mb", 0.8)):
            self.facts.add(Fact(fid, v, "%", "x", "s", "A1"))
        U.MARGINS.clear()
        U.MARGINS.update({"a": ("ma", "pm_pp"), "b": ("mb", "pm_pp")})

    def tearDown(self):
        U.MARGINS.clear()

    def test_combined_margin(self):
        ch, m = U.change_check(self.facts, "a", "b")
        self.assertAlmostEqual(ch, 1.0)
        self.assertAlmostEqual(m, 1.0)  # √(0.6² + 0.8²)

    def test_change_within_margin_is_called_possible_noise(self):
        s = U.check_sentence(self.facts, Num(self.facts), "a", "b", "pp", ("2015", "2025"))
        self.assertIn("could be sampling noise", s)
        self.assertNotIn("unlikely", s)

    def test_no_margin_no_sentence(self):
        U.MARGINS.pop("b")
        self.assertEqual(U.check_sentence(self.facts, Num(self.facts), "a", "b", "pp"), "")
        self.assertEqual(U.pm(Num(self.facts), "b"), "")


class RealData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for state in (U.MARGINS, U.INFO):
            preserved_state = patch.dict(state)
            preserved_state.start()
            cls.addClassCleanup(preserved_state.stop)
        cls.facts, cls.d = build_all()
        U.add_facts(cls.facts, cls.d)

    def test_margins_only_from_publishers_that_give_them(self):
        allowed = {
            "nomis-aps-emp-places-ci",
            "nomis-ashe-resident-cv",
            "ashe-2025-table1-revised",
            "ashe-2026-table1-provisional",
            "nomis-ashe-places",
            "ott-2009to2019",
            "ott-2019to2023",
            "ott-2024",
            "ott-2025",
            "ons-lfs-a11",
        }
        for fid, (mid, _) in U.MARGINS.items():
            self.assertIn(self.facts[mid].source, allowed, mid)
        for prefix in ("house.", "school.", "hol.gb.", "etb.", "hmrc.", "spend.", "rec."):
            self.assertFalse([f for f in U.MARGINS if f.startswith(prefix)], prefix)

    def test_headline_margins_exist(self):
        for fid in (
            "earn.ft.2025",
            "earn.ft.2026",
            "earn.real.ft.2015",
            "work.place.wales.2025",
            "hol.world.holiday.2025",
            "hol.cty.spain.all.2015",
        ):
            self.assertIn(fid, U.MARGINS)
        self.assertEqual(self.facts["moe.lfs.rate.latest"].value, 0.4)
        self.assertEqual(self.facts["moe.lfs.rate.change_year"].value, 0.6)

    def test_margin_follows_the_published_cv(self):
        f = self.facts
        self.assertAlmostEqual(
            f["moe.earn.ft.2025"].value,
            f["earn.ft.2025"].value * 1.96 * f["cv.earn.ft.2025"].value / 100,
        )

    def test_no_margin_for_ireland(self):
        # ONS's interval leaves out land-border trips that the published figure includes
        self.assertFalse([f for f in U.MARGINS if "ireland" in f])

    def test_no_margin_before_2024_for_holidays_alone(self):
        self.assertNotIn("hol.world.holiday.2019", U.MARGINS)


if __name__ == "__main__":
    unittest.main()
