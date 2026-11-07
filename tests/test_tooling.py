"""Executable contracts for the canonical development commands."""

import configparser
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class Tooling(unittest.TestCase):
    def test_test_command_collects_nested_quality_tests(self):
        result = subprocess.run(
            ["make", "-n", "test"], cwd=ROOT, capture_output=True, text=True, check=True
        )
        self.assertIn("-m scripts.test_stability --runs 1", result.stdout)
        self.assertIn("quality/tests", (ROOT / "pyproject.toml").read_text())
        self.assertIn("test_*.py", (ROOT / "pyproject.toml").read_text())

    def test_quality_composes_all_delivered_checks(self):
        result = subprocess.run(
            ["make", "-n", "quality"], cwd=ROOT, capture_output=True, text=True, check=True
        )
        for command in (
            "ruff",
            "compileall",
            "mypy",
            "deptry",
            "check_agents",
            "-m quality.measure",
        ):
            self.assertIn(command, result.stdout)

    def test_coverage_and_dashboard_use_one_gate_and_measurement(self):
        for arguments in (["coverage"], ["verify-coverage"], ["-f", "quality/Makefile", "metrics"]):
            result = subprocess.run(
                ["make", "-n", *arguments], cwd=ROOT, capture_output=True, text=True, check=True
            )
            self.assertEqual(result.stdout.count("-m quality.measure"), 1)
        config = configparser.ConfigParser()
        config.read(ROOT / "quality" / "coverage.ini")
        self.assertEqual(config["report"].getfloat("fail_under"), 80)
        self.assertTrue(config["run"].getboolean("branch"))
        self.assertEqual(config["run"]["source"].split(), ["builder", "scripts"])
        self.assertNotIn("omit", config["run"])
        self.assertNotIn("omit", config["report"])
        self.assertIn("pytest==8.4.2", (ROOT / "requirements-test.txt").read_text())
        self.assertIn("coverage==7.10.7", (ROOT / "quality/requirements.txt").read_text())

    def test_standalone_dashboard_setup_includes_pytest(self):
        result = subprocess.run(
            ["make", "-n", "-f", "quality/Makefile", "setup"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("-r requirements-test.txt", result.stdout)

    def test_compiler_is_forced_before_typechecking(self):
        result = subprocess.run(
            ["make", "-n", "typecheck"], cwd=ROOT, capture_output=True, text=True, check=True
        )
        self.assertLess(result.stdout.index("compileall -q -f"), result.stdout.index("-m mypy"))
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "bad.py"
            path.write_text("def invalid(:\n")
            result = subprocess.run(
                [sys.executable, "-m", "compileall", "-q", "-f", directory],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)

    def test_guidance_checker_rejects_broken_link(self):
        from scripts.check_agents import check

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "AGENTS.md").write_text("[Missing](missing.md)\n")
            self.assertTrue(check(root)[1])


if __name__ == "__main__":
    unittest.main()
