"""Checks of the phone user-test pack in docs/user-test/. Run with: make test"""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("user_test", ROOT / "scripts" / "user_test.py")
assert spec is not None and spec.loader is not None
ut = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ut)


class Pack(unittest.TestCase):
    def setUp(self):
        self.pack = ut.load()
        self.qs = self.pack["questions"]

    def test_shape_matches_the_goal(self):
        self.assertEqual(len(self.qs), 12)
        self.assertEqual(self.pack["time_limit_seconds"], 8 * 60)
        self.assertEqual(self.pack["pass_rules"], {"participants": 5, "min_correct_each": 9, "min_correct_total": 48})
        crit = sorted(q["critical_area"] for q in self.qs if q["critical"])
        self.assertEqual(crit, ["Causation", "Illustrative households", "Tax interpretation"])

    def test_every_question_is_answerable(self):
        for q in self.qs:
            self.assertEqual(sorted(q["options"]), ["A", "B", "C", "D"], q["id"])
            self.assertIn(q["answer"], q["options"], q["id"])
            self.assertTrue(q["evidence"], q["id"])

    def test_generated_sheets_are_up_to_date(self):
        for name, text in ut.rendered().items():
            self.assertEqual((ut.PACK / name).read_text(encoding="utf-8"), text,
                             f"{name} is stale: run python scripts/user_test.py render")

    def test_answers_are_on_the_built_site(self):
        if not (ut.SITE / "index.html").exists():
            self.fail("site/ is not built: run make build first")
        self.assertEqual(ut.check(), [])


class Scoring(unittest.TestCase):
    def setUp(self):
        self.pack = ut.load()
        self.key = {f"q{q['id']}": q["answer"] for q in self.pack["questions"]}

    def row(self, name, wrong=(), secs="400", commit="abc1234"):
        r = {"participant": name, "consent": "yes", "eligible": "yes", "site_commit": commit,
             "phone": "x", "seconds_taken": secs}
        r.update(self.key)
        for q in wrong:
            r[f"q{q}"] = "E"
        return r

    def test_all_pass(self):
        rows = [self.row(f"P{i}", wrong=(1, 2)) for i in range(1, 6)]  # 10 each, 50 total
        ok, lines = ut.score(rows, self.pack)
        self.assertTrue(ok, lines)

    def test_missed_critical_fails_even_with_high_score(self):
        rows = [self.row(f"P{i}") for i in range(1, 5)] + [self.row("P5", wrong=(7,))]
        ok, lines = ut.score(rows, self.pack)
        self.assertFalse(ok)
        self.assertIn("missed critical Q7", "\n".join(lines))

    def test_total_below_48_fails(self):
        rows = [self.row(f"P{i}", wrong=(1, 2, 3)) for i in range(1, 6)]  # 9 each, 45 total
        ok, _ = ut.score(rows, self.pack)
        self.assertFalse(ok)

    def test_over_time_fails(self):
        rows = [self.row(f"P{i}") for i in range(1, 5)] + [self.row("P5", secs="481")]
        self.assertFalse(ut.score(rows, self.pack)[0])

    def test_mixed_versions_fail(self):
        rows = [self.row(f"P{i}") for i in range(1, 5)] + [self.row("P5", commit="def5678")]
        self.assertFalse(ut.score(rows, self.pack)[0])

    def test_wrong_number_of_people_fails(self):
        self.assertFalse(ut.score([self.row(f"P{i}") for i in range(1, 5)], self.pack)[0])


if __name__ == "__main__":
    unittest.main()
