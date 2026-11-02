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


class ComparisonPage(unittest.TestCase):
    """The two-year comparison leads with fixed figures and explains every gap in place."""

    def setUp(self):
        self.saved = list(pages_life.MEAS)
        f = Facts()
        for y, v in ((2010, 70.0), (2019, 74.0), (2025, 75.0)):
            f.add(Fact(f"work.rate.{y}", v, "%", str(y), "s", "A1"))
        for y, v in ((2019, 20.0), (2025, 26.0)):
            f.add(Fact(f"occ.{pages_life.occ_scheme(y)}.{y}", v, "%", str(y), "s", "B1"))
        for y, v in ((2010, 500.0), (2019, 520.0), (2025, 600.0)):
            f.add(Fact(f"pay.{y}", v, "£", str(y), "s", "C1"))
            f.add(Fact(f"paycash.{y}", v / 2, "£", str(y), "s", "D1"))
        for y, v in ((2010, 17.0), (2019, 19.0)):
            f.add(Fact(f"house.private.{y}", v, "%", str(y), "s", "E1"))
        self.facts = f
        self.num = Num(f)
        pages_life.MEAS[:] = [
            ("work.rate", "work", "Employment rate", lambda y: f"work.rate.{y}", "pct", "pp", str, None),
            ("work.occ.prof", "work", "Share of workers in: Professional", lambda y: f"occ.{pages_life.occ_scheme(y)}.{y}", "pct", "pp", str, pages_life.occ_scheme),
            ("earn.ft", "earnings", "Pay", lambda y: f"pay.{y}", "pounds", "pct", str, None),
            ("earn.ftcash", "earnings", "Pay in cash", lambda y: f"paycash.{y}", "pounds", "pct", str, None),
            ("house.private", "housing", "Renting privately", lambda y: f"house.private.{y}", "pct", "pp", str, None),
        ]

    def tearDown(self):
        pages_life.MEAS[:] = self.saved

    def m(self, key):
        return next(m for m in pages_life.MEAS if m[0] == key)

    def test_status(self):
        self.assertEqual(pages_life._status(self.facts, self.m("work.rate"), 2010, 2025), "ok")
        self.assertEqual(pages_life._status(self.facts, self.m("work.occ.prof"), 2019, 2025), "break")
        self.assertEqual(pages_life._status(self.facts, self.m("house.private"), 2010, 2025), "missing")

    def test_largest_changes_leave_out_breaks_gaps_and_cash(self):
        out = pages_life.largest_changes(self.facts, self.num, 2019, 2025)
        self.assertIn("Employment rate", out)
        self.assertIn("Pay", out)
        self.assertNotIn("Professional", out)
        self.assertNotIn("Renting privately", out)
        self.assertNotIn("Pay in cash", out)

    def test_missing_figure_is_explained_with_nearest_pair(self):
        out = pages_life.key_sentence(self.facts, self.num, "housing", 2010, 2025)
        self.assertIn("not compared", out)
        self.assertIn("not yet published", out)
        self.assertIn('href="2010-2019.html"', out)
        self.assertNotIn("data-change", out)

    def test_definition_change_is_explained_and_not_calculated(self):
        pages_life.KEY_MEASURES["work"], saved = ("work.occ.prof", "Professional share"), pages_life.KEY_MEASURES["work"]
        try:
            out = pages_life.key_sentence(self.facts, self.num, "work", 2019, 2025)
        finally:
            pages_life.KEY_MEASURES["work"] = saved
        self.assertIn("not compared", out)
        self.assertIn("SOC2010 to SOC2020", out)
        self.assertNotIn("data-change", out)

    def test_lead_sentence_says_direction_and_change(self):
        out = pages_life.key_sentence(self.facts, self.num, "work", 2010, 2025)
        self.assertIn("went up from", out)
        self.assertIn("+5.0 percentage points", out)

    def test_small_percentage_changes_keep_a_decimal(self):
        out = pages_life.change_cell(self.facts, self.num, "pay.2010", "pay.2019", "pct", "pounds")
        self.assertIn("+4.0%", out)

    def test_shared_label_prefix_is_written_once(self):
        self.assertEqual(pages_life._join_labels(["Share in: A", "Share in: B"]), "Share in: A; B")


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


class Holidays(unittest.TestCase):
    def test_only_single_countries_are_ranked(self):
        from builder.data import _country_rows
        rows = [["Spain", 5], ["Rest of Europe", 9], ["Total World", 99], ["- of which EU", 50], ["Other Asia", 3], ["USA", 4], ["Fly/cruise (stay onboard)", 1]]
        self.assertEqual([n for n, _ in _country_rows(rows, 0, 0, [1])], ["Spain", "United States"])

    def test_survey_change_blocks_comparison(self):
        self.assertNotEqual(pages_life.gb_survey(2019), pages_life.gb_survey(2022))
        self.assertEqual(pages_life.gb_survey(2022), pages_life.gb_survey(2025))


class Explanations(unittest.TestCase):
    """Quoted explanations must match their source and always say who said them."""

    def setUp(self):
        from builder.sources import all_sources
        from builder import explain
        self.explain, self.sources = explain, all_sources()

    def test_every_quote_is_in_its_source(self):
        self.assertEqual(self.explain.missing_quotes(self.sources), [])

    def test_a_changed_quote_is_caught(self):
        key = next(iter(self.explain.EXPLANATIONS))
        e = self.explain.EXPLANATIONS[key]
        original = e["quote"]
        try:
            e["quote"] = [original[0].replace(" ", "  ", 1) + " and more"]
            self.assertTrue(self.explain.missing_quotes(self.sources))
        finally:
            e["quote"] = original

    def test_box_names_the_publisher_and_links_the_source(self):
        for key, e in self.explain.EXPLANATIONS.items():
            out = self.explain.box(key, self.sources)
            self.assertIn(f"In the words of the {e['publisher']}", out)
            self.assertIn("<blockquote", out)
            self.assertIn(f'methods.html#src-{e["source"]}', out)
            self.assertIn(self.sources[e["source"]]["page"], out)

    def test_life_quotes_have_a_topic_and_years(self):
        for key, e in self.explain.EXPLANATIONS.items():
            if "topic" in e:
                self.assertIn(e["topic"], {t[0] for t in pages_life.TOPICS}, key)
                self.assertTrue(set(e["years"]) <= set(pages_life.YEARS), key)
