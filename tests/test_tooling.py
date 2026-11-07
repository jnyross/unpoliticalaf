"""Executable contracts for the canonical development commands."""

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
        self.assertIn("-m pytest", result.stdout)
        self.assertIn("quality/tests", result.stdout)
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
            "quality/report.py",
        ):
            self.assertIn(command, result.stdout)

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
