"""Performance reports must expose failures, not reward fast broken builds."""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import build_performance as perf


class Measurement(unittest.TestCase):
    def measure(self, duration, exit_code=0, budget=90):
        with patch.object(perf, "perf_counter", side_effect=[10.0, 10.0 + duration]), \
                patch.object(perf.platform, "platform", return_value="Linux-test"), \
                patch.object(perf.subprocess, "run", return_value=subprocess.CompletedProcess(["make", "build"], exit_code)) as run:
            report = perf.measure_build(budget)
        run.assert_called_once_with(["make", "build"], cwd=perf.ROOT, check=False)
        return report

    def test_measures_real_command_with_monotonic_clock(self):
        report = self.measure(44.5)
        self.assertEqual(report["duration_seconds"], 44.5)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["schema_version"], 1)
        self.assertTrue(report["started_at"].endswith("+00:00"))

    def test_at_budget_passes_but_above_budget_fails(self):
        self.assertEqual(self.measure(90)["status"], "passed")
        self.assertEqual(self.measure(90.1)["status"], "over_budget")

    def test_fast_failed_build_is_still_a_failure(self):
        report = self.measure(0.1, exit_code=2)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["exit_code"], 2)

    def test_failed_build_takes_priority_over_budget(self):
        self.assertEqual(self.measure(95, exit_code=2)["status"], "failed")

    def test_missing_make_is_recorded(self):
        with patch.object(perf.subprocess, "run", side_effect=FileNotFoundError("make")), \
                contextlib.redirect_stderr(io.StringIO()):
            report = perf.measure_build(90)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["exit_code"], 127)

    def test_only_named_ci_context_is_retained(self):
        with patch.dict(os.environ, {"GITHUB_SHA": "a" * 40, "GITHUB_RUN_ID": "123", "PRIVATE_TOKEN": "not-for-reports"}):
            report = self.measure(1)
        self.assertEqual(report["commit"], "a" * 40)
        self.assertEqual(report["run_id"], "123")
        self.assertNotIn("not-for-reports", json.dumps(report))

    def test_invalid_budgets_are_refused(self):
        for value in ("0", "-1", "nan", "inf"):
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                perf.positive_seconds(value)
        self.assertEqual(perf.positive_seconds("1.5"), 1.5)


class Reports(unittest.TestCase):
    def test_json_and_summary_survive_failure_and_budget_breach(self):
        for status, exit_code, expected in (("passed", 0, 0), ("over_budget", 0, 1), ("failed", 2, 2)):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp) / "metrics/build.json"
                summary = Path(tmp) / "summary.md"
                summary.write_text("Earlier step\n", encoding="utf-8")
                report = {"status": status, "exit_code": exit_code, "duration_seconds": 91.25, "max_seconds": 90}
                with patch.object(perf, "measure_build", return_value=report) as measure, \
                        patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}), \
                        contextlib.redirect_stdout(io.StringIO()):
                    code = perf.main(["--output", str(output), "--max-seconds", "90"])
                measure.assert_called_once_with(90)
                self.assertEqual(code, expected)
                self.assertEqual(json.loads(output.read_text()), report)
                self.assertTrue(summary.read_text().startswith("Earlier step\n"))
                self.assertIn("91.25s", summary.read_text())
                self.assertIn(status, summary.read_text())


if __name__ == "__main__":
    unittest.main()
