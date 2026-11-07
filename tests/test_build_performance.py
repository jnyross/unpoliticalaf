"""Performance reports expose failures rather than reward fast broken builds."""

import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts import build_performance as perf


class Measurement(unittest.TestCase):
    def measure(self, duration, exit_code=0, budget=90):
        with (
            patch.object(perf, "perf_counter", side_effect=[10.0, 10.0 + duration]),
            patch.object(perf.platform, "platform", return_value="Linux-test"),
            patch.object(
                perf.subprocess,
                "run",
                return_value=subprocess.CompletedProcess(["make", "build"], exit_code),
            ) as run,
        ):
            report = perf.measure_build(budget)
        run.assert_called_once_with(["make", "build"], cwd=perf.ROOT, check=False)
        return report

    def test_measures_real_command_with_monotonic_clock(self):
        report = self.measure(44.5)
        self.assertEqual(report["duration_seconds"], 44.5)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["schema_version"], 1)
        self.assertTrue(report["started_at"].endswith("+00:00"))
        self.assertEqual(perf.DEFAULT_MAX_SECONDS, 90)

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
        with (
            patch.object(perf.subprocess, "run", side_effect=FileNotFoundError("make")),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            report = perf.measure_build(90)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["exit_code"], 127)

    def test_only_named_context_is_retained(self):
        with patch.dict(
            os.environ,
            {
                "GITHUB_SHA": "a" * 40,
                "GITHUB_RUN_ID": "123",
                "BUILD_PIP_CACHE_HIT": "true",
                "PRIVATE_TOKEN": "not-for-reports",
            },
        ):
            report = self.measure(1)
        self.assertEqual(report["commit"], "a" * 40)
        self.assertEqual(report["run_id"], "123")
        self.assertEqual(report["cache"]["pip_cache_hit"], True)
        self.assertEqual(report["cache"]["glossary_maxsize"], 4096)
        self.assertEqual(report["cache"]["glossary_initial_entries"], 0)
        self.assertFalse(report["cache"]["restored_build_output"])
        self.assertNotIn("not-for-reports", json.dumps(report))
        self.assertIn("setup and independent make check/tests excluded", report["measurement"])

    def test_prebuild_context_is_observed_before_the_subprocess(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "site").mkdir()
            (root / "builder/__pycache__").mkdir(parents=True)
            with patch.object(perf, "ROOT", root), patch.dict(os.environ, {}, clear=True):
                report = self.measure(1)
        self.assertTrue(report["cache"]["site_existed"])
        self.assertTrue(report["cache"]["builder_bytecode_existed"])
        self.assertIsNone(report["cache"]["pip_cache_hit"])
        self.assertEqual(report["python_executable"], sys.executable)

    def test_invalid_budgets_are_refused(self):
        for value in ("0", "-1", "nan", "inf", "not-a-number"):
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                perf.positive_seconds(value)
        self.assertEqual(perf.positive_seconds("1.5"), 1.5)


class Reports(unittest.TestCase):
    def test_make_and_ci_preserve_the_canonical_gates_and_budget(self):
        result = subprocess.run(
            ["make", "-n", "benchmark"], cwd=perf.ROOT, capture_output=True, text=True, check=True
        )
        self.assertIn(".venv/bin/python scripts/build_performance.py", result.stdout)
        self.assertNotIn("--max-seconds", result.stdout)
        workflow = (perf.ROOT / ".github/workflows/check.yml").read_text()
        self.assertIn("run: make benchmark", workflow)
        self.assertLess(workflow.index("run: make benchmark"), workflow.index("--collect-only"))
        # Coverage now measures build + check + the same canonical timed tests.
        self.assertIn("run: make verify-coverage", workflow)
        self.assertIn("run: make test-stability", workflow)
        self.assertIn("run: make quality", workflow)
        self.assertIn("if-no-files-found: error", workflow)
        self.assertIn("include-hidden-files: true", workflow)
        self.assertNotIn("--max-seconds", workflow)
        self.assertNotIn("continue-on-error", workflow)

    def test_json_and_summary_survive_failure_and_budget_breach(self):
        for status, exit_code, expected in (
            ("passed", 0, 0),
            ("over_budget", 0, 1),
            ("failed", 2, 2),
        ):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp) / "metrics/build.json"
                summary = Path(tmp) / "summary.md"
                summary.write_text("Earlier step\n", encoding="utf-8")
                report = {
                    "status": status,
                    "exit_code": exit_code,
                    "duration_seconds": 91.25,
                    "max_seconds": 90,
                    "cache": {"glossary_maxsize": 4096},
                }
                with (
                    patch.object(perf, "measure_build", return_value=report) as measure,
                    patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}),
                    contextlib.redirect_stdout(io.StringIO()),
                ):
                    code = perf.main(["--output", str(output), "--max-seconds", "90"])
                measure.assert_called_once_with(90)
                self.assertEqual(code, expected)
                self.assertEqual(json.loads(output.read_text()), report)
                self.assertTrue(summary.read_text().startswith("Earlier step\n"))
                self.assertIn("91.25s", summary.read_text())
                self.assertIn(status, summary.read_text())

    def test_real_make_failure_and_overbudget_exit_nonzero(self):
        for command, budget, expected_status, expected_code in (
            ("exit 7", "90", "failed", 2),
            (f'{sys.executable} -c "import time; time.sleep(0.05)"', "0.001", "over_budget", 1),
        ):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "Makefile").write_text(f".PHONY: build\nbuild:\n\t{command}\n")
                output = root / "result.json"
                # A new interpreter calls the real make subprocess, not a mock.
                program = (
                    "from pathlib import Path; from scripts import build_performance as p; "
                    f"p.ROOT=Path({str(root)!r}); "
                    f"raise SystemExit(p.main(['--output',{str(output)!r},"
                    f"'--max-seconds',{budget!r}]))"
                )
                result = subprocess.run(
                    [sys.executable, "-c", program],
                    cwd=perf.ROOT,
                    capture_output=True,
                    text=True,
                    # Failure fixtures must not append fake results to the real CI summary.
                    env={**os.environ, "GITHUB_STEP_SUMMARY": str(root / "summary.md")},
                )
                self.assertEqual(result.returncode, expected_code, result.stdout + result.stderr)
                report = json.loads(output.read_text())
                self.assertEqual(report["status"], expected_status)
                self.assertIn(expected_status, (root / "summary.md").read_text())


if __name__ == "__main__":
    unittest.main()
