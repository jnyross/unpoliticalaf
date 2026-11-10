"""Checks of John's questions in docs/johns-questions/. Run with: make test"""

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "johns_questions", ROOT / "scripts" / "johns_questions.py"
)
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

    def test_blank_evidence_cannot_mark_a_probe_answered(self):
        data = copy.deepcopy(self.data)
        data["questions"][0]["probes"][0]["evidence"] = [{"page": "", "text": ""}]
        self.assertTrue(any("evidence" in x for x in jq.validate(data)))

    def test_baseline_intent_and_all_94_ids_are_preserved(self):
        baseline = json.loads((jq.QUESTIONS.parent / "baseline.json").read_text())
        original = {q["id"]: q for q in baseline["questions"]}
        current = {q["id"]: q for q in self.data["questions"]}
        self.assertEqual(set(original), set(current))
        self.assertEqual(len(list(jq.probes(baseline))), 94)
        self.assertEqual(sum(p["was_open"] for _, p in jq.probes(baseline)), 10)
        for qid, question in original.items():
            self.assertEqual(current[qid]["asked"], question["asked"], qid)
            self.assertEqual(current[qid].get("also_asked", []), question["also_asked"], qid)
            self.assertEqual(
                {p["id"] for p in current[qid]["probes"]},
                {p["id"] for p in question["probes"]},
                qid,
            )
            current_probes = {p["id"]: p for p in current[qid]["probes"]}
            for previous in question["probes"]:
                probe = current_probes[previous["id"]]
                if probe["question"] != previous["question"]:
                    self.assertTrue(
                        any(
                            entry.get("question") == previous["question"] and entry.get("reason")
                            for entry in probe.get("history", [])
                        ),
                        probe["id"],
                    )

    def test_welfare_denominator_does_not_claim_dwp_only(self):
        for _, probe in jq.probes(self.data):
            if probe["id"] in {"J10.6", "J10.7"}:
                self.assertIn("including tax credits and Child Benefit", probe["question"])
        page_source = (ROOT / "builder/pages_welfare.py").read_text()
        self.assertNotIn("of DWP benefit spending", page_source)
        self.assertIn("including tax credits and Child Benefit", page_source)

    def test_welfare_fact_units_name_the_combined_denominator(self):
        from builder.data import Facts
        from builder.data_welfare_dwp import build

        facts = Facts()
        build(facts)
        shares = [
            fact
            for fid, fact in facts.items()
            if fid.startswith("dwp.share.") and fact.period == "2021-22"
        ]
        self.assertEqual(len(shares), 9)
        for fact in shares:
            self.assertIn("Non-DWP Welfare", fact.unit)
            self.assertNotIn("DWP benefit spending", fact.unit)

    def test_complete_inventory_has_no_open_probes(self):
        self.assertEqual(jq.gaps(self.data), [])
        self.assertEqual(len(jq.pack(self.data)["questions"]), 94)
        self.assertEqual(jq.pack(self.data)["open"], [])

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
