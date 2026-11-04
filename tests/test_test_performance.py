"""Timing reports must measure real tests without hiding unittest failures."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import test_performance


class PerformanceReports(unittest.TestCase):
    def run_report(self, suite):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "reports"
            with contextlib.redirect_stdout(io.StringIO()):
                status = test_performance.run_suite(suite, destination, stream=io.StringIO())
            report = json.loads((destination / "timings.json").read_text(encoding="utf-8"))
            summary = (destination / "summary.md").read_text(encoding="utf-8")
        return status, report, summary

    def test_monotonic_timings_include_setup_teardown_and_cleanups(self):
        events = []

        class Example(unittest.TestCase):
            def setUp(self):
                events.append("setup")
                self.addCleanup(events.append, "cleanup")

            def test_pass(self):
                events.append("test")

            def tearDown(self):
                events.append("teardown")

        def clock():
            # Suite start, test start, test stop (after cleanup), suite stop.
            if events:
                self.assertEqual(events, ["setup", "test", "teardown", "cleanup"])
            return next(ticks)

        ticks = iter([10, 11, 11.25, 12])
        with patch.object(test_performance, "perf_counter", side_effect=clock):
            status, report, summary = self.run_report(unittest.TestSuite([Example("test_pass")]))
        self.assertEqual(status, 0)
        self.assertTrue(report["successful"])
        self.assertEqual(report["suite_seconds"], 2)
        self.assertEqual(report["tests"][0]["seconds"], 0.25)
        self.assertEqual(report["tests_run"], 1)
        self.assertIn("1 tests in **2.000 seconds**", summary)

    def test_failed_outcomes_are_retained_and_return_nonzero(self):
        class Examples(unittest.TestCase):
            def test_failure(self):
                self.fail("intentional fixture failure")

            def test_error(self):
                raise RuntimeError("intentional fixture error")

            def test_subtest(self):
                with self.subTest(value=1):
                    self.fail("intentional subtest failure")

            @unittest.skip("intentional fixture skip")
            def test_skip(self):
                pass

            @unittest.expectedFailure
            def test_expected_failure(self):
                self.fail("expected fixture failure")

            @unittest.expectedFailure
            def test_unexpected_success(self):
                pass

        suite = unittest.TestLoader().loadTestsFromTestCase(Examples)
        status, report, summary = self.run_report(suite)
        self.assertEqual(status, 1)
        self.assertFalse(report["successful"])
        self.assertEqual(report["tests_run"], 6)
        self.assertEqual(len(report["tests"]), 6)
        self.assertEqual(report["failures"], 2)
        self.assertEqual(report["errors"], 1)
        self.assertEqual(report["skipped"], 1)
        self.assertEqual(report["expected_failures"], 1)
        self.assertEqual(report["unexpected_successes"], 1)
        self.assertIn("**failed**", summary)

    def test_empty_suite_fails_with_a_report(self):
        status, report, summary = self.run_report(unittest.TestSuite())
        self.assertEqual(status, 1)
        self.assertEqual(report["tests_run"], 0)
        self.assertFalse(report["successful"])
        self.assertIn("No tests were discovered", summary)

    def test_slowest_ten_are_sorted_but_json_keeps_every_test(self):
        suite = unittest.TestSuite([unittest.FunctionTestCase(lambda: None) for _ in range(12)])
        ticks = [0]
        for duration in range(1, 13):
            ticks.extend([100, 100 + duration])
        ticks.append(200)
        with patch.object(test_performance, "perf_counter", side_effect=ticks):
            status, report, summary = self.run_report(suite)
        self.assertEqual(status, 0)
        self.assertEqual([row["seconds"] for row in report["tests"]], list(range(12, 0, -1)))
        self.assertEqual(summary.count("| `"), 10)
        self.assertIn("| 12.000000 |", summary)
        self.assertNotIn("| 2.000000 |", summary)
        self.assertIn("python", report)
        self.assertIn("platform", report)
        self.assertIn("generated_at", report)

    def test_discovery_import_errors_fail_and_still_write_reports(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "test_broken_fixture.py").write_text(
                "raise RuntimeError('intentional import failure')\n", encoding="utf-8",
            )
            destination = root / "reports"
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                status = test_performance.main(["-s", folder, "--report-dir", str(destination)])
            report = json.loads((destination / "timings.json").read_text(encoding="utf-8"))
        self.assertEqual(status, 1)
        self.assertEqual(report["errors"], 1)
        self.assertEqual(report["tests_run"], 1)
        self.assertEqual(len(report["tests"]), 1)
        self.assertFalse(report["successful"])


if __name__ == "__main__":
    unittest.main()
