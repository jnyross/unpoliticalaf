"""Fast checks of the rules the site promises. Run with: make test"""
import re
import unittest

from builder.data import Fact, Facts
from builder.html import fmt, line_chart, Num
from builder import pages_life


class Formatting(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(fmt(1360.1, "bn"), "£1,360bn")
        self.assertEqual(fmt(50.43, "bn"), "£50.4bn")
        self.assertEqual(fmt(33.18, "per100"), "£33")
        self.assertEqual(fmt(27.25, "pct"), "27.2%")
        self.assertEqual(fmt(58712, "millions"), "58.7 million")
        self.assertIsNone(fmt(None, "pct"))

    def test_missing_figure_is_not_zero(self):
        facts = Facts()
        facts.add(Fact("x.2020", None, "%", "2020", "s", "A1"))
        num = Num(facts)
        out = num("x.2020", "pct")
        self.assertIn("not available", out)
        self.assertNotIn("0", re.sub(r"<[^>]+>", "", out))


class Charts(unittest.TestCase):
    def test_gap_breaks_the_line(self):
        svg = line_chart("t", ["2018", "2019", "2020", "2021"], [("a", [1, 2, None, 4], "a")], "units")
        # Two separate pieces: a path for 2018-2019 and a single point for 2021. Nothing is drawn through 2020.
        self.assertEqual(svg.count("<path"), 1)
        self.assertEqual(svg.count("<circle"), 1)

    def test_definition_break_splits_the_line(self):
        svg = line_chart("t", ["1", "2", "3", "4"], [("a", [1, 2, 3, 4], "a")], "u", breaks=[(2, "New method")], split_breaks=True)
        self.assertEqual(svg.count("<path"), 2)

    def test_axis_labels_are_not_rounded_away(self):
        svg = line_chart("t", ["2018", "2019", "2020"], [("a", [0.5, 6, 9.4], "a")], "units", ymin=0)
        labels = re.findall(r'text-anchor="end">([0-9.,]+)</text>', svg)
        self.assertIn("2.5", labels)
        self.assertIn("7.5", labels)

    def test_room_counts_not_compared_across_definition_change(self):
        self.assertNotEqual(pages_life.rooms_basis(2010), pages_life.rooms_basis(2011))
        self.assertEqual(pages_life.rooms_basis(2011), pages_life.rooms_basis(2024))

    def test_chart_has_text_alternative(self):
        svg = line_chart("Title", ["1", "2"], [("a", [1, 2], "a")], "u")
        self.assertIn('role="img"', svg)
        self.assertIn("aria-label", svg)


class Comparisons(unittest.TestCase):
    def setUp(self):
        self.facts = Facts()
        self.facts.add(Fact("r.2010", 20.0, "%", "2010", "s", "A1"))
        self.facts.add(Fact("r.2020", 25.0, "%", "2020", "s", "A2"))
        self.facts.add(Fact("m.2010", None, "%", "2010", "s", "A3"))
        self.num = Num(self.facts)

    def test_percentage_points(self):
        out = pages_life.change_cell(self.facts, self.num, "r.2010", "r.2020", "pp", "pct")
        self.assertIn("+5.0 percentage points", out)

    def test_no_change_without_both_years(self):
        out = pages_life.change_cell(self.facts, self.num, "m.2010", "r.2020", "pp", "pct")
        self.assertIn("no figure", out)


class Rates(unittest.TestCase):
    def test_worked_example_from_saved_pages(self):
        from builder.rates import read_rates
        from builder.sources import all_sources
        r = read_rates(all_sources())
        ill = r["illustration"]
        self.assertEqual(ill["allowance"], 12570)
        self.assertAlmostEqual(ill["income_tax"], (30000 - 12570) * 0.20)
        self.assertGreater(ill["average_rate"], 0)
        self.assertLess(ill["average_rate"], ill["marginal"])


class Sources(unittest.TestCase):
    def test_hashes_match(self):
        from builder.sources import all_sources, verify_hashes
        self.assertEqual(verify_hashes(all_sources()), [])


if __name__ == "__main__":
    unittest.main()
