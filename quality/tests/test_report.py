"""Exercise actual Radon analysis, coverage joins and the exported dashboard."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "quality_report", Path(__file__).parents[1] / "report.py"
)
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class QualityReport(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "builder").mkdir()
        (self.root / "scripts").mkdir()
        (self.root / "builder" / "example.py").write_text(
            "def choose(value):\n    if value:\n        return 1\n    return 0\n",
            encoding="utf-8",
        )
        (self.root / "scripts" / "unused.py").write_text("answer = 42\n", encoding="utf-8")
        summary = {
            "num_statements": 4,
            "covered_lines": 3,
            "num_branches": 2,
            "covered_branches": 1,
        }
        self.coverage = {
            "totals": {
                "num_statements": 5,
                "covered_lines": 3,
                "num_branches": 2,
                "covered_branches": 1,
            },
            "files": {
                "builder/example.py": {"summary": summary},
                "scripts/unused.py": {
                    "summary": {
                        "num_statements": 1,
                        "covered_lines": 0,
                        "num_branches": 0,
                        "covered_branches": 0,
                    }
                },
            },
        }

    def test_real_complexity_and_coverage_including_unexecuted_source(self):
        result = report.collect(self.root, self.coverage)
        example, unused = result["files"]
        self.assertEqual(example["max_complexity"], 2)
        self.assertEqual(example["functions"][0]["name"], "choose")
        self.assertEqual(example["functions"][0]["line"], 1)
        self.assertGreater(example["maintainability_index"], 0)
        self.assertEqual(unused["covered_lines"], 0)
        self.assertEqual(unused["max_complexity"], 0)
        self.assertEqual(len(result["files"]), 2)

    def test_missing_coverage_fails_instead_of_hiding_source(self):
        del self.coverage["files"]["scripts/unused.py"]
        with self.assertRaises(KeyError):
            report.collect(self.root, self.coverage)

    def test_nested_functions_and_methods_are_measured(self):
        (self.root / "builder" / "example.py").write_text(
            "class Example:\n"
            "    def method(self, value):\n"
            "        def inner(x):\n"
            "            return 1 if x else 0\n"
            "        return inner(value)\n",
            encoding="utf-8",
        )
        functions = report.collect(self.root, self.coverage)["files"][0]["functions"]
        self.assertTrue(any(f["name"] == "Example.method" for f in functions))
        self.assertTrue(any(f["complexity"] == 2 and "inner" in f["name"] for f in functions))

    def test_percentages_distinguish_no_branches_from_no_coverage(self):
        self.assertEqual(report.percentage(0, 0), "n/a")
        self.assertEqual(report.percentage(0, 10), "0.0%")
        self.assertEqual(report.percentage(1, 4), "25.0%")

    def test_dashboard_escapes_source_names_and_links_to_details(self):
        result = report.collect(self.root, self.coverage)
        result["files"][0]["path"] = "builder/<script>.py"
        result["files"][0]["functions"][0]["name"] = "<unsafe>"
        page = report.dashboard(result)
        self.assertIn("builder/&lt;script&gt;.py", page)
        self.assertIn("&lt;unsafe&gt;", page)
        self.assertNotIn("<unsafe>", page)
        self.assertIn('href="coverage/index.html"', page)
        self.assertIn("60.0%", page)
        self.assertIn("50.0%", page)

    def test_cli_writes_consistent_json_html_and_summary(self):
        output = self.root / "reports"
        output.mkdir()
        (output / "coverage.json").write_text(json.dumps(self.coverage), encoding="utf-8")
        report.main(["--root", str(self.root), "--output", str(output)])
        metrics = json.loads((output / "metrics.json").read_text())
        self.assertEqual(metrics["totals"], self.coverage["totals"])
        self.assertIn("builder/example.py", (output / "summary.md").read_text())
        self.assertIn("Code quality metrics", (output / "index.html").read_text())


if __name__ == "__main__":
    unittest.main()
