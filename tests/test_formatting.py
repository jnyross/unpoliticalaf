"""Exercise the real canonical lint/format targets on disposable source trees."""

import ast
import hashlib
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = ("builder", "scripts", "tests", "quality")
SOURCE_PATHS = tuple(
    Path(folder) / nested / "new_module.py"
    for folder in SOURCE_ROOTS
    for nested in ("nested", "nested/data")
)


def file_hashes(root):
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file() and not any(part.endswith("_cache") for part in path.parts)
    }


class Formatting(unittest.TestCase):
    def fixture(self, root):
        for name in ("Makefile", "pyproject.toml", "ruff.toml"):
            shutil.copyfile(ROOT / name, root / name)
        for relative in SOURCE_PATHS:
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            (root / relative).write_text("value = 1\n")
        # A nested configuration must not override the repository policy.
        (root / "quality" / "pyproject.toml").write_text(
            '[tool.black]\nline-length = 10\n[tool.ruff.lint]\nignore = ["F821"]\n'
        )
        for name in ("reference", "data", "site", ".factory"):
            (root / name).mkdir()
            (root / name / "untouched.py").write_text("invalid Python here !!!\n")

    def make(self, root, target):
        return subprocess.run(
            ["make", f"RUN_PYTHON={sys.executable}", target],
            cwd=root,
            text=True,
            capture_output=True,
        )

    def require_tools(self):
        for module in ("black", "ruff"):
            if importlib.util.find_spec(module) is None:
                self.skipTest(f"{module} is a development tool; run make setup-dev")

    def test_quality_includes_nonmutating_black_check(self):
        result = subprocess.run(
            ["make", "-n", "quality"], cwd=ROOT, capture_output=True, text=True, check=True
        )
        self.assertIn("-m black --config pyproject.toml --check --diff", result.stdout)
        self.assertNotIn("-m ruff format", result.stdout)
        result = subprocess.run(
            ["make", "-n", "format"], cwd=ROOT, capture_output=True, text=True, check=True
        )
        self.assertIn(
            "-m black --config pyproject.toml builder scripts tests quality", result.stdout
        )

    def test_nested_format_negatives_fail_check_and_quality_without_writes(self):
        self.require_tools()
        for relative in SOURCE_PATHS:
            with self.subTest(source=relative), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.fixture(root)
                path = root / relative
                path.write_text("value=1\n")
                before = file_hashes(root)
                for target in ("format-check", "quality"):
                    result = self.make(root, target)
                    self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn("would reformat", result.stdout + result.stderr)
                    self.assertEqual(before, file_hashes(root))

    def test_nested_lint_negatives_fail_check_and_quality_without_writes(self):
        self.require_tools()
        for relative in SOURCE_PATHS:
            with self.subTest(source=relative), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.fixture(root)
                (root / relative).write_text("print(undefined_name)\n")
                before = file_hashes(root)
                for target in ("lint", "quality"):
                    result = self.make(root, target)
                    self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn("F821", result.stdout + result.stderr)
                    self.assertEqual(before, file_hashes(root))

    def test_format_is_recursive_idempotent_and_preserves_ast_and_public_names(self):
        self.require_tools()
        source = (
            "FACT_ID='etb.2a.directtax.1'\n"
            "def public_value(amount_bn):\n"
            " return {'fact_id':FACT_ID,'url':'/who-pays.html#income-tax',"
            "'worksheet':'Table 2a','value':amount_bn}\n"
        )
        # This 97-column call stays on one line at 100, but not at 88 or 10.
        argument = "x" * 72
        source += f"result = public_value('{argument}')\n"
        expected_call = f'result = public_value("{argument}")'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            for relative in SOURCE_PATHS:
                (root / relative).write_text(source)
            untouched = {
                name: (root / name / "untouched.py").read_bytes()
                for name in ("reference", "data", "site", ".factory")
            }
            before = file_hashes(root)
            result = self.make(root, "format")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            after = file_hashes(root)
            self.assertNotEqual(before, after)
            formatted_sources = set()
            for relative in SOURCE_PATHS:
                formatted = (root / relative).read_text()
                self.assertEqual(ast.dump(ast.parse(source)), ast.dump(ast.parse(formatted)))
                self.assertIn(expected_call, formatted.splitlines())
                formatted_sources.add(formatted)
            self.assertEqual(len(formatted_sources), 1)
            for target in ("format-check", "lint", "format"):
                result = self.make(root, target)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(after, file_hashes(root))
            for name, content in untouched.items():
                self.assertEqual(content, (root / name / "untouched.py").read_bytes())


if __name__ == "__main__":
    unittest.main()
