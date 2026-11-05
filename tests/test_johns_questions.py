"""Checks of John's questions in docs/johns-questions/. Run with: make test"""
import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("johns_questions", ROOT / "scripts" / "johns_questions.py")
assert spec is not None and spec.loader is not None
jq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jq)


class File(unittest.TestCase):
    def setUp(self):
        self.data = jq.load()

    def test_file_is_well_formed(self):
        self.assertEqual(jq.validate(self.data), [])

    def test_every_question_has_a_probe(self):
        for q in self.data["questions"]:
            self.assertTrue(q["probes"], q["id"])

    def test_answered_probes_are_on_the_built_site(self):
        if not (jq.SITE / "index.html").exists():
            self.fail("site/ is not built: run make build first")
        self.assertEqual(jq.check(), [])

    def test_open_probe_needs_a_gap(self):
        data = copy.deepcopy(self.data)
        p = data["questions"][0]["probes"][0]
        p["evidence"] = []
        p.pop("gap", None)
        self.assertTrue(any("needs a one-sentence gap" in x for x in jq.validate(data)))

    def test_answer_must_be_an_option(self):
        data = copy.deepcopy(self.data)
        answered = next(p for _, p in jq.probes(data) if not jq.is_open(p))
        answered["answer"] = "Z"
        self.assertTrue(any("is not one of the options" in x for x in jq.validate(data)))

    def test_every_question_is_in_exactly_one_topic_group(self):
        ids = [q["id"] for q in self.data["questions"]]
        grouped = [i for members in jq.TOPIC_GROUPS.values() for i in members]
        self.assertEqual(sorted(grouped), sorted(ids))
        self.assertEqual(len(grouped), len(set(grouped)))

    def test_group_sheets_hold_only_their_questions(self):
        for name, members in jq.TOPIC_GROUPS.items():
            text = jq.sheet(self.data, name)
            heads = [line.split(".")[0][3:] for line in text.splitlines() if line.startswith("## ")]
            self.assertEqual(sorted(set(heads)), sorted(members), name)

    def test_pack_holds_only_answered_probes(self):
        out = jq.pack(self.data)
        answered = {p["id"] for _, p in jq.probes(self.data) if not jq.is_open(p)}
        self.assertEqual({q["id"] for q in out["questions"]}, answered)
        self.assertEqual(len(out["open"]), len(jq.gaps(self.data)))


if __name__ == "__main__":
    unittest.main()
