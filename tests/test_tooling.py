"""Executable contracts for the canonical development commands."""

import configparser
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class Tooling(unittest.TestCase):
    def test_version_keeps_the_same_repository_root_without_importing_readers(self):
        from builder import readers, version

        self.assertEqual(version.ROOT, readers.ROOT)

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
            "scripts/check_complexity.py",
            "lint-imports --config .importlinter --no-cache",
            "-m pytest tests/architecture",
        ):
            self.assertIn(command, result.stdout)

    def test_architecture_reuses_pin_and_virtualenv_and_precedes_regressions(self):
        self.assertIn(
            "-r requirements-architecture.txt", (ROOT / "requirements-test.txt").read_text()
        )
        self.assertIn("import-linter==2.15", (ROOT / "requirements-architecture.txt").read_text())
        result = subprocess.run(
            ["make", "-n", "architecture", "VENV=/tmp/architecture-venv"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("/tmp/architecture-venv/bin/lint-imports", result.stdout)
        self.assertIn("/tmp/architecture-venv/bin/python", result.stdout)
        self.assertLess(result.stdout.index("lint-imports"), result.stdout.index("-m pytest"))

    def test_complexity_reuses_dashboard_pin_and_original_source_population(self):
        from scripts import check_complexity

        self.assertEqual(check_complexity.SOURCE_DIRS, ("builder", "scripts", "tests"))
        self.assertEqual(check_complexity.MAX_COMPLEXITY, 20)
        result = subprocess.run(
            ["make", "-n", "setup-quality", "complexity"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("-r quality/requirements.txt", result.stdout)
        self.assertIn("unittest discover -s tests/quality", result.stdout)
        self.assertIn("radon==6.0.1", (ROOT / "quality/requirements.txt").read_text())

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
