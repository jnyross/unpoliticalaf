"""Fast checks of the rules the site promises. Run with: make test"""
import re
import unittest

from builder.data import Fact, Facts
from builder.html import fmt, line_chart, small_multiples, Num
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


class SmallMultiples(unittest.TestCase):
    SERIES = [("North", [1.0, 2.0, 3.0]), ("South", [4.0, None, 6.0]), ("East", [7.0, 8.0, 9.0]), ("West", [None, None, None])]

    def test_one_labelled_panel_per_group(self):
        fig = small_multiples("t", ["1", "2", "3"], self.SERIES, "u", "dp1")
        self.assertEqual(fig.count('role="img"'), 4)
        for name, _ in self.SERIES:
            self.assertIn(f'aria-label="{name}"', fig)
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
        self.assertIn("chart and table", rest)
        self.assertIn("<figure>chart</figure>", rest.split("</summary>", 1)[1])

    def test_marker_and_unmarked_sections(self):
        from builder.html import fold, FOLD, NOFOLD
        body = (f'<h2 id="a">1. Bars</h2><ul class="bars"></ul>{FOLD}<table></table>'
                '<h2 id="b">Open</h2><p>All of it</p>'
                f'<h2 id="c">Kept</h2><div class="answer"><p>x</p></div>{NOFOLD}<table></table>')
        out = fold(body)
        self.assertEqual(out.count('<details class="more">'), 1)
        self.assertIn("More on Bars", out)
        self.assertNotIn("<!--", out)


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
        src = dict(publisher="P", title="T", geography="UK", population="All", published="2025", page="https://example.org", file="data/x.xlsx", licence="OGL")
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
            self.assertIn(f'methods.html#src-{e["source"]}', out)
            self.assertIn(self.sources[e["source"]]["page"], out)

    def test_life_quotes_have_a_topic_and_years(self):
        for key, e in self.explain.EXPLANATIONS.items():
            if "topic" in e:
                self.assertIn(e["topic"], {t[0] for t in pages_life.TOPICS}, key)
                self.assertTrue(set(e["years"]) <= set(pages_life.YEARS), key)
