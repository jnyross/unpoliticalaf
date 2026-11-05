"""Run explicitly after installing requirements-review.txt; never needs GitHub access."""
from pathlib import Path
import tempfile
import unittest

from scripts import review_pr as review


class RealAnalyzerTests(unittest.TestCase):
    def test_real_tools_find_correctness_and_security_without_executing_code(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            sentinel = directory / "must-not-exist"
            source = (
                "import pickle\nfrom pathlib import Path\n"
                f"Path({str(sentinel)!r}).write_text('executed')\n"
                "result = undefined_review_name  # noqa\n"
                "value = pickle.loads(b'not-a-pickle')  # nosec\n"
            )
            (directory / "0.py").write_text(source)
            findings = review.analyze(directory, {"0.py": ("builder/fixture.py", {3, 4, 5})})
            self.assertTrue(any("F821" in f[2] and f[1] == 4 for f in findings))
            self.assertTrue(any("B301" in f[2] and f[1] == 5 for f in findings))
            self.assertFalse(sentinel.exists(), "PR code must never execute")
            old_only = review.analyze(directory, {"0.py": ("builder/fixture.py", {2})})
            self.assertEqual(old_only, [])

    def test_real_tools_accept_clean_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "0.py").write_text("def double(value):\n    return value * 2\n")
            self.assertEqual(review.analyze(directory, {"0.py": ("clean.py", {1, 2})}), [])

    def test_real_tools_do_not_claim_syntax_errors_are_clean(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "0.py").write_text("def broken(:\n")
            with self.assertRaises(review.ReviewError):
                review.analyze(directory, {"0.py": ("broken.py", {1})})


if __name__ == "__main__":
    unittest.main()
