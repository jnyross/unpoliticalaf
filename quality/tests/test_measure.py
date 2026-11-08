"""Real tiny measured subprocesses exercise the gate without recursive full suites."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as et

from quality import measure


ROOT = Path(__file__).resolve().parents[2]


class CoverageMeasurement(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.output = self.root / "reports"
        for folder in ("builder", "scripts", "tests", "quality/tests"):
            (self.root / folder).mkdir(parents=True)
        for package in ("builder", "scripts"):
            (self.root / package / "__init__.py").write_text("")
        for module in ("build", "check"):
            (self.root / "builder" / f"{module}.py").write_text("answer = 42\n")
        # Use the real canonical worker, not a test substitute for pytest behavior.
        worker = ROOT / "scripts" / "test_performance.py"
        (self.root / "scripts" / "test_performance.py").write_text(
            f"import runpy\nrunpy.run_path({str(worker)!r}, run_name='__main__')\n"
        )
        (self.root / "tests" / "test_example.py").write_text("def test_ok():\n    assert True\n")
        (self.root / "quality/tests" / "test_nested.py").write_text(
            "def test_nested():\n    assert True\n"
        )
        (self.root / "pyproject.toml").write_text(
            '[tool.pytest.ini_options]\ntestpaths=["tests", "quality/tests"]\n'
        )
        (self.root / "quality" / "coverage.ini").write_bytes(
            (ROOT / "quality" / "coverage.ini").read_bytes()
        )
        environment = patch.dict(
            os.environ, {"PYTHONPATH": str(ROOT), "PYTEST_ADDOPTS": "-k absent"}
        )
        environment.start()
        self.addCleanup(environment.stop)

    def latest(self):
        return sorted(self.output.glob("invocation-*"))[-1]

    def test_fresh_combined_reports_match_xml_and_nested_timing_population(self):
        self.assertEqual(measure.measure(self.root, self.output), 0)
        output = self.latest()
        coverage = json.loads((output / "coverage.json").read_text())
        metrics = json.loads((output / "metrics.json").read_text())
        self.assertEqual(metrics["totals"], coverage["totals"])
        xml = et.parse(output / "coverage.xml").getroot()
        self.assertEqual(int(xml.attrib["lines-valid"]), metrics["totals"]["num_statements"])
        timing = json.loads((output / "test-timings" / "timings.json").read_text())
        self.assertEqual(timing["tests_run"], 2)
        self.assertEqual(timing["pytest_args"], [])
        self.assertEqual(timing["pytest_addopts"], "")
        self.assertTrue(any("quality/tests/test_nested.py" in name for name in timing["collected"]))
        self.assertIn("80% minimum", (output / "summary.md").read_text())
        self.assertIn("not unit tests alone", (output / "summary.md").read_text())

    def test_below_bar_rejects_unexecuted_recursive_sources_and_keeps_reports(self):
        nested = self.root / "builder" / "nested"
        nested.mkdir()
        (nested / "__init__.py").write_text("")
        (nested / "unused.py").write_text("".join(f"value_{i} = {i}\n" for i in range(100)))
        self.assertEqual(measure.measure(self.root, self.output), 2)
        output = self.latest()
        data = json.loads((output / "coverage.json").read_text())
        self.assertEqual(data["files"]["builder/nested/unused.py"]["summary"]["covered_lines"], 0)
        self.assertTrue((output / "index.html").is_file())
        self.assertIn("80", (output / "gate.log").read_text())

    def test_failed_measured_tests_never_reuse_earlier_success(self):
        self.assertEqual(measure.measure(self.root, self.output), 0)
        (self.root / "tests" / "test_example.py").write_text("def test_bad():\n    assert False\n")
        self.assertEqual(measure.measure(self.root, self.output), 1)
        invocations = list(self.output.glob("invocation-*"))
        self.assertEqual(len(invocations), 2)
        failures = [p for p in invocations if not (p / "metrics.json").exists()]
        self.assertEqual(len(failures), 1)
        phases = json.loads((failures[0] / "measurement.json").read_text())["phases"]
        self.assertEqual(phases[-1]["name"], "tests")
        self.assertEqual(phases[-1]["exit_code"], 1)
        self.assertIn("assert False", (failures[0] / "tests.log").read_text())

    def test_failed_build_or_check_preserves_original_status(self):
        for module in ("build", "check"):
            with self.subTest(module=module):
                path = self.root / "builder" / f"{module}.py"
                path.write_text("raise SystemExit(9)\n")
                self.assertEqual(measure.measure(self.root, self.output), 9)
                path.write_text("answer = 42\n")

    def test_measured_configuration_is_the_hashed_root_configuration(self):
        config = self.root / "quality" / "coverage.ini"
        config.write_text("[run]\nbranch = not-a-boolean\n")
        self.assertEqual(measure.measure(self.root, self.output), 1)
        output = self.latest()
        self.assertIn("not-a-boolean", (output / "build.log").read_text())
        self.assertFalse((output / "metrics.json").exists())

    def test_export_or_dashboard_failure_cannot_be_a_pass(self):
        original_run = subprocess.run
        for target in ("report", "html", "xml", "json", "quality.report"):
            with self.subTest(target=target):

                def fail_command(command, **kwargs):
                    if target in command:
                        return subprocess.CompletedProcess(command, 7)
                    return original_run(command, **kwargs)

                with patch.object(measure.subprocess, "run", side_effect=fail_command):
                    self.assertEqual(measure.measure(self.root, self.output), 7)


if __name__ == "__main__":
    unittest.main()
