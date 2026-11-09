"""Facts readers look for sit in the answer box at the top of their page (audit 11 gap 6). Run with: make test"""

import re
import unittest
from pathlib import Path

from builder.pages_life import FIRST_YEAR

SITE = Path(__file__).resolve().parent.parent / "site"
# page -> words its answer box must contain, and the section it links to
KEY_FACTS = {
    "life/schools.html": (["law limits infant classes", "30 pupils"], "#schools-large"),
    "life/work.html": (
        ["Manufacturing went from", "of all jobs", "women's rate went from"],
        "#work-industry",
    ),
    "life/holidays.html": (["most visited countries for holidays", "Spain"], "#holidays-countries"),
}


class KeyFacts(unittest.TestCase):
    def test_schools_answer_keeps_the_first_year_and_its_figures(self):
        html = (SITE / "life/schools.html").read_text(encoding="utf-8")
        match = re.search(r'<div class="answer">(.*?)</div>', html, re.S)
        self.assertIsNotNone(match)
        box = match.group(1)
        first = FIRST_YEAR["schools"]
        self.assertIn(f"In January {first} the figures were", box)
        for phase in ("primary", "secondary"):
            self.assertIn(f'data-fact="school.{phase}.{first}"', box)

    def test_key_facts_are_in_the_answer_box(self):
        for path, (words, anchor) in KEY_FACTS.items():
            f = SITE / path
            if not f.exists():
                self.fail("site/ is not built: run make build first")
            html = f.read_text(encoding="utf-8")
            box = re.search(r'<div class="answer">(.*?)</div>', html, re.S).group(1)
            text = re.sub(r"<[^>]+>", "", box)
            for w in words:
                self.assertIn(w, text, f"{path}: answer box lacks {w!r}")
            self.assertIn(f'href="{anchor}"', box, path)
            self.assertIn(f"id='{anchor[1:]}'", html.replace('"', "'"), path)

    def test_work_cause_note_sits_before_the_long_chart(self):
        """The change-is-not-cause note and women's and men's rates are on the first screen (audit 14 gap 1)."""
        f = SITE / "life/work.html"
        if not f.exists():
            self.fail("site/ is not built: run make build first")
        html = f.read_text(encoding="utf-8")
        box_end = html.index("</div>", html.index('<div class="answer">'))
        note = html.index("Change is not cause.")
        self.assertLess(box_end, note)
        self.assertLess(note, html.index("id='trend'"))
        self.assertEqual(html.count("Change is not cause."), 1, "the work page shows the note once")


class AprilPay2026Site(unittest.TestCase):
    """The built pages and downloads share one price base and show April 2026 pay."""

    def read(self, path):
        f = SITE / path
        if not f.exists():
            self.fail("site/ is not built: run make build first")
        return f.read_text(encoding="utf-8")

    def test_pay_pages_name_april_2026_prices_only(self):
        for path in ("index.html", "methods.html", "life/earnings.html", "life/index.html"):
            html = self.read(path)
            self.assertNotIn("April 2025 prices", html, path)
            self.assertNotIn("2025 prices)", html, path)
        home = self.read("index.html")
        self.assertIn("After inflation, pay in April 2026 was", home)
        self.assertNotIn("does not yet include", home)
        self.assertIn("April 2026 prices", self.read("life/earnings.html"))
        for path in ("life/earnings.html", "life/index.html", "life/compare/2024-2025.html"):
            self.assertNotIn("does not yet include", self.read(path), path)
        earnings = self.read("life/earnings.html")
        for sid in ("ashe-2025-table1-revised", "ashe-2026-table1-provisional", "ashe-2026-fig2"):
            self.assertIn(f"figures/{sid}.html", earnings, sid)

    def test_download_and_facts_match_the_page(self):
        import json

        html = self.read("life/earnings.html")
        self.assertIn('data-fact="earn.ft.2026"', html)
        facts = {f["id"]: f for f in json.loads(self.read("data/facts.json"))["facts"]}
        self.assertEqual(facts["earn.ft.2026"]["value"], 811.2)
        self.assertEqual(facts["earn.ft.2026"]["status"], "provisional")
        self.assertEqual(facts["earn.ft.2025"]["status"], "revised")
        self.assertEqual(facts["earn.real.ft.2025"]["unit"], "£ a week, April 2026 prices")
        downloads = [
            self.read(href.replace("../", ""))
            for href in re.findall(r'href="([^"]+\.csv)"', html)
            if (SITE / href.replace("../", "")).exists()
        ]
        table = [d for d in downloads if "Full-time (2026 prices)" in d]
        self.assertTrue(table, "the yearly earnings table has a CSV download")
        rows = [r for r in table[0].splitlines() if r.startswith("2026,")]
        self.assertEqual(len(rows), 1)
        self.assertIn("811", rows[0])


if __name__ == "__main__":
    unittest.main()
