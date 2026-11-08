"""Regression tests for the complexity gate; run via make complexity."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys
from unittest.mock import patch

from scripts import check_complexity as gate


def branching_function(name, branches):
    return (
        f"def {name}(value):\n"
        + "".join(f"    if value == {n}: return {n}\n" for n in range(branches))
        + "    return None\n"
    )


class ComplexityGate(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in gate.SOURCE_DIRS:
            directory = self.root / name
            directory.mkdir()
            (directory / "__init__.py").write_text("", encoding="utf-8")
        self.baseline({})

    def write(self, relative, source):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")

    def baseline(self, entries):
        self.write("complexity-baseline.json", json.dumps(entries))

    def run_gate(self):
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            return gate.main(self.root)

    def test_threshold_boundary_and_new_high_complexity_function(self):
        self.write("builder/example.py", branching_function("example", 19))
        self.assertEqual(self.run_gate(), 0)  # 19 decisions + 1 = ceiling 20
        self.write("builder/example.py", branching_function("example", 20))
        self.assertEqual(self.run_gate(), 1)
        self.assertIn(
            "complexity 21 exceeds ceiling 20", gate.violations(gate.measure(self.root), {})[0]
        )

    def test_existing_debt_is_measured_and_cannot_increase(self):
        self.baseline({"builder/example.py:example": 21})
        self.write("builder/example.py", branching_function("example", 20))
        self.assertEqual(self.run_gate(), 0)
        self.write("builder/example.py", branching_function("example", 21))
        self.assertEqual(self.run_gate(), 1)

    def test_improvement_requires_lowering_the_baseline(self):
        self.baseline({"builder/example.py:example": 23})
        self.write("builder/example.py", branching_function("example", 21))
        self.assertEqual(self.run_gate(), 1)
        self.baseline({"builder/example.py:example": 22})
        self.assertEqual(self.run_gate(), 0)

    def test_improvement_to_default_ceiling_requires_removing_entry(self):
        self.baseline({"builder/example.py:example": 21})
        self.write("builder/example.py", branching_function("example", 19))
        self.assertEqual(self.run_gate(), 1)
        self.baseline({})
        self.assertEqual(self.run_gate(), 0)

    def test_removed_or_renamed_functions_leave_obsolete_entries(self):
        self.baseline({"builder/example.py:old": 21})
        self.write("builder/example.py", "def renamed(): return 1\n")
        self.assertEqual(self.run_gate(), 1)

    def test_all_source_directories_are_checked_recursively(self):
        for directory in gate.SOURCE_DIRS:
            with self.subTest(directory=directory):
                path = f"{directory}/nested/example.py"
                self.write(path, branching_function("example", 20))
                self.assertEqual(self.run_gate(), 1)
                (self.root / path).unlink()

    def test_scopes_async_functions_and_closures_are_analyzed(self):
        self.write(
            "builder/scopes.py",
            "class Outer:\n"
            "    async def method(self, value):\n"
            "        def inner(value):\n"
            "            return 1 if value else 2\n"
            "        return inner(value)\n"
            "    class Inner:\n"
            "        def method(self): return 1\n",
        )
        scores = gate.measure(self.root)
        self.assertEqual(scores["builder/scopes.py:Outer.method"], 1)
        self.assertEqual(scores["builder/scopes.py:Outer.method.inner"], 2)
        self.assertEqual(scores["builder/scopes.py:Outer.Inner.method"], 1)

    def test_repeated_definitions_keep_the_largest_score(self):
        self.write(
            "builder/example.py", branching_function("example", 20) + "def example(): return 1\n"
        )
        self.assertEqual(self.run_gate(), 1)

    def test_invalid_baseline_is_an_analysis_failure(self):
        for contents in (
            "not json",
            "[]",
            '{"bad": 21}',
            '{"builder/a.py:f": true}',
            '{"builder/a.py:f": 20}',
        ):
            with self.subTest(contents=contents):
                self.write("complexity-baseline.json", contents)
                self.assertEqual(self.run_gate(), 2)

    def test_missing_baseline_is_an_analysis_failure(self):
        (self.root / "complexity-baseline.json").unlink()
        self.assertEqual(self.run_gate(), 2)

    def test_syntax_error_is_an_analysis_failure(self):
        self.write("scripts/broken.py", "def broken(:\n")
        self.assertEqual(self.run_gate(), 2)

    def test_empty_source_scope_is_an_analysis_failure(self):
        (self.root / "builder/__init__.py").unlink()
        self.assertEqual(self.run_gate(), 2)

    def test_renamed_function_cannot_borrow_another_functions_allowance(self):
        self.baseline({"builder/example.py:old": 22, "scripts/example.py:renamed": 25})
        self.write("builder/example.py", branching_function("renamed", 21))
        self.write("scripts/example.py", branching_function("renamed", 24))
        self.assertEqual(self.run_gate(), 1)
        problems = gate.violations(
            gate.measure(self.root), gate.load_baseline(self.root / "complexity-baseline.json")
        )
        self.assertTrue(
            any("builder/example.py:renamed" in p and "ceiling 20" in p for p in problems)
        )
        self.assertTrue(any("old: remove obsolete" in p for p in problems))

    def test_duplicate_baseline_identifiers_fail_closed(self):
        self.write("complexity-baseline.json", '{"builder/a.py:f": 21, "builder/a.py:f": 99}')
        self.assertEqual(self.run_gate(), 2)

    def test_invalid_baseline_identifiers_fail_closed(self):
        for name in (
            "outside/a.py:f",
            "builder/../a.py:f",
            "builder/a.txt:f",
            "builder/a.py:",
            "builder/a.py:f:other",
            "builder/a.py:not a name",
        ):
            with self.subTest(name=name):
                self.baseline({name: 21})
                self.assertEqual(self.run_gate(), 2)

    def test_analyzer_failure_has_analysis_exit_and_diagnostic(self):
        self.write("builder/example.py", "def example(): return 1\n")
        output = StringIO()
        with patch.object(gate, "cc_visit_ast", side_effect=RuntimeError("analyzer failed")):
            with redirect_stderr(output), redirect_stdout(StringIO()):
                self.assertEqual(gate.main(self.root), 2)
        self.assertIn("analyzer failed", output.getvalue())

    def test_invalid_source_encoding_fails_closed(self):
        (self.root / "builder/bad.py").write_bytes(b"\xff")
        self.assertEqual(self.run_gate(), 2)

    def test_gate_does_not_rewrite_baseline_on_failure(self):
        self.baseline({"builder/example.py:old": 21})
        self.write("builder/example.py", branching_function("new", 21))
        path = self.root / "complexity-baseline.json"
        before = path.read_bytes()
        self.assertEqual(self.run_gate(), 1)
        self.assertEqual(path.read_bytes(), before)

    def test_cli_preserves_success_violation_and_analysis_exit_codes(self):
        command = [
            sys.executable,
            "-c",
            "from pathlib import Path; import sys; "
            "from scripts.check_complexity import main; "
            "raise SystemExit(main(Path(sys.argv[1])))",
            str(self.root),
        ]
        self.write("builder/example.py", branching_function("example", 19))
        passed = subprocess.run(command, cwd=gate.ROOT, capture_output=True, text=True)
        self.assertEqual(passed.returncode, 0, passed.stderr)
        self.assertIn("Complexity gate passed", passed.stdout)
        self.write("builder/example.py", branching_function("example", 20))
        rejected = subprocess.run(command, cwd=gate.ROOT, capture_output=True, text=True)
        self.assertEqual(rejected.returncode, 1)
        self.assertIn("complexity 21 exceeds ceiling 20", rejected.stderr)
        self.write("complexity-baseline.json", "not json")
        failed = subprocess.run(command, cwd=gate.ROOT, capture_output=True, text=True)
        self.assertEqual(failed.returncode, 2)
        self.assertIn("Complexity analysis failed", failed.stderr)
