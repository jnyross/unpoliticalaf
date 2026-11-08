"""Exercise the real import contracts in isolated copies, never the checkout."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class ImportContracts(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for package in ("builder", "scripts"):
            shutil.copytree(
                ROOT / package,
                self.root / package,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
        shutil.copy2(ROOT / ".importlinter", self.root / ".importlinter")

    def add_import(self, module, statement):
        path = self.root / (module.replace(".", "/") + ".py")
        with path.open("a", encoding="utf-8") as stream:
            stream.write("\n" + statement + "\n")

    def lint(self):
        return subprocess.run(
            [
                str(Path(sys.executable).with_name("lint-imports")),
                "--config",
                ".importlinter",
                "--no-cache",
            ],
            cwd=self.root,
            env={**os.environ, "PYTHONPATH": str(self.root), "NO_COLOR": "1"},
            text=True,
            capture_output=True,
            timeout=30,
        )

    def assert_broken(self, contract):
        result = self.lint()
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, output)
        self.assertIn(contract + " BROKEN", output)

    def test_current_architecture_passes(self):
        result = self.lint()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Contracts: 5 kept, 0 broken.", result.stdout)

    def test_builder_cannot_import_scripts(self):
        self.add_import("builder.pages_home", "import scripts.user_test")
        self.assert_broken("Builder must not depend on operational scripts")

    def test_page_cannot_import_build_orchestration(self):
        self.add_import("builder.pages_home", "from . import build")
        self.assert_broken("Build orchestration is not a library")

    def test_producer_cannot_import_checker_even_inside_a_function(self):
        self.add_import(
            "builder.data",
            "def architecture_probe():\n    from . import check",
        )
        self.assert_broken("Production modules must not depend on the checker")

    def add_nested_import(self, statement):
        package = self.root / "builder" / "feature"
        package.mkdir()
        (package / "__init__.py").write_text('"""Feature fixture."""\n')
        self.add_import("builder.feature.worker", statement)

    def test_nested_module_cannot_import_build_orchestration(self):
        self.add_nested_import("from .. import build")
        self.assert_broken("Build orchestration is not a library")

    def test_nested_module_cannot_import_checker(self):
        self.add_nested_import("import builder.check")
        self.assert_broken("Production modules must not depend on the checker")

    def test_package_initializer_cannot_import_build_orchestration(self):
        self.add_import("builder.__init__", "from . import build")
        self.assert_broken("Build orchestration is not a library")

    def test_package_initializer_cannot_import_checker(self):
        self.add_import("builder.__init__", "from . import check")
        self.assert_broken("Production modules must not depend on the checker")

    def test_checker_cannot_reuse_fact_producer(self):
        self.add_import("builder.check", "from builder.data import build_all")
        self.assert_broken("Checkers must remain independent of producers")

    def test_checker_cannot_import_fiscal_formula_inside_function(self):
        self.add_import(
            "builder.check",
            "def architecture_probe():\n    from .data_top_earners import build",
        )
        self.assert_broken("Checkers must remain independent of producers")

    def test_calculation_checker_cannot_import_fiscal_producer(self):
        self.add_import("builder.check_calculations", "from . import data")
        self.assert_broken("Checkers must remain independent of producers")

    def test_producer_cannot_import_calculation_checker(self):
        self.add_import("builder.data", "from . import check_calculations")
        self.assert_broken("Production modules must not depend on the checker")

    def test_logging_cannot_bridge_checker_to_fiscal_producer(self):
        self.add_import("builder.logging", "from . import data")
        self.assert_broken("Shared helpers must stay below facts and pages")

    def test_shared_dependency_free_logging_passes(self):
        self.add_import("builder.data", "from .logging import get_logger")
        result = self.lint()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_version_cannot_regain_reader_dependency(self):
        self.add_import("builder.version", "from .readers import ROOT")
        self.assert_broken("Shared helpers must stay below facts and pages")

    def test_syntax_error_fails_instead_of_passing_empty_graph(self):
        self.add_import("builder.pages_home", "def invalid(:")
        result = self.lint()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("Contracts: 5 kept, 0 broken.", result.stdout)

    def test_analyzer_configuration_error_fails_closed(self):
        config = self.root / ".importlinter"
        config.write_text(config.read_text().replace("type = forbidden", "type = nonexistent"))
        result = self.lint()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("Contracts: 5 kept, 0 broken.", result.stdout)

    def test_make_stops_on_analyzer_error_before_running_regressions(self):
        self.add_import("builder.pages_home", "def invalid(:")
        result = subprocess.run(
            [
                "make",
                "-f",
                str(ROOT / "Makefile"),
                "architecture",
                f"VENV={Path(sys.executable).parent.parent}",
            ],
            cwd=self.root,
            env={**os.environ, "PYTHONPATH": str(self.root)},
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("-m pytest", result.stdout)

    def test_accuracy_audit_cannot_reuse_page_producer(self):
        self.add_import("scripts.accuracy_check", "import builder.pages_money")
        self.assert_broken("Checkers must remain independent of producers")

    def test_shared_helper_cannot_import_pages(self):
        self.add_import("builder.html", "from . import pages_home")
        self.assert_broken("Shared helpers must stay below facts and pages")

    def test_indirect_checker_dependency_is_rejected(self):
        self.add_import("builder.check", "from . import architecture_bridge")
        self.add_import("builder.architecture_bridge", "from . import data")
        self.assert_broken("Checkers must remain independent of producers")

    def test_new_modules_cannot_bypass_foundation_boundary(self):
        self.add_import("builder.findings", "from . import new_feature")
        self.add_import("builder.new_feature", "VALUE = 1")
        self.assert_broken("Shared helpers must stay below facts and pages")

    def add_feature_flags(self, *, html_import=True):
        if not (self.root / "builder" / "feature_flags.py").exists():
            self.add_import("builder.feature_flags", '"""Dependency-free configuration fixture."""')
        if html_import:
            self.add_import("builder.html", "from . import feature_flags")

    def test_html_can_consume_dependency_free_feature_flags(self):
        self.add_feature_flags()
        result = self.lint()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_other_helpers_cannot_consume_feature_flags(self):
        self.add_feature_flags()
        self.add_import("builder.findings", "from . import feature_flags")
        self.assert_broken("Shared helpers must stay below facts and pages")

    def test_feature_flags_cannot_import_fact_producers(self):
        self.add_feature_flags()
        self.add_import("builder.feature_flags", "from . import data")
        self.assert_broken("Shared helpers must stay below facts and pages")

    def test_feature_flags_cannot_import_pages_indirectly(self):
        self.add_feature_flags()
        self.add_import("builder.feature_flags", "from . import architecture_bridge")
        self.add_import("builder.architecture_bridge", "from . import pages_home")
        self.assert_broken("Shared helpers must stay below facts and pages")

    def test_present_but_unused_optional_permission_is_an_error(self):
        self.add_feature_flags(html_import=False)
        path = self.root / "builder" / "html.py"
        path.write_text(path.read_text().replace(", feature_flags", ""), encoding="utf-8")
        result = self.lint()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("builder.html -> builder.feature_flags", result.stdout + result.stderr)

    def test_unused_existing_permission_remains_an_error(self):
        path = self.root / "builder" / "rates.py"
        path.write_text(path.read_text().replace("from .readers import ROOT", ""), encoding="utf-8")
        result = self.lint()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("builder.rates -> builder.readers", result.stdout + result.stderr)

    def test_optional_permissions_cannot_use_wildcards(self):
        config = self.root / ".importlinter"
        config.write_text(
            config.read_text().replace(
                "builder.html -> builder.feature_flags",
                "builder.* -> builder.feature_flags",
            ),
            encoding="utf-8",
        )
        result = self.lint()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("exact declared optional module", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
