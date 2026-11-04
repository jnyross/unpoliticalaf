"""Exercise the real stability CLI with deterministic stable/unstable fixtures."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest

from scripts.test_stability import summarize


ROOT = Path(__file__).resolve().parent.parent


class StabilityCLI(unittest.TestCase):
    def probe(self, source, *options, preexisting_report=None):
        with tempfile.TemporaryDirectory() as folder:
            suite = Path(folder) / "suite"
            suite.mkdir()
            (suite / "test_sample.py").write_text(textwrap.dedent(source), encoding="utf-8")
            output = Path(folder) / "reports"
            if preexisting_report:
                output.mkdir()
                (output / "report.json").write_text(json.dumps(preexisting_report))
            process = subprocess.run(
                [sys.executable, "-m", "scripts.test_stability",
                 "--start-directory", str(suite), "--output", str(output),
                 "--runs", "3", *options],
                cwd=ROOT, capture_output=True, text=True, timeout=30,
                env={**os.environ, "PYTHONHASHSEED": "99"},
            )
            self.assertIn(process.returncode, (0, 1), process.stderr)
            report = json.loads((output / "report.json").read_text())
            summary = (output / "summary.md").read_text()
            logs = [(output / f"run-{n}.log").read_text() for n in (1, 2, 3)]
            return process.returncode, report, summary, logs

    def test_stable_suite_passes_and_records_every_attempt(self):
        code, report, summary, logs = self.probe("""
            import unittest
            class Sample(unittest.TestCase):
                def test_ok(self):
                    self.assertEqual(2 + 2, 4)
        """)
        self.assertEqual(code, 0)
        self.assertTrue(report["successful"])
        self.assertEqual(report["stable_passed"], 1)
        self.assertEqual(report["flaky_tests"], [])
        self.assertEqual([r["hash_seed"] for r in report["runs"]], ["1", "2", "3"])
        self.assertEqual(report["tests"]["test_sample.Sample.test_ok"]["pass_rate"], 1)
        self.assertIn("**PASS**", summary)
        self.assertTrue(all("Ran 1 test" in log for log in logs))

    def test_failure_then_pass_is_flaky_and_still_fails(self):
        code, report, summary, logs = self.probe("""
            import os
            import unittest
            class Sample(unittest.TestCase):
                def test_changes(self):
                    self.assertNotEqual(os.environ["PYTHONHASHSEED"], "1")
        """)
        self.assertEqual(code, 1)
        test = "test_sample.Sample.test_changes"
        self.assertEqual(report["flaky_tests"], [test])
        self.assertEqual(report["tests"][test]["outcomes"], ["failure", "passed", "passed"])
        self.assertAlmostEqual(report["tests"][test]["pass_rate"], 2 / 3)
        self.assertIn(test, summary)
        self.assertIn("AssertionError", logs[0])

    def test_persistent_failure_is_not_mislabeled_as_flaky(self):
        code, report, _, _ = self.probe("""
            import unittest
            class Sample(unittest.TestCase):
                def test_broken(self):
                    self.fail("always broken")
        """)
        self.assertEqual(code, 1)
        self.assertEqual(report["flaky_tests"], [])
        self.assertEqual(report["tests"]["test_sample.Sample.test_broken"]["outcomes"],
                         ["failure"] * 3)

    def test_errors_subtests_and_unexpected_success_are_failures(self):
        code, report, _, logs = self.probe("""
            import unittest
            class Sample(unittest.TestCase):
                def test_error(self):
                    raise RuntimeError("test error")
                def test_subtests(self):
                    for number in range(2):
                        with self.subTest(number=number):
                            self.assertEqual(number, 0)
                @unittest.expectedFailure
                def test_unexpected(self):
                    pass
        """)
        self.assertEqual(code, 1)
        for method, outcome in (("error", "error"), ("subtests", "failure"),
                                ("unexpected", "unexpected_success")):
            self.assertEqual(report["tests"][f"test_sample.Sample.test_{method}"]["outcomes"],
                             [outcome] * 3)
        self.assertIn("number=1", logs[0])

    def test_skips_and_expected_failures_are_not_passes(self):
        code, report, _, _ = self.probe("""
            import unittest
            class Sample(unittest.TestCase):
                def test_ok(self):
                    pass
                @unittest.skip("fixture skip")
                def test_skipped(self):
                    pass
                @unittest.expectedFailure
                def test_expected(self):
                    self.fail("known failure")
        """)
        self.assertEqual(code, 0)
        self.assertEqual(report["stable_passed"], 1)
        for method, outcome in (("skipped", "skipped"), ("expected", "expected_failure")):
            self.assertEqual(report["tests"][f"test_sample.Sample.test_{method}"]["outcomes"],
                             [outcome] * 3)
            self.assertEqual(report["tests"][f"test_sample.Sample.test_{method}"]["pass_rate"], 0)

    def test_changing_skip_is_flagged(self):
        code, report, _, _ = self.probe("""
            import os
            import unittest
            class Sample(unittest.TestCase):
                @unittest.skipIf(os.environ["PYTHONHASHSEED"] == "1", "unstable skip")
                def test_changes(self):
                    pass
        """)
        self.assertEqual(code, 1)
        self.assertEqual(report["flaky_tests"], ["test_sample.Sample.test_changes"])

    def test_class_fixture_and_import_errors_fail(self):
        for source in (
            """
            import unittest
            class Sample(unittest.TestCase):
                @classmethod
                def setUpClass(cls):
                    raise RuntimeError("fixture error")
                def test_not_run(self):
                    pass
            """,
            "raise ImportError('discovery error')",
        ):
            with self.subTest(source=source):
                code, report, _, logs = self.probe(source)
                self.assertEqual(code, 1)
                self.assertTrue(all(not run["successful"] for run in report["runs"]))
                self.assertTrue(any("error" in data["outcomes"]
                                    for data in report["tests"].values()))
                self.assertIn("ERROR", logs[0])

    def test_crash_cannot_reuse_a_previous_success_report(self):
        code, report, summary, _ = self.probe(
            "import os; os._exit(0)", preexisting_report={"successful": True})
        self.assertEqual(code, 1)
        self.assertFalse(report["successful"])
        self.assertEqual(report["total_tests"], 0)
        self.assertTrue(all("no report" in run["problem"] for run in report["runs"]))
        self.assertIn("**FAIL**", summary)

    def test_timeout_produces_failure_evidence(self):
        code, report, summary, _ = self.probe("import time; time.sleep(10)",
                                            "--timeout", "0.1")
        self.assertEqual(code, 1)
        self.assertTrue(all(run["exit_code"] == 124 for run in report["runs"]))
        self.assertIn("worker timed out", summary)

    def test_empty_suite_fails(self):
        code, report, _, _ = self.probe("# no tests")
        self.assertEqual(code, 1)
        self.assertEqual(report["total_tests"], 0)


class StabilitySummary(unittest.TestCase):
    def test_missing_test_is_not_a_stable_pass(self):
        runs = [
            {"tests": {"example": "passed"}, "exit_code": 0, "successful": True},
            {"tests": {}, "exit_code": 0, "successful": True},
        ]
        report = summarize(runs)
        self.assertFalse(report["successful"])
        self.assertEqual(report["tests"]["example"]["outcomes"], ["passed", "missing"])
        self.assertEqual(report["stable_passed"], 0)
        self.assertEqual(report["flaky_tests"], [])  # Incomplete evidence, not a proven flake.

    def test_runner_failure_wins_even_when_test_outcomes_pass(self):
        runs = [
            {"tests": {"example": "passed"}, "exit_code": 1, "successful": True},
            {"tests": {"example": "passed"}, "exit_code": 0, "successful": True},
        ]
        self.assertFalse(summarize(runs)["successful"])


if __name__ == "__main__":
    unittest.main()
