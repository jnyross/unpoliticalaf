"""Fail-closed autonomous evidence, using synthetic fixtures, not real readers."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("standins", ROOT / "scripts/standins.py")
si = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(si)
jq = __import__("johns_questions")

PACK = json.loads(si.PACK.read_text())
KEY = {str(q["id"]): q["answer"] for q in PACK["questions"]}
NEW = {"questions": [{"id": i, "options": {"A": "yes", "B": "no"},
                      "answer": "A"} for i in range(1, 25)]}
DATA = {"not_sure": "unknown", "questions": [
    {"id": ids[0], "asked": "fixture", "probes": [{"id": ids[0] + ".1", "question": "fixture",
      "options": {"A": "yes", "B": "no"}, "answer": "A",
      "why": "fixture", "evidence": [{"page": "fixture.html", "text": "fixture"}]}]}
    for ids in jq.TOPIC_GROUPS.values()]}


def write_fixture(audit):
    readers = audit / "readers"
    readers.mkdir()
    (audit / "new-questions.json").write_text(json.dumps(NEW))
    si.seal(audit / "new-questions.json", audit)
    for who in [f"R{i}" for i in range(1, 6)] + ["SR"]:
        row = {"reader": who, "site_commit": "abc1234", "budget": 40,
               "actions_used": 40, "with_site": KEY}
        sessions = {"state" if who == "SR" else "phone": 40}
        if who != "SR":
            row.update(without_site={k: "E" for k in KEY},
                       new_with_site={str(i): "A" for i in range(1, 25)},
                       new_without_site={str(i): "E" for i in range(1, 25)},
                       new_actions_used=40,
                       johns_with_site={q["probes"][0]["id"]: "A" for q in DATA["questions"]},
                       johns_without_site={q["probes"][0]["id"]: "E" for q in DATA["questions"]},
                       johns_actions_used={g: 40 for g in jq.TOPIC_GROUPS})
            sessions.update(new=40, **{f"johns-{g}": 40 for g in jq.TOPIC_GROUPS})
        (readers / f"{who}.json").write_text(json.dumps(row))
        for suffix, actions in sessions.items():
            name = f"{who}-{suffix}"
            state = {"reader": name, "site_commit": "abc1234",
                     "build_digest": "a" * 64, "mode": "sr" if who == "SR" else "phone",
                     "budget": 40, "actions": actions, "log": ["scroll down"] * actions}
            (readers / f"{name}.json").write_text(json.dumps(state))


class Evidence(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.audit = Path(self.temp.name)
        write_fixture(self.audit)

    def score(self):
        with patch.object(jq, "load", return_value=DATA):
            return si.score(self.audit)

    def change(self, name, **fields):
        path = self.audit / "readers" / name
        data = json.loads(path.read_text())
        data.update(fields)
        path.write_text(json.dumps(data))

    def test_complete_boundary_sessions_pass_without_human_adapter(self):
        with patch("user_test.score", side_effect=AssertionError("human adapter used")):
            res, lines = self.score()
        self.assertTrue(res["all_reader_standins"], lines)
        self.assertIn("met (simulated)", lines[-1])
        self.assertNotIn("seconds", "\n".join(lines))

    def test_invalid_sessions_fail(self):
        cases = [
            ("R1-phone.json", {"actions": 41, "budget": 99}, "phone_test"),
            ("R1-phone.json", {"actions": -1}, "phone_test"),
            ("R1-phone.json", {"actions": True}, "phone_test"),
            ("R1-phone.json", {"log": []}, "phone_test"),
            ("R1-phone.json", {"site_commit": "different"}, "phone_test"),
            ("R1-new.json", {"actions": 41}, "new_questions"),
            ("R1-new.json", {"build_digest": "b" * 64}, "new_questions"),
            ("SR-state.json", {"mode": "phone"}, "screen_reader"),
        ]
        for name, fields, section in cases:
            with self.subTest(name=name, fields=fields):
                path = self.audit / "readers" / name
                old = path.read_text()
                self.change(name, **fields)
                self.assertFalse(self.score()[0][section])
                path.write_text(old)

    def test_each_group_has_its_own_budget_and_required_state(self):
        for group in jq.TOPIC_GROUPS:
            path = self.audit / "readers" / f"R1-johns-{group}.json"
            old = path.read_text()
            self.change(path.name, actions=41)
            self.assertFalse(self.score()[0]["johns_questions"])
            path.unlink()
            self.assertFalse(self.score()[0]["all_reader_standins"])
            path.write_text(old)
        self.assertTrue(self.score()[0]["johns_questions"])

    def test_missing_or_duplicate_reader_fails(self):
        old = (self.audit / "readers" / "R5.json").read_text()
        (self.audit / "readers" / "R5.json").unlink()
        res, _ = self.score()
        for key in ("phone_test", "new_questions", "prior_knowledge", "johns_questions"):
            self.assertFalse(res[key], key)
        (self.audit / "readers" / "R5.json").write_text(old)
        self.change("R4.json", reader="R3")
        self.assertFalse(self.score()[0]["phone_test"])

    def test_counts_must_match_and_all_group_keys_are_required(self):
        self.change("R1.json", actions_used=39)
        self.assertFalse(self.score()[0]["phone_test"])
        self.change("R1.json", actions_used=40, new_actions_used=39)
        self.assertFalse(self.score()[0]["new_questions"])
        self.change("R1.json", new_actions_used=40, johns_actions_used={})
        self.assertFalse(self.score()[0]["johns_questions"])
        counts = {g: 40 for g in jq.TOPIC_GROUPS}
        counts["extra"] = 0
        self.change("R1.json", johns_actions_used=counts)
        self.assertFalse(self.score()[0]["johns_questions"])

    def test_screen_reader_score_critical_blockers_and_candidate(self):
        self.change("SR.json", blockers=["unresolved access barrier"])
        self.assertFalse(self.score()[0]["screen_reader"])
        self.change("SR.json", blockers=[], site_commit="other")
        self.assertFalse(self.score()[0]["screen_reader"])
        missed = dict(KEY)
        critical = next(str(q["id"]) for q in PACK["questions"] if q["critical"])
        missed[critical] = "E"
        self.change("SR.json", site_commit="abc1234", with_site=missed)
        self.assertFalse(self.score()[0]["screen_reader"])
        missed = dict(KEY)
        for key in list(missed)[:4]:
            missed[key] = "E"
        self.change("SR.json", with_site=missed)
        self.assertFalse(self.score()[0]["screen_reader"])

    def test_missing_malformed_or_cross_reader_state_fails(self):
        path = self.audit / "readers" / "R2-phone.json"
        old = path.read_text()
        for content in ("{}", "not json"):
            path.write_text(content)
            self.assertFalse(self.score()[0]["phone_test"])
        path.write_text(old)
        self.change(path.name, build_digest="b" * 64)
        self.assertFalse(self.score()[0]["phone_test"])

    def test_tool_refuses_overwrite_and_candidate_or_mode_changes(self):
        site = self.audit / "site"
        site.mkdir()
        (site / "build.json").write_text(json.dumps({"commit": "abc1234"}))
        state = self.audit / "readers" / "R1-phone.json"
        with patch.object(si, "SITE", site), patch.object(si, "browser") as browser:
            self.assertEqual(si.session("phone", ["start", "--state", str(state)]), 1)
            self.assertEqual(si.session("phone", ["tap", "--state", str(state), "1"]), 1)
            self.assertEqual(si.session("sr", ["tap", "--state", str(state), "1"]), 1)
            browser.assert_not_called()

    def test_incomplete_prior_or_new_results_fail(self):
        for field in ("without_site", "new_without_site", "new_with_site", "johns_without_site"):
            path = self.audit / "readers" / "R1.json"
            old = path.read_text()
            self.change(path.name, **{field: {}})
            self.assertFalse(self.score()[0]["all_reader_standins"], field)
            path.write_text(old)

    def test_missing_bad_or_changed_seal_fails_even_with_injected_pack(self):
        seal = self.audit / "new-questions.sha256"
        for content in ("", "0" * 64 + "  new-questions.json\n"):
            seal.write_text(content)
            with patch.object(jq, "load", return_value=DATA):
                self.assertFalse(si.score(self.audit, new_pack=NEW)[0]["new_questions"])
        seal.unlink()
        self.assertFalse(self.score()[0]["new_questions"])

    def test_open_or_failed_probe_controls_final_verdict_and_exit(self):
        bad = copy.deepcopy(DATA)
        bad["questions"][0]["probes"][0]["evidence"] = []
        bad["questions"][0]["probes"][0]["gap"] = "not supported"
        with patch.object(jq, "load", return_value=bad):
            res, lines = si.score(self.audit)
            self.assertTrue(res["d11_ready_for_5"])
            self.assertFalse(res["all_reader_standins"])
            self.assertIn("NOT MET", lines[-1])
            self.assertEqual(si.main(["standins", "score", str(self.audit)]), 1)
        for i in (1, 2):
            answers = {q["probes"][0]["id"]: "A" for q in DATA["questions"]}
            answers[DATA["questions"][0]["probes"][0]["id"]] = "B"
            self.change(f"R{i}.json", johns_with_site=answers)
        self.assertFalse(self.score()[0]["johns_questions"])

    def test_question_count_and_unique_ids_are_enforced(self):
        for questions in (NEW["questions"][:-1], [NEW["questions"][0]] * 24):
            self.assertTrue(si.validate_pack({"questions": questions}))


if __name__ == "__main__":
    unittest.main()
