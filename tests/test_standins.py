"""Checks of the rubric v3 stand-in scoring in scripts/standins.py. Run with: make test

These need no browser: they cover sealing and the pass bars. The phone and
screen-reader tools are exercised by the goal audit itself."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("standins", ROOT / "scripts" / "standins.py")
si = importlib.util.module_from_spec(spec)
spec.loader.exec_module(si)

PACK = json.loads((ROOT / "docs/user-test/questions.json").read_text())
KEY = {str(q["id"]): q["answer"] for q in PACK["questions"]}
WRONG = {k: "E" for k in KEY}


def new_pack(n=24):
    return {"title": "t", "questions": [{"id": i, "options": {"A": "a", "B": "b", "C": "c", "D": "d"},
                                         "answer": "B", "critical": False} for i in range(1, n + 1)]}


def reader(i, with_site=KEY, without=WRONG, new_right=24, actions=30):
    return {"reader": f"R{i}", "site_commit": "abc1234", "budget": 40, "actions_used": actions,
            "with_site": dict(with_site), "without_site": dict(without),
            "new_with_site": {str(q): ("B" if q <= new_right else "A") for q in range(1, 25)},
            "new_without_site": {}}


class Score(unittest.TestCase):
    def run_score(self, readers, sr=None, new=None):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "readers").mkdir()
            for r in readers:
                (Path(d) / "readers" / f"{r['reader']}.json").write_text(json.dumps(r))
            if sr:
                (Path(d) / "readers" / "SR.json").write_text(json.dumps(sr))
            return si.score(d, PACK, new or new_pack())[0]

    def test_all_right_passes(self):
        res = self.run_score([reader(i) for i in range(1, 6)],
                             sr={"reader": "SR", "budget": 40, "actions_used": 20, "with_site": KEY})
        self.assertTrue(res["phone_test"])
        self.assertTrue(res["prior_knowledge"])
        self.assertTrue(res["new_questions"])
        self.assertTrue(res["screen_reader"])
        self.assertTrue(res["d11_ready_for_5"])

    def test_a_missed_critical_question_fails_the_phone_test(self):
        miss = dict(KEY, **{"5": "A" if KEY["5"] != "A" else "B"})
        res = self.run_score([reader(1, with_site=miss)] + [reader(i) for i in range(2, 6)])
        self.assertFalse(res["phone_test"])
        self.assertFalse(res["d11_ready_for_5"])

    def test_over_the_action_budget_fails(self):
        res = self.run_score([reader(1, actions=41)] + [reader(i) for i in range(2, 6)])
        self.assertFalse(res["phone_test"])

    def test_answers_already_known_do_not_count(self):
        # Everyone already knew everything: the site added nothing.
        res = self.run_score([reader(i, without=KEY) for i in range(1, 6)])
        self.assertTrue(res["phone_test"])
        self.assertFalse(res["prior_knowledge"])

    def test_new_questions_need_80_percent(self):
        # 19 of 24 each is 79%.
        res = self.run_score([reader(i, new_right=19) for i in range(1, 6)])
        self.assertFalse(res["new_questions"])
        res = self.run_score([reader(i, new_right=20) for i in range(1, 6)])
        self.assertTrue(res["new_questions"])

    def test_no_screen_reader_file_fails_that_stand_in_only(self):
        res = self.run_score([reader(i) for i in range(1, 6)])
        self.assertFalse(res["screen_reader"])
        self.assertTrue(res["d11_ready_for_5"])


class Seal(unittest.TestCase):
    def test_seal_then_unseal(self):
        with tempfile.TemporaryDirectory() as d:
            q = Path(d) / "q.json"
            q.write_text(json.dumps(new_pack()))
            self.assertEqual(si.seal(q, Path(d) / "audit"), 0)
            self.assertEqual(si.unseal(q, Path(d) / "audit"), 0)
            q.write_text(json.dumps(new_pack(23)))
            self.assertEqual(si.unseal(q, Path(d) / "audit"), 1)

    def test_a_question_without_a_right_option_is_refused(self):
        bad = new_pack()
        bad["questions"][0]["answer"] = "F"
        self.assertTrue(si.validate_pack(bad))


class Prompts(unittest.TestCase):
    def test_every_prompt_the_procedure_names_exists(self):
        readme = (ROOT / "docs/standins/README.md").read_text()
        for name in ("question-writer", "informal-reader", "phone-reader", "profiles", "screen-reader",
                     "fact-checker", "critic", "judge"):
            self.assertIn(f"prompts/{name}.md", readme)
            self.assertTrue((ROOT / f"docs/standins/prompts/{name}.md").exists(), name)


class Johns(unittest.TestCase):
    DATA = {"not_sure": "n", "questions": [{"id": "J1", "asked": "a", "added": "d", "source": "s", "probes": [
        {"id": "J1.1", "question": "q", "options": {"A": "a", "B": "b"}, "answer": "B", "why": "w",
         "evidence": [{"page": "x.html", "text": "t"}]}]}]}

    def readers(self, right):
        return [{"reader": f"R{i}", "johns_with_site": {"J1.1": "B" if i <= right else "A"}} for i in range(1, 6)]

    def test_passes_when_four_of_five_right(self):
        res, _ = si.score_johns(self.readers(4), self.DATA)
        self.assertTrue(res["johns_questions"], res)

    def test_fails_and_writes_a_gap_when_three_of_five_right(self):
        res, _ = si.score_johns(self.readers(3), self.DATA)
        self.assertFalse(res["johns_questions"])
        self.assertIn("J1.1", res["johns_gaps"][0])

    def test_open_probe_is_a_gap(self):
        import copy
        data = copy.deepcopy(self.DATA)
        data["questions"][0]["probes"].append({"id": "J1.2", "question": "q2", "evidence": [], "gap": "missing"})
        res, _ = si.score_johns(self.readers(5), data)
        self.assertFalse(res["johns_questions"])
        self.assertEqual(res["johns_gaps"], ["J1.2: missing"])


if __name__ == "__main__":
    unittest.main()
