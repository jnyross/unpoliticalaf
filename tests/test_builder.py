"""Fast checks of the rules the site promises. Run with: make test"""
import re
import unittest

from builder.data import Fact, Facts
from builder.html import fmt, line_chart, small_multiples, Num
from builder import pages_life, pages_ranges


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

    def test_summary_reads_first_latest_high_low_and_gaps(self):
        svg = line_chart("t", ["2018", "2019", "2020", "2021", "2022"], [("a", [5.0, 9.0, None, 2.0, 4.0], "a")], "u", kind="pct")
        text = re.sub(r"<[^>]+>", "", svg.split('class="csum"')[1])
        self.assertIn("5.0% in 2018 and 4.0% in 2022", text)
        self.assertIn("highest 9.0% (2019)", text)
        self.assertIn("lowest 2.0% (2021)", text)
        self.assertIn("No figure for 2020", text)

    def test_summary_does_not_compare_across_a_definition_break(self):
        svg = line_chart("t", ["1", "2", "3", "4", "5", "6"], [("a", [1.0, 9.0, 2.0, 3.0, 0.5, 4.0], "a")], "u",
                         breaks=[(3, "New method")], kind="dp1")
        text = re.sub(r"<[^>]+>", "", svg.split('class="csum"')[1])
        self.assertIn("1 to 3: 1.0 in 1 and 2.0 in 3", text)
        self.assertIn("4 to 6: 3.0 in 4 and 4.0 in 6", text)
        self.assertNotIn("9.0 in 1", text)

    def test_summary_keeps_forecasts_apart(self):
        svg = line_chart("t", ["1", "2", "3", "4"], [("a", [1.0, 2.0, 3.0, 99.0], "a")], "u", forecast_from=3, kind="dp1")
        text = re.sub(r"<[^>]+>", "", svg.split('class="csum"')[1])
        self.assertIn("1.0 in 1 and 3.0 in 3", text)
        self.assertIn("Forecast for 4: 99.0", text)
        self.assertIn("forecasts, not measurements", text)

    def test_summary_numbers_are_traceable_figures(self):
        facts = Facts()
        for i, v in enumerate([1.0, 2.0, 3.0]):
            facts.add(Fact(f"x.{i}", v, "%", str(i), "s", f"A{i + 1}"))
        svg = line_chart("t", ["0", "1", "2"], [("a", [1.0, 2.0, 3.0], "a")], "u", kind="pct", num=Num(facts), ids=[["x.0", "x.1", "x.2"]])
        summary = svg.split('class="csum"')[1]
        self.assertIn('data-fact="x.0"', summary)
        self.assertIn('data-fact="x.2"', summary)

    def test_events_do_not_split_the_summary(self):
        svg = line_chart("t", ["1", "2", "3"], [("a", [1.0, 5.0, 2.0], "a")], "u", events=[(1, "Covid")], kind="dp1")
        text = re.sub(r"<[^>]+>", "", svg.split('class="csum"')[1])
        self.assertIn("1.0 in 1 and 2.0 in 3", text)
        self.assertIn("not what it caused", text)

    def test_chart_has_text_alternative(self):
        svg = line_chart("Title", ["1", "2"], [("a", [1, 2], "a")], "u")
        self.assertIn('role="img"', svg)
        self.assertIn("aria-label", svg)


class ChartMarks(unittest.TestCase):
    def test_axis_labels_hidden_inside_chart_images(self):
        from builder.html import hide_chart_marks
        out = hide_chart_marks('<svg role="img" aria-label="x"><text>0</text></svg><svg><text>a</text></svg>')
        self.assertEqual(out, '<svg role="img" aria-label="x"><g aria-hidden="true"><text>0</text></g></svg><svg><text>a</text></svg>')
        self.assertEqual(hide_chart_marks(out), out)  # running twice changes nothing


class SmallMultiples(unittest.TestCase):
    SERIES = [("North", [1.0, 2.0, 3.0]), ("South", [4.0, None, 6.0]), ("East", [7.0, 8.0, 9.0]), ("West", [None, None, None])]

    def test_one_labelled_panel_per_group(self):
        fig = small_multiples("t", ["1", "2", "3"], self.SERIES, "u", "dp1")
        self.assertEqual(fig.count('role="img"'), 4)
        for name, _ in self.SERIES[:3]:
            self.assertIn(f'aria-label="{name}: ', fig)
        # Each panel's spoken name gives its latest figure; a panel with none gives just the name
        self.assertIn('aria-label="South: 6.0 in 3"', fig)
        self.assertIn('aria-label="West"', fig)
        self.assertIn("No figures", fig)  # a group with no data says so, it is not drawn as zero

    def test_gaps_are_not_joined(self):
        fig = small_multiples("t", ["1", "2", "3"], self.SERIES, "u", "dp1")
        south = re.search(r'<path id="sm\d+s1" d="([^"]+)"', fig).group(1)
        self.assertEqual(south.count("M"), 2)

    def test_one_readout_and_summary_for_all_panels(self):
        fig = small_multiples("t", ["1", "2", "3"], self.SERIES, "u", "dp1")
        self.assertEqual(fig.count("data-chart="), 1)
        self.assertIn("<strong>South</strong>", fig)
        self.assertIn("No figure for 2", fig)

    def test_definition_break_splits_lines_and_summary(self):
        fig = small_multiples("t", ["1", "2", "3", "4"], [("a", [1.0, 2.0, 3.0, 4.0]), ("b", [1.0, 1.0, 1.0, 1.0])], "u", "dp1",
                              breaks=[(2, "New method")], split_breaks=True)
        a = re.search(r'<path id="sm\d+s0" d="([^"]+)"', fig).group(1)
        self.assertEqual(a.count("M"), 2)
        self.assertIn("values either side are not compared", fig)


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


class SpanComparisons(unittest.TestCase):
    """Averages over several years: only when every year has a figure measured the same way."""

    def setUp(self):
        self.saved = list(pages_life.MEAS)
        f = Facts()
        for y in range(2008, 2026):
            f.add(Fact(f"rate.{y}", 60.0 + y - 2008, "%", str(y), "s", "A1"))
            if y != 2016:
                f.add(Fact(f"gap.{y}", 10.0, "%", str(y), "s", "B1"))
            f.add(Fact(f"occ.{y}", 20.0, "%", str(y), "s", "C1"))
        self.facts = f
        pages_life.MEAS[:] = [
            ("work.rate", "work", "Employment rate", lambda y: f"rate.{y}", "pct", "pp", str, None),
            ("work.gap", "work", "Has a gap", lambda y: f"gap.{y}", "pct", "pp", str, None),
            ("work.occ.prof", "work", "Professional", lambda y: f"occ.{y}", "pct", "pp", str, pages_life.occ_scheme),
            ("house.crowd.all", "housing", "Overcrowded", lambda y: f"rate.{y}", "pct", "pp", str, None),
        ]
        pages_ranges.add_range_facts(f)
        self.num = Num(f)

    def tearDown(self):
        pages_life.MEAS[:] = self.saved

    def m(self, key):
        return next(m for m in pages_life.MEAS if m[0] == key)

    def test_average_is_recorded_with_its_formula(self):
        a = self.facts["avg.work.rate.2009-2011"]
        self.assertAlmostEqual(a.value, 62.0)
        self.assertEqual(a.status, "calculated")
        self.assertEqual(a.inputs, ["rate.2009", "rate.2010", "rate.2011"])
        self.assertEqual(a.formula, "(rate.2009 + rate.2010 + rate.2011) ÷ 3")

    def test_no_average_over_a_missing_year_or_a_definition_change(self):
        self.assertNotIn("avg.work.gap.2015-2017", self.facts)
        self.assertIn("avg.work.gap.2017-2019", self.facts)
        self.assertNotIn("avg.work.occ.prof.2019-2021", self.facts)  # SOC changed in 2021
        self.assertNotIn("avg.house.crowd.all.2009-2011", self.facts)  # already a three-year average
        out = pages_ranges._not_compared(self.facts, self.m("work.gap"), (2015, 2017), (2019, 2021))
        self.assertIn("no figure for 2016", out)
        out = pages_ranges._not_compared(self.facts, self.m("work.occ.prof"), (2019, 2021), (2022, 2024))
        self.assertIn("definition changed within 2019 to 2021", out)

    def test_spans_either_side_of_a_change_are_not_compared(self):
        self.assertEqual(pages_ranges.span_status(self.facts, self.m("work.occ.prof"), (2011, 2013), (2022, 2024)), "break")
        self.assertEqual(pages_ranges.span_status(self.facts, self.m("work.occ.prof"), (2011, 2013), (2016, 2018)), "ok")

    def test_change_between_averages(self):
        out = pages_ranges.key_sentence(self.facts, self.num, "work", (2009, 2011), (2017, 2019))
        self.assertIn("+8.0 percentage points", out)
        self.assertIn('data-from="avg.work.rate.2009-2011"', out)

    def test_spans_never_overlap(self):
        for a, b in pages_ranges.span_pairs():
            self.assertGreater(b[0], a[1])


class DefaultComparison(unittest.TestCase):
    """The default pair fills every topic and is picked by a rule that ignores which way figures moved."""

    def setUp(self):
        self.saved = list(pages_life.MEAS)
        f = Facts()
        for y in range(2008, 2026):
            for k in ("w", "e", "s"):
                f.add(Fact(f"{k}.{y}", 50.0, "%", str(y), "s", "A1"))
            if y <= 2024:
                f.add(Fact(f"h.{y}", 20.0, "%", str(y), "s", "A1"))
            if y >= 2009:
                f.add(Fact(f"v.{y}", 70.0, "n", str(y), "s", "A1"))
        self.facts = f
        pages_life.MEAS[:] = [
            ("work.rate", "work", "W", lambda y: f"w.{y}", "pct", "pp", str, None),
            ("earn.ft", "earnings", "E", lambda y: f"e.{y}", "pct", "pp", str, None),
            ("house.private", "housing", "H", lambda y: f"h.{y}", "pct", "pp", str, None),
            ("hol.per100", "holidays", "V", lambda y: f"v.{y}", "int", "pct", str, pages_life.hol_basis),
            ("school.primary", "schools", "S", lambda y: f"s.{y}", "dp1", "abs", str, None),
        ]
        pages_ranges.add_range_facts(f)

    def tearDown(self):
        pages_life.MEAS[:] = self.saved

    def test_default_years_fill_all_five_topics(self):
        a, b = pages_ranges.default_years(self.facts)
        self.assertEqual((a, b), (2009, 2023))
        for x, y in pages_ranges.suggested_years(self.facts):
            self.assertTrue(pages_ranges.full_pair(self.facts, x, y))

    def test_default_spans_fill_all_five_topics_and_avoid_the_pandemic(self):
        a, b = pages_ranges.default_spans(self.facts)
        self.assertTrue(pages_ranges.full_pair(self.facts, a, b))
        for sp in (a, b):
            self.assertFalse(any(y in (2020, 2021) for y in range(sp[0], sp[1] + 1)))


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



class Holidays(unittest.TestCase):
    def test_only_single_countries_are_ranked(self):
        from builder.data import _country_rows
        rows = [["Spain", 5], ["Rest of Europe", 9], ["Total World", 99], ["- of which EU", 50], ["Other Asia", 3], ["USA", 4], ["Fly/cruise (stay onboard)", 1]]
        self.assertEqual([n for n, _ in _country_rows(rows, 0, 0, [1])], ["Spain", "United States"])

    def test_survey_change_blocks_comparison(self):
        self.assertNotEqual(pages_life.gb_survey(2019), pages_life.gb_survey(2022))
        self.assertEqual(pages_life.gb_survey(2022), pages_life.gb_survey(2025))


class WhoPaysAndTaxMix(unittest.TestCase):
    """Scorecard gap 6: tax mix over time and household-type splits."""

    @classmethod
    def setUpClass(cls):
        import warnings
        from builder.data import build_all
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cls.facts, cls.d = build_all()

    def test_points_format_is_signed(self):
        self.assertEqual(fmt(2.04, "pts"), "+2.0 points")
        self.assertEqual(fmt(-4.3, "pts"), "-4.3 points")

    def test_tax_shares_add_up_to_all_taxes(self):
        from builder.pages_money_extra import tax_mix_section
        num = Num(self.facts)
        tax_mix_section(self.facts, self.d, num, {"obr": {"publisher": "OBR", "title": "t", "page": "", "id": "obr"}})
        rc = self.d["receipts"]
        keys = [k for k, _ in rc["groups"]] + ["othertax"]
        outturn = [y for y in rc["years"] if y < rc["forecast_from"]]
        for y in (outturn[0], outturn[-1]):
            total = sum(self.facts[f"rec.share.{k}.{y}"].value for k in keys)
            self.assertAlmostEqual(total, 100, places=6, msg=y)
        self.assertFalse(any(f.startswith("rec.share.") and f.endswith(rc["forecast_from"]) for f in self.facts))

    def test_household_types_and_benefits_series(self):
        w = self.d["who_types"]
        self.assertEqual(len(w["types"]), 11)
        for k, _, _ in w["types"]:
            self.assertIsNotNone(self.facts[f"etb.t12.{k}.alltax"].value)
        ys = w["t16_years"]
        self.assertEqual(ys[0], "1977")
        self.assertIn("1994/95", ys)
        self.assertEqual(len(ys), len(set(ys)))
        self.assertTrue(all(0 < self.facts[f"etb.t16.ret.{y}"].value <= 100 for y in ys))


class IncomeTaxByAge(unittest.TestCase):
    """Review gap 4: HMRC Income Tax by age (Survey of Personal Incomes Table 3.2)."""

    @classmethod
    def setUpClass(cls):
        import warnings
        from builder.data import build_all
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cls.facts, cls.d = build_all()

    def test_age_ranges_add_up_to_hmrc_totals(self):
        f = self.facts
        ages = [k for k, _ in self.d["who_age"]["ages"]]
        n = sum(f[f"spi.age.n.{a}.all"].value for a in ages)
        self.assertLess(abs(n - f["spi.age.n.all.all"].value) / f["spi.age.n.all.all"].value, 0.005)
        published = f["spi.age.n.all.all"].value * f["spi.age.meantax.all.all"].value / 1e6
        self.assertLess(abs(f["spi.age.tottax.sum.all"].value - published) / published, 0.005)
        for m in ("n", "tax", "inc"):
            self.assertAlmostEqual(sum(f[f"spi.age.share{m}.{a}"].value for a in ages), 100, places=6)

    def test_men_and_women_add_up(self):
        f = self.facts
        for a, _ in self.d["who_age"]["ages"]:
            both = f[f"spi.age.n.{a}.men"].value + f[f"spi.age.n.{a}.women"].value
            self.assertLess(abs(both - f[f"spi.age.n.{a}.all"].value), 15, a)  # thousands, rounded

    def test_page_wording_matches_the_data(self):
        f = self.facts
        ages = [k for k, _ in self.d["who_age"]["ages"]]
        top_tax = max(ages, key=lambda a: f[f"spi.age.meantax.{a}.all"].value)
        top_inc = sorted(ages, key=lambda a: f[f"spi.age.meaninc.{a}.all"].value)[-2:]
        self.assertIn(top_tax, top_inc)  # "groups that owed the most tax per taxpayer also had the highest incomes"
        self.assertLess(f[f"spi.age.medtax.{top_tax}.all"].value, f[f"spi.age.meantax.{top_tax}.all"].value)


class Glossary(unittest.TestCase):
    def wrap(self, main):
        return f'<html><body><nav>VAT</nav><main id="main" class="wrap">{main}</main><footer><p>VAT</p></footer></body></html>'

    def test_first_use_in_text_is_linked_once(self):
        from builder.glossary import link_terms
        out = link_terms(self.wrap("<p>VAT is a tax. VAT again.</p>"), "taxes.html")
        self.assertEqual(out.count('href="glossary.html#vat"'), 1)
        self.assertIn('<a class="term" href="glossary.html#vat">VAT</a> is a tax. VAT again.', out)

    def test_headings_links_figures_and_tables_are_left_alone(self):
        from builder.glossary import link_terms
        main = ('<h2 id="x">VAT</h2><p><a href="a.html">VAT</a> <data value="1" data-fact="f" data-kind="int">GDP</data></p>'
                "<table><caption>VAT</caption><tr><td>VAT</td></tr></table><p><strong>VAT</strong></p>")
        out = link_terms(self.wrap(main), "taxes.html")
        self.assertNotIn('class="term"', out)

    def test_links_work_from_subfolders_and_skip_the_glossary(self):
        from builder.glossary import link_terms
        self.assertIn('href="../../glossary.html#median"', link_terms(self.wrap("<p>The median rose.</p>"), "life/compare/2010-2025.html"))
        self.assertNotIn('class="term"', link_terms(self.wrap("<p>The median rose.</p>"), "glossary.html"))

    def test_longer_phrase_wins_and_case_matters_for_names(self):
        from builder.glossary import link_terms
        out = link_terms(self.wrap("<p>Taxes took 30% of gross household income. The vat was full.</p>"), "x.html")
        self.assertIn('glossary.html#gross-income">gross household income</a>', out)
        self.assertNotIn("#vat", out)

    def test_text_hidden_from_screen_readers_is_left_alone(self):
        from builder.glossary import link_terms
        out = link_terms(self.wrap('<div aria-hidden="true"><p>VAT</p></div><p>VAT</p>'), "x.html")
        self.assertIn('<div aria-hidden="true"><p>VAT</p></div><p><a class="term"', out)

    def test_every_term_has_an_anchor_and_words(self):
        from builder.glossary import GROUPS
        anchors = [a for _, _, terms in GROUPS for a, _, _, _ in terms]
        self.assertEqual(len(anchors), len(set(anchors)))
        for _, _, terms in GROUPS:
            for a, name, text, words in terms:
                self.assertTrue(words and text.strip(), a)


class Folding(unittest.TestCase):
    def test_answer_stays_in_view_and_detail_folds(self):
        from builder.html import fold
        body = ('<h1>Q</h1><h2 id="a">Work</h2><p>Intro</p><div class="answer"><p>75%</p><div>x</div></div>'
                '<figure>chart</figure><table></table>')
        out = fold(body)
        lead, rest = out.split('<details class="more">')
        self.assertIn('<div class="answer"><p>75%</p><div>x</div></div>', lead)
        self.assertIn("<p>Intro</p>", lead)
        self.assertIn("More on Work", rest)
        # The section's main chart stays in view under the answer; only the table folds.
        self.assertIn("<figure>chart</figure>", lead)
        self.assertIn('class="hint">table<', rest)
        self.assertNotIn("<figure>", rest)

    def test_chart_inside_a_disclosure_stays_folded(self):
        from builder.html import fold
        body = ('<h2 id="a">Work</h2><div class="answer"><p>x</p></div>'
                '<details><summary>s</summary><figure>inner</figure></details><p class="small">Cap</p><ul class="bars"><li>b</li></ul><table></table>')
        lead, rest = fold(body).split('<details class="more">')
        self.assertIn('<p class="small">Cap</p>', lead)
        self.assertIn('<ul class="bars"><li>b</li></ul>', lead)
        self.assertIn("<figure>inner</figure>", rest)

    def test_long_comparison_list_keeps_first_rows(self):
        from builder.html import fold, KEEP_ROWS
        rows = "".join(f"<li>r{i}</li>" for i in range(KEEP_ROWS + 3))
        body = f'<h2 id="a">Work</h2><div class="answer"><p>x</p></div><ul class="cmp-list">{rows}</ul><table></table>'
        lead, rest = fold(body).split('<details class="more">')
        self.assertIn(f"<li>r{KEEP_ROWS - 1}</li>", lead)
        self.assertNotIn(f"<li>r{KEEP_ROWS}</li>", lead)
        self.assertIn(f'<ul class="cmp-list cont"><li>r{KEEP_ROWS}</li>', rest)

    def test_csv_download_beside_table_chart_and_list(self):
        from builder import downloads
        from builder.html import line_chart
        downloads.FILES.clear()
        chart = line_chart("Pay", ["2020", "2021"], [("Median", [500.0, None], "a")], "£ a week")
        body = ('<h2 id="a">Pay</h2>' + chart
                + '<div class="tablewrap" tabindex="0"><table><caption>Pay, £</caption><thead><tr><th scope="col">Year</th><th scope="col">Pay</th></tr></thead>'
                  '<tbody><tr><th scope="row">2020</th><td><data value="500.0">£500</data></td></tr></tbody></table></div>'
                + '<ul class="bars"><li><div class="lab"><span>A, B</span><span>1%</span></div></li></ul>')
        out = downloads.add_links(body, "life/pay.html")
        self.assertEqual(out.count('<p class="dl">'), 3)
        self.assertNotIn("<!--csv:", out)
        self.assertIn('href="../csv/life/pay/pay.csv" download', out)
        self.assertEqual(downloads.FILES["csv/life/pay/pay.csv"], "\ufeffPeriod,Median\r\n2020,500\r\n2021,\r\n")
        self.assertEqual(downloads.FILES["csv/life/pay/pay-2.csv"], "\ufeffYear,Pay\r\n2020,£500\r\n")
        self.assertEqual(downloads.FILES["csv/life/pay/pay-3.csv"], '\ufeffGroup,Value\r\n"A, B",1%\r\n')

    def test_folded_chart_keeps_its_download(self):
        from builder.html import fold, KEEP_ROWS
        rows = "".join(f"<li>r{i}</li>" for i in range(KEEP_ROWS + 3))
        dl = '<p class="dl"><a href="x.csv" download>Download this data (CSV)</a></p>'
        body = f'<h2 id="a">Work</h2><div class="answer"><p>x</p></div><ul class="cmp-list">{rows}</ul>{dl}<table></table>'
        lead, rest = fold(body).split('<details class="more">')
        self.assertIn(dl, lead)
        self.assertNotIn(dl, rest)

    def test_spark_leaves_gaps_and_breaks(self):
        from builder.html import spark
        pts = [(2008, None), (2009, 1.0), (2010, 2.0), (2011, 3.0), (2012, 4.0)]
        svg = spark(pts, "label", highlight=2010, group=lambda y: y >= 2011)
        self.assertIn('role="img"', svg)
        self.assertEqual(svg.count('class="gap"'), 1)   # 2008 has no figure
        self.assertEqual(svg.count('class="brk"'), 1)   # definition change between 2010 and 2011
        self.assertEqual(svg.count("<polyline"), 2)     # never joined across the break
        self.assertEqual(svg.count('class="hi"'), 1)

    def test_marker_and_unmarked_sections(self):
        from builder.html import fold, FOLD, NOFOLD
        body = (f'<h2 id="a">1. Bars</h2><ul class="bars"></ul>{FOLD}<table></table>'
                '<h2 id="b">Open</h2><p>All of it</p>'
                f'<h2 id="c">Kept</h2><div class="answer"><p>x</p></div>{NOFOLD}<table></table>')
        out = fold(body)
        self.assertEqual(out.count('<details class="more">'), 1)
        self.assertIn("More on Bars", out)
        self.assertNotIn("<!--", out)

    def test_contents_can_follow_the_first_chart(self):
        from builder.html import fold, toc, before_toc, FOLD
        body = (f'<h1>Q</h1><div class="answer"><p>a</p></div><h2 id="a">One</h2><ul class="bars"></ul>{before_toc("<p>Scale</p>")}{FOLD}<table></table>'
                '<h2 id="b">Two</h2><p>x</p><h2 id="c">Three</h2><p>y</p>')
        out = toc(fold(body), after_first=True)
        # The chart comes before the contents list, and the note sits between them, outside the fold.
        self.assertLess(out.index('class="bars"'), out.index('class="toc"'))
        self.assertLess(out.index("</details>"), out.index("<p>Scale</p>"))
        self.assertLess(out.index("<p>Scale</p>"), out.index('class="toc"'))
        self.assertLess(out.index('class="toc"'), out.index('<h2 id="b">'))
        self.assertIn('href="#a"', out)
        # Without the option the contents list stays above the first section.
        plain = toc(fold(body))
        self.assertLess(plain.index('class="toc"'), plain.index('<h2 id="a">'))


if __name__ == "__main__":
    unittest.main()


class Trace(unittest.TestCase):
    def setUp(self):
        from builder import trace
        self.trace = trace
        self.facts = Facts()
        self.facts.add(Fact("a.2020", 10.0, "£bn", "2020-21", "s1", "4_2!B23"))
        self.facts.add(Fact("b.1999 to 2000", 5.0, "%", "1999-00", "s2", "T1!C4"))
        self.facts.add(Fact("c.2020", 2.0, "ratio", "2020-21", "s1", "", status="calculated",
                            formula="a.2020 ÷ b.1999 to 2000", inputs=["a.2020", "b.1999 to 2000"]))
        src = dict(publisher="P", title="T", geography="UK", population="All", published="2025", page="https://example.org", file="data/x.xlsx", licence="OGL",
                   retrieved="2026-01-01", sha256="0" * 64)
        self.sources = {"s1": src, "s2": dict(src, title="T2"), "s3": dict(src, title="Unused")}

    def test_anchor_is_safe(self):
        self.assertEqual(self.trace.anchor("b.1999 to 2000"), "f-b.1999_to_2000")

    def test_where_reads_sheet_and_cell(self):
        self.assertEqual(self.trace.where(self.facts["a.2020"]), "Sheet “4_2”, cell B23")

    def test_record_pages_cover_inputs_and_every_source(self):
        pages = self.trace.figure_pages(self.facts, self.sources, {"c.2020"})
        self.assertEqual(set(pages), {"figures/s1.html", "figures/s2.html", "figures/s3.html"})
        s1 = pages["figures/s1.html"]
        # The calculation links to its inputs, including one on another source's page.
        self.assertIn('id="f-c.2020"', s1)
        self.assertIn('id="f-a.2020"', s1)
        self.assertIn('href="s2.html#f-b.1999_to_2000"', s1)
        self.assertIn('id="f-b.1999_to_2000"', pages["figures/s2.html"])
        self.assertIn("No figure from this source is shown directly", pages["figures/s3.html"])

    def test_page_gets_records_for_its_figures_only(self):
        html = '<body><data value="10.0" data-fact="a.2020" data-kind="bn">£10bn</data></body>'
        out = self.trace.add_trace(html, "life/2020.html", self.facts, self.sources)
        self.assertIn('data-up="../"', out)
        self.assertIn('"a.2020"', out)
        self.assertNotIn('"c.2020"', out)
        self.assertEqual(self.trace.add_trace("<body></body>", "x.html", self.facts, self.sources), "<body></body>")

    def test_corrections_link_to_their_change(self):
        out = self.trace.corrections_page()
        self.assertIn("/pull/71", out)
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
            self.assertIn(f'sources.html#src-{e["source"]}', out)
            self.assertIn(self.sources[e["source"]]["page"], out)

    def test_life_quotes_have_a_topic_and_years(self):
        for key, e in self.explain.EXPLANATIONS.items():
            if "topic" in e:
                self.assertIn(e["topic"], {t[0] for t in pages_life.TOPICS}, key)
                self.assertTrue(set(e["years"]) <= set(pages_life.YEARS), key)


class HouseholdTaxHistory(unittest.TestCase):
    """Scorecard gap 4: household tax over time, two ONS methods kept apart."""

    @classmethod
    def setUpClass(cls):
        import warnings
        from builder.data import build_all
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cls.facts, cls.d = build_all()

    def test_series_covers_1977_to_latest_with_one_overlap_year(self):
        t = self.d["tax_history"]
        self.assertEqual(t["households"][0], "1977")
        self.assertEqual(t["households"][-1], t["people"][0])
        self.assertEqual(t["people"][-1], "2023/24")

    def test_published_2023_24_matches_table_8(self):
        self.assertEqual(self.facts["etbp.all.2023-24.all"].value, self.facts["etb.t8.gross.all.all"].value)

    def test_wording_about_fifths_matches_the_data(self):
        f, t = self.facts, self.d["tax_history"]
        from builder.data_taxhist import key
        below = [p for p in t["households"] if f[f"etbh.pall.{key(p)}.q1"].value < f[f"etbh.pall.{key(p)}.q5"].value]
        self.assertEqual(below, [str(y) for y in range(1977, 1988)])
        for p in t["people"][1:]:
            self.assertLess(abs(f[f"etbp.all.{key(p)}.q1"].value - f[f"etbp.all.{key(p)}.q5"].value), 5, p)

    def test_methods_are_not_joined_on_the_page(self):
        from builder.pages_money_extra import tax_history_section
        src = {"publisher": "ONS", "title": "t", "page": "", "id": "x"}
        ids = ["etb-hist-quintile-all", "etb-hist-quintile-all-2", "etb-fye2018", "etb-fye2019", "etb-fye2020",
               "etb-fye2021", "etb-fye2022", "etb-fye2023", "etb"]
        html = tax_history_section(self.facts, self.d, Num(self.facts), {i: dict(src, id=i) for i in ids})
        self.assertIn("The line breaks at 2018/19", html)
        self.assertIn("People, no top-income adjustment", html)


class BeforeTwoThousandEight(unittest.TestCase):
    """Gap 5: series that reach back before 2008, with their breaks."""

    @classmethod
    def setUpClass(cls):
        import warnings
        from builder.data import build_all
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cls.facts, cls.d = build_all()
        pages_life.init(cls.d)

    def test_series_start_where_the_sources_do(self):
        from builder import pages_history as H
        f = self.facts
        self.assertEqual(f["work.rate.1971"].value, 72.0)  # LF24 row '1971 Q2'
        self.assertNotIn("work.ptshare.1991", f)  # part-time figures start in 1992
        self.assertIn("work.ptshare.1992", f)
        self.assertNotIn("house.lfs.private.1982", f)  # no tenure figure between 1981 and 1984: nothing filled in
        self.assertIn("house.lfs.private.1984", f)
        self.assertNotIn("hol.ips.all.2024", f)  # the long travel series stops before the 2024 method change
        self.assertIn("earn.real.ft.2002", f)
        self.assertNotIn("earn.real.ft.2001", f)
        self.assertIn("school.primary.2006", f)
        for topic, first in H.FIRST_YEAR.items():
            self.assertTrue(any(H._has(f, m[3](first)) for m in H.LONG if m[1] == topic), topic)

    def test_tenure_surveys_are_not_compared(self):
        from builder import pages_history as H
        m = next(m for m in H.LONG if m[0] == "house.lfs.private")
        self.assertEqual(H.latest_comparable(self.facts, m, 1995), 2008)  # the last Labour Force Survey year, not the English Housing Survey

    def test_pay_is_compared_only_within_one_survey_method(self):
        from builder import pages_history as H
        m = next(m for m in H.LONG if m[0] == "earn.ft")
        self.assertEqual(H.latest_comparable(self.facts, m, 2002), 2003)
        self.assertEqual(H.latest_comparable(self.facts, m, 2004), 2005)
        self.assertEqual(H.latest_comparable(self.facts, m, 2007), pages_life.LAST)

    def test_early_year_page_shows_gaps_and_links_to_comparisons(self):
        from builder import pages_history as H
        from builder.html import Num
        num = Num(self.facts)
        html = H.early_year_page(self.facts, self.d, num, {}, 1975)
        self.assertIn("Not available: the earnings figures used here start in 2002", html)
        self.assertIn('data-fact="work.rate.1975"', html)
        self.assertIn(f'href="compare/1975-{pages_life.LAST}.html"', html)
        self.assertIn('<option value="1975" selected>', html)


class EarlyComparisons(unittest.TestCase):
    """Gap 6: two years before 2008 can be compared, using only figures measured the same way."""

    @classmethod
    def setUpClass(cls):
        import warnings
        from builder.data import build_all
        from builder.html import Num
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cls.facts, cls.d = build_all()
        pages_life.init(cls.d)
        cls.num = Num(cls.facts)

    def page(self, a, b):
        from builder import pages_early_compare as E
        return E.compare_page(self.facts, self.d, self.num, {}, a, b)

    def test_every_pair_with_an_earlier_year(self):
        from builder import pages_early_compare as E
        from builder.data import EARLY_YEARS, YEARS
        n, m = len(EARLY_YEARS), len(YEARS)
        self.assertEqual(len(E.pairs()), n * (n - 1) // 2 + n * m)
        self.assertIn((1971, 1972), E.pairs())
        self.assertNotIn((2008, 2009), E.pairs())  # those use the full comparison pages

    def test_changes_only_between_years_measured_the_same_way(self):
        html = self.page(2002, 2025)
        self.assertIn('data-from="work.rate.2002" data-to="work.rate.2025"', html)
        self.assertNotIn('data-from="earn.real.ft.2002"', html)  # pay survey methods changed in 2004 and 2006
        self.assertIn("not comparable: definition changed (before 2004 method → 2006 method onwards)", html)
        self.assertIn('<a href="2006-2025.html">2006 and 2025</a>', html)  # nearest pair for pay

    def test_tenure_surveys_are_not_joined(self):
        html = self.page(1995, 2010)
        self.assertNotIn('data-from="house.lfs.private.1995" data-to="house.private.2010"', html)
        self.assertIn("the Labour Force Survey tenure figures end in 2008", html)
        self.assertIn('data-from="house.lfs.private.1995" data-to="house.lfs.private.2008"', self.page(1995, 2008))

    def test_missing_years_are_explained_not_filled(self):
        html = self.page(1985, 2025)
        self.assertIn("No figure for 1985: before 1992 tenure was measured only in 1981, 1984, 1988 and 1991", html)
        self.assertIn("No figure for 2025: this series of visits abroad stops at 2023", html)
        self.assertIn("Not available: no earnings figure for 1985, because these figures start in 2002", html)
        self.assertIn('<a href="1985-2023.html">1985 and 2023</a>', html)

    def test_compare_form_offers_every_year(self):
        form = pages_life.compare_form("")
        self.assertIn('<option value="1971">', form)
        self.assertIn(f'<option value="{pages_life.LAST}"', form)


class MoneyViews(unittest.TestCase):
    """Cash, after inflation and share of GDP: the switch and the figures behind it."""

    @classmethod
    def setUpClass(cls):
        import warnings
        from builder.data import build_all
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cls.facts, cls.d = build_all()

    def test_switch_works_without_javascript(self):
        from builder.html import switch
        out = switch("Show amounts as", [("Cash", "n1", "<p>a</p>"), ("After inflation", "n2", "<p>b</p>"), ("Share of GDP", "n3", "<p>c</p>")], default=1)
        self.assertNotIn("<script", out)
        self.assertEqual(out.count('type="radio"'), 3)
        self.assertEqual(out.count(" checked"), 1)
        self.assertIn('class="v1" checked', out)
        # Every view is in the page, each under its own heading, for browsers that cannot switch.
        for label in ("Cash", "After inflation", "Share of GDP"):
            self.assertIn(f'<p class="vhead">{label}</p>', out)

    def test_real_terms_use_the_obr_deflator(self):
        f = self.facts
        self.assertEqual(f["agg.deflator.2025-26"].value, 100)
        y = "2010-11"
        self.assertAlmostEqual(f[f"rec.real.vat.{y}"].value, f[f"rec.vat.{y}"].value * 100 / f[f"agg.deflator.{y}"].value)
        self.assertAlmostEqual(f[f"agg.real.receipts.{y}"].value, f[f"agg.receipts.{y}"].value * 100 / f[f"agg.deflator.{y}"].value)

    def test_tax_shares_of_gdp_match_the_obr_for_all_receipts(self):
        # Our share of GDP for single taxes divides by the same GDP the OBR uses for its receipts share.
        f = self.facts
        for y in ("2008-09", "2025-26"):
            self.assertAlmostEqual(100 * f[f"agg.receipts.{y}"].value / f[f"agg.gdpcash.{y}"].value, f[f"gdp.receipts.{y}"].value, places=6)

    def test_no_real_terms_before_the_deflator_starts(self):
        f = self.facts
        self.assertIsNone(f["agg.deflator.1950-51"].value)
        self.assertNotIn("agg.real.tme.1950-51", f)
        self.assertNotIn("hist.real.health.1950-51", f)

    def test_long_history_stops_before_estimated_year(self):
        h = self.d["spend_history"]
        self.assertEqual(h["years"][-1], "2021-22")  # 2022-23 is grown by the OBR, not measured
        self.assertNotIn("hist.gdp.health.2022-23", self.facts)

    def test_long_history_gaps_stay_missing(self):
        f = self.facts
        self.assertIsNone(f["hist.gdp.health.1942-43"].value)  # no figures during the Second World War
        self.assertIsNone(f["hist.gdp.social.1950-51"].value)  # social security starts in 1955-56
        self.assertIsNotNone(f["hist.gdp.defence.1942-43"].value)
