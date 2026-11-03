"""Facts readers look for sit in the answer box at the top of their page (audit 11 gap 6). Run with: make test"""
import re
import unittest
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
# page -> words its answer box must contain, and the section it links to
KEY_FACTS = {
    "life/schools.html": (["law limits infant classes", "30 pupils"], "#schools-large"),
    "life/work.html": (["Manufacturing went from", "of all jobs"], "#work-industry"),
    "life/holidays.html": (["most visited countries for holidays", "Spain"], "#holidays-countries"),
}


class KeyFacts(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
