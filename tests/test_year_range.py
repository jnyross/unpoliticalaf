"""The year explorer reaches 2026 from stated bounds, with real figures and plain gaps.

The expected annual, pair and range pages come from the explorer's bounds, never
from the files a build happened to write, and the latest year only shows figures
that were published for it.
"""

import re
import tempfile
import unittest
import warnings
from itertools import combinations
from pathlib import Path
from unittest.mock import patch

from builder import check, pages_early_compare, pages_life, pages_ranges
from builder.data import EARLY_YEARS, YEARS

ANNUAL = range(1971, 2027)
SPANS = [(s, s + 2) for s in range(2008, 2025)]


def _span_slug(a, b):
    return f"{a[0]}-{a[1]}-and-{b[0]}-{b[1]}"


class Bounds(unittest.TestCase):
    def test_explorer_and_early_years_reach_2026(self):
        self.assertEqual(EARLY_YEARS, list(range(1971, 2008)))
        self.assertEqual(YEARS, list(range(2008, 2027)))
        self.assertEqual(pages_life.LAST, 2026)

    def test_checker_states_its_own_bounds(self):
        self.assertEqual(
            (check.ANNUAL_FIRST, check.EXPLORER_FIRST, check.ANNUAL_LAST), (1971, 2008, 2026)
        )

    def test_expected_population_comes_from_the_bounds(self):
        want = check.expected_life_pages()
        self.assertEqual(want["year"], {f"life/{y}.html" for y in ANNUAL})
        self.assertEqual(
            want["pair"], {f"life/compare/{a}-{b}.html" for a, b in combinations(ANNUAL, 2)}
        )
        self.assertEqual(
            want["span"],
            {
                f"life/compare/spans/{_span_slug(a, b)}.html"
                for a, b in combinations(SPANS, 2)
                if b[0] > a[1]
            },
        )
        self.assertEqual((len(want["year"]), len(want["pair"]), len(want["span"])), (56, 1540, 105))
        for path in (
            "life/2026.html",
            "life/compare/1971-2026.html",
            "life/compare/2022-2026.html",
            "life/compare/2025-2026.html",
            "life/compare/spans/2008-2010-and-2024-2026.html",
        ):
            self.assertIn(path, want["year"] | want["pair"] | want["span"])

    def test_builder_writes_exactly_the_expected_population(self):
        built = {f"life/{y}.html" for y in YEARS + EARLY_YEARS}
        built |= {f"life/compare/{a}-{b}.html" for a, b in combinations(YEARS, 2)}
        built |= {f"life/compare/{a}-{b}.html" for a, b in pages_early_compare.pairs()}
        spans = {
            f"life/compare/spans/{pages_ranges.slug(a, b)}.html"
            for a, b in pages_ranges.span_pairs()
        }
        want = check.expected_life_pages()
        self.assertEqual(built, want["year"] | want["pair"])
        self.assertEqual(spans, want["span"])
        self.assertIn(((2008, 2010), (2024, 2026)), pages_ranges.span_pairs())
        for a, b in pages_ranges.span_pairs():
            self.assertGreater(b[0], a[1])


class Structure(unittest.TestCase):
    """check_structure reports a whole missing year, which counting found files cannot."""

    def _site(self, root, drop=(), extra=()):
        want = check.expected_life_pages()
        heads = {}
        for y in ANNUAL:
            heads[f"life/{y}.html"] = f"Everyday life in {y}"
        for a, b in combinations(ANNUAL, 2):
            heads[f"life/compare/{a}-{b}.html"] = f"{a} compared with {b}"
        for a, b in combinations(SPANS, 2):
            if b[0] > a[1]:
                heads[f"life/compare/spans/{_span_slug(a, b)}.html"] = (
                    f"{a[0]} to {a[1]} compared with {b[0]} to {b[1]}"
                )
        topics = "".join(f'<h2 id="{t}">{t}</h2>' for t in check.LIFE_TOPICS)
        pages = {p: f"<h1>{h}</h1>{topics}" for p, h in heads.items()}
        pages.update({p: "<h1>Extra</h1>" for p in extra})
        for p in drop:
            pages.pop(p, None)
        for p, html in pages.items():
            f = root / p
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(html, encoding="utf-8")

        def links(paths, base):
            return "".join(f'<a href="{Path(p).relative_to(base)}">x</a>' for p in sorted(paths))

        (root / "life/index.html").write_text(links(want["year"], "life"), encoding="utf-8")
        (root / "life/compare/index.html").write_text(
            links(want["pair"], "life/compare"), encoding="utf-8"
        )
        (root / "life/compare/spans/index.html").write_text(
            links(want["span"], "life/compare/spans"), encoding="utf-8"
        )

    def _problems(self, **kw):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._site(root, **kw)
            problems = []
            with patch.object(check, "SITE", root), patch.object(check, "problems", problems):
                check.check_structure()
        return [p for p in problems if not p.startswith("missing page ")]

    def test_complete_population_passes(self):
        self.assertEqual(self._problems(), [])

    def test_a_whole_missing_latest_year_is_reported(self):
        drop = {"life/2026.html"} | {f"life/compare/{a}-2026.html" for a in range(1971, 2026)}
        drop |= {
            f"life/compare/spans/{_span_slug(a, (2024, 2026))}.html" for a in SPANS if a[1] < 2024
        }
        out = " ".join(self._problems(drop=drop))
        self.assertIn("1 missing year pages, for example life/2026.html", out)
        self.assertIn("55 missing pair pages, for example life/compare/1971-2026.html", out)
        self.assertIn(
            "14 missing span pages, for example life/compare/spans/2008-2010-and-2024-2026.html",
            out,
        )

    def test_pages_outside_the_bounds_are_reported(self):
        out = " ".join(self._problems(extra={"life/2027.html", "life/compare/2026-2027.html"}))
        self.assertIn("life/2027.html", out)
        self.assertIn("life/compare/2026-2027.html", out)

    def test_a_page_whose_heading_names_other_years_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._site(root)
            (root / "life/compare/2010-2026.html").write_text(
                "<h1>2010 compared with 2025</h1>", encoding="utf-8"
            )
            problems = []
            with patch.object(check, "SITE", root), patch.object(check, "problems", problems):
                check.check_structure()
        out = " ".join(problems)
        self.assertIn("life/compare/2010-2026.html", out)


def _text(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def _section(html, key):
    m = re.search(rf'<h2 id="{key}".*?(?=<h2 id=|\Z)', html, re.S)
    return m.group(0) if m else ""


class Latest(unittest.TestCase):
    """2026 shows what was published for it and says plainly what was not."""

    @classmethod
    def setUpClass(cls):
        from builder import uncertainty
        from builder.data import build_all
        from builder.html import Num
        from builder.sources import SOURCES

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cls.facts, cls.d = build_all()
        uncertainty.add_facts(cls.facts, cls.d)
        pages_life.init(cls.d)
        pages_ranges.add_range_facts(cls.facts)
        cls.num = Num(cls.facts)
        cls.sources = SOURCES

    def _value(self, fid):
        f = self.facts.get(fid)
        return None if f is None else f.value

    def test_no_2026_value_is_invented(self):
        for fid, f in self.facts.items():
            if fid.endswith(".2026") and f.value is not None:
                self.assertFalse(fid.startswith(("house.", "hol.")), fid)
                self.assertNotEqual(f.status, "forecast", fid)
        for fid in ("work.rate.2026", "work.women.2026", "school.primary.2026"):
            self.assertEqual(self.facts[fid].status, "published", fid)
        self.assertEqual(self.facts["earn.ft.2026"].status, "provisional")
        for fid in ("hol.world.holiday.2026", "house.owners.2026", "work.place.wales.2026"):
            self.assertIsNone(self._value(fid), fid)

    def test_ranges_ending_2026_average_only_complete_comparable_years(self):
        self.assertIn("avg.work.rate.2024-2026", self.facts)
        self.assertEqual(
            self.facts["avg.work.rate.2024-2026"].inputs,
            ["work.rate.2024", "work.rate.2025", "work.rate.2026"],
        )
        for fid in self.facts:
            if fid.startswith("avg.") and fid.endswith(".2024-2026"):
                self.assertFalse(fid.startswith(("avg.house.", "avg.hol.")), fid)

    def test_year_page_2026_shows_published_figures_and_gaps(self):
        html = pages_life.year_page(self.facts, self.d, self.num, self.sources, 2026)
        self.assertIn("<h1>Everyday life in 2026</h1>", html)
        self.assertIn('data-fact="work.rate.2026"', html)
        self.assertIn('data-fact="earn.real.ft.2026"', html)
        self.assertIn('data-fact="school.primary.2026"', html)
        for key in ("housing", "holidays"):
            sec = _text(_section(html, key))
            self.assertTrue(sec, key)
            self.assertRegex(sec, r"not (yet )?(published|available)", key)
        self.assertNotIn('href="2027.html"', html)

    def test_pair_with_2026_compares_only_what_both_years_have(self):
        html = pages_life.compare_page(self.facts, self.d, self.num, self.sources, 2010, 2026)
        self.assertIn("<h1>2010 compared with 2026</h1>", html)
        self.assertIn('data-from="work.rate.2010" data-to="work.rate.2026"', html)
        self.assertIn('data-to="school.primary.2026"', html)
        self.assertNotRegex(html, r'data-to="(house|hol)\.[^"]*\.2026"')
        self.assertIn("no figure for 2026", _text(html))

    def test_method_break_to_2026_is_not_compared(self):
        html = pages_life.compare_page(self.facts, self.d, self.num, self.sources, 2015, 2026)
        self.assertIn("how it codes jobs in 2021", _text(html))
        self.assertNotIn('data-from="earn.real.ft.2015" data-to="earn.real.ft.2026"', html)

    def test_earliest_year_against_2026(self):
        from builder import pages_early_compare as E

        html = E.compare_page(self.facts, self.d, self.num, self.sources, 1971, 2026)
        self.assertIn("<h1>1971 compared with 2026</h1>", html)
        self.assertIn('data-from="work.rate.1971" data-to="work.rate.2026"', html)
        self.assertNotRegex(html, r'data-to="(house|hol)\.[^"]*\.2026"')

    def test_range_ending_2026(self):
        html = pages_ranges.span_page(
            self.facts, self.d, self.num, self.sources, (2008, 2010), (2024, 2026)
        )
        self.assertIn("<h1>2008 to 2010 compared with 2024 to 2026</h1>", html)
        self.assertIn('data-to="avg.work.rate.2024-2026"', html)
        self.assertNotRegex(html, r'data-(to|fact)="avg\.(house|hol)\.[^"]*\.2024-2026"')
        text = _text(html)
        self.assertIn("the English Housing Survey for 2025-26 is not yet published.", text)
        self.assertNotRegex(text, r"\.\s*\.")

    def test_topic_answers_use_each_topics_latest_published_year(self):
        for key in ("work", "earnings", "housing", "holidays", "schools"):
            answer, _ = pages_life.TOPIC_BUILDERS[key](self.facts, self.d, self.num, self.sources)
            self.assertNotIn('class="missing"', answer, key)
        hub = pages_life.life_index(self.facts, self.d, self.num, self.sources)
        for m in re.finditer(r'<div class="answer">.*?</div>', hub, re.S):
            self.assertNotIn('class="missing"', m.group(0))
        answer, _ = pages_life.TOPIC_BUILDERS["holidays"](
            self.facts, self.d, self.num, self.sources
        )
        self.assertIn('data-fact="hol.world.holiday.2025"', answer)
        self.assertNotIn("In 2026", _text(answer))

    def test_neutral_default_pair_does_not_depend_on_results(self):
        before = pages_ranges.default_years(self.facts)
        saved = {
            fid: self.facts[fid].value
            for fid in self.facts
            if fid.startswith("work.rate.") and self.facts[fid].value is not None
        }
        try:
            for fid, v in saved.items():
                self.facts[fid].value = 200 - v
            self.assertEqual(pages_ranges.default_years(self.facts), before)
        finally:
            for fid, v in saved.items():
                self.facts[fid].value = v
        self.assertNotIn(2026, before)  # no full five-topic figures for 2026 yet


if __name__ == "__main__":
    unittest.main()
