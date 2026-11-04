"""Cached glossary scans must not share a page's mutable linking decisions."""
import unittest

from builder import glossary


class GlossaryCache(unittest.TestCase):
    def setUp(self):
        glossary._term_matches.cache_clear()

    def tearDown(self):
        glossary._term_matches.cache_clear()

    def test_repeated_text_reuses_the_scan(self):
        text = "The public sector and GDP."
        first = glossary._link_text(text, set(), "", 12)
        second = glossary._link_text(text, set(), "", 12)
        self.assertEqual(first, second)
        self.assertEqual(glossary._term_matches.cache_info().hits, 1)
        self.assertEqual(glossary._term_matches.cache_info().maxsize, 4096)

    def test_paths_and_done_sets_remain_page_specific(self):
        text = "The public sector and GDP."
        done = {"public-sector"}
        root = glossary._link_text(text, set(), "", 12)
        nested = glossary._link_text(text, done, "../../", 12)
        self.assertIn('href="glossary.html#public-sector"', root)
        self.assertNotIn('href="../../glossary.html#public-sector"', nested)
        self.assertIn('href="../../glossary.html#gdp"', nested)
        self.assertEqual(done, {"public-sector", "gdp"})
        self.assertEqual(glossary._term_matches.cache_info().hits, 1)

    def test_link_limit_is_not_cached(self):
        text = "The public sector and GDP."
        self.assertEqual(glossary._link_text(text, set(), "", 1).count('class="term"'), 1)
        self.assertEqual(glossary._link_text(text, set(), "", 12).count('class="term"'), 2)

    def test_overlapping_phrases_keep_longer_match_first(self):
        text = "Gross household income, household income and gross income."
        output = glossary._link_text(text, set(), "", 12)
        self.assertIn('>Gross household income</a>', output)
        self.assertEqual(output, glossary._link_text(text, set(), "", 12))

    def test_cache_evicts_old_text(self):
        for i in range(4097):
            glossary._term_matches(f"Text without glossary words {i}")
        info = glossary._term_matches.cache_info()
        self.assertEqual(info.currsize, 4096)
        glossary._term_matches("Text without glossary words 0")
        self.assertEqual(glossary._term_matches.cache_info().misses, info.misses + 1)


if __name__ == "__main__":
    unittest.main()
