"""Real tool failures, isolated from the retained source and generated site."""

import importlib.util
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ToolFailures(unittest.TestCase):
    def run_tool(self, module, arguments, cwd):
        if importlib.util.find_spec(module) is None:
            self.skipTest(f"{module} is a development tool; run make setup-dev")
        return subprocess.run(
            [sys.executable, "-m", module, *arguments], cwd=cwd, capture_output=True, text=True
        )

    def test_ruff_rejects_unused_import_and_undefined_name(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.py"
            path.write_text("import os\nprint(undefined_name)\n")
            result = self.run_tool(
                "ruff", ["check", "--config", str(ROOT / "ruff.toml"), str(path)], directory
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("F401", result.stdout)
            self.assertIn("F821", result.stdout)

    def test_strict_typing_rejects_real_core_api_misuse(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.py"
            path.write_text(
                "from builder.rates import EmployeeIllustration\n"
                "from builder.downloads import raw\n"
                "def untyped(value):\n    return value\n"
                "def wrong(value: EmployeeIllustration) -> int:\n"
                "    value['salary'] = 'not a number'\n"
                "    value['invented'] = 1\n"
                "    raw('not a number')\n"
                "    return 'not an int'\n"
            )
            result = self.run_tool(
                "mypy",
                ["--config-file", str(ROOT / "mypy.ini"), "--no-incremental", str(path)],
                ROOT,
            )
            self.assertNotEqual(result.returncode, 0)
            for code in (
                "no-untyped-def",
                "typeddict-item",
                "unknown-key",
                "arg-type",
                "return-value",
            ):
                self.assertIn(code, result.stdout)

    def test_deptry_rejects_missing_transitive_unused_and_runtime_dev_imports(self):
        cases = [
            ("import deliberately_missing_dependency\n", "openpyxl==3.1.5\n", "", "DEP001"),
            ("import et_xmlfile\n", "openpyxl==3.1.5\n", "", "DEP003"),
            ("", "pypdf==5.1.0\n", "", "DEP002"),
            ("import pytest\n", "", "pytest==8.4.2\n", "DEP004"),
        ]
        for source, runtime, development, code in cases:
            with self.subTest(code=code), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "app.py").write_text(source)
                (root / "requirements.txt").write_text(runtime)
                (root / "requirements-dev.txt").write_text(development)
                (root / "pyproject.toml").write_text(
                    '[tool.deptry]\nrequirements_files = ["requirements.txt"]\n'
                    'requirements_files_dev = ["requirements-dev.txt"]\n'
                )
                result = self.run_tool("deptry", ["."], root)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(code, result.stdout + result.stderr)

    def test_pytest_collects_nested_tests_but_not_similar_names(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "nested"
            nested.mkdir()
            for name in ("test_included.py", "testexcluded.py", "excluded_test.py"):
                (nested / name).write_text("def test_probe():\n    pass\n")
            result = self.run_tool(
                "pytest",
                ["--collect-only", "-q", "-c", str(ROOT / "pyproject.toml"), str(root)],
                root,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("test_included.py", result.stdout)
            self.assertNotIn("testexcluded.py", result.stdout)
            self.assertNotIn("excluded_test.py", result.stdout)

    def test_canonical_dependency_config_follows_nested_dev_requirements(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "quality").mkdir()
            for path in (
                "pyproject.toml",
                "requirements.txt",
                "requirements-dev.txt",
                "requirements-test.txt",
                "requirements-a11y.txt",
                "requirements-typing.txt",
                "quality/requirements.txt",
            ):
                shutil.copyfile(ROOT / path, root / path)
            (root / "app.py").write_text("import pytest\n")
            result = self.run_tool("deptry", ["."], root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("DEP004", result.stdout + result.stderr)
