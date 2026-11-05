"""AGENTS.md freshness checks catch renamed, missing and escaping references."""
import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import check_agents


class AgentsReferences(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        (self.root / "docs").mkdir()
        (self.root / "docs/product-spec.md").write_text("# Product\n", encoding="utf-8")
        (self.root / "Makefile").write_text("check:\n\ttrue\n", encoding="utf-8")
        self.write_agents("Read `docs/product-spec.md` and `docs/`.\n")

    def write_agents(self, text):
        (self.root / "AGENTS.md").write_text(text, encoding="utf-8")

    def test_current_repository_references_exist(self):
        count, problems = check_agents.check(check_agents.ROOT)
        self.assertGreater(count, 0)
        self.assertEqual(problems, [])

    def test_literal_file_and_directory_references_pass(self):
        self.assertEqual(check_agents.check(self.root), (2, []))

    def test_renamed_file_fails_with_document_line(self):
        (self.root / "docs/product-spec.md").rename(self.root / "docs/renamed.md")
        count, problems = check_agents.check(self.root)
        self.assertEqual(count, 2)
        self.assertEqual(problems, [
            "AGENTS.md:1: docs/product-spec.md: referenced path does not exist"
        ])

    def test_missing_directory_fails(self):
        self.write_agents("Use `data/`.\n")
        self.assertIn("data/: referenced path does not exist", check_agents.check(self.root)[1][0])

    def test_directory_reference_cannot_be_replaced_with_file(self):
        self.write_agents("Read `Makefile/`.\n")
        self.assertIn("expected a directory", check_agents.check(self.root)[1][0])

    def test_inline_links_and_reference_definitions_are_checked(self):
        self.write_agents(
            '[Spec](docs/product-spec.md "Product")\n'
            "[missing][guide]\n\n[guide]: docs/missing.md\n"
        )
        count, problems = check_agents.check(self.root)
        self.assertEqual(count, 2)
        self.assertEqual(problems, [
            "AGENTS.md:4: docs/missing.md: referenced path does not exist"
        ])

    def test_link_fragment_and_query_do_not_become_part_of_filename(self):
        self.write_agents("[Spec](docs/product-spec.md?view=1#product)\n")
        self.assertEqual(check_agents.check(self.root), (1, []))

    def test_inline_links_with_each_markdown_title_style_pass(self):
        for title in ('"Guide title"', "'Guide title'", "(Guide title)"):
            with self.subTest(title=title):
                self.write_agents(f"[Spec](docs/product-spec.md {title})\n")
                self.assertEqual(check_agents.check(self.root), (1, []))

    def test_broken_inline_links_with_each_title_style_fail(self):
        for title in ('"Guide title"', "'Guide title'", "(Guide title)"):
            with self.subTest(title=title):
                self.write_agents(f"`docs/`\n[Missing](docs/missing.md {title})\n")
                self.assertEqual(check_agents.check(self.root), (2, [
                    "AGENTS.md:2: docs/missing.md: referenced path does not exist"
                ]))

    def test_angle_link_with_encoded_spaces(self):
        (self.root / "docs/other spec.md").write_text("# Other\n", encoding="utf-8")
        self.write_agents("[Spec](<docs/other%20spec.md>)\n")
        self.assertEqual(check_agents.check(self.root), (1, []))

    def test_bare_filenames_are_checked(self):
        self.write_agents("Use `Makefile`, `README.md`.\n")
        self.assertEqual(check_agents.check(self.root)[1], [
            "AGENTS.md:1: README.md: referenced path does not exist"
        ])

    def test_all_broken_references_are_reported(self):
        self.write_agents("`missing.md`\n`absent/`\n")
        self.assertEqual(len(check_agents.check(self.root)[1]), 2)

    def test_parent_path_cannot_escape_checkout(self):
        self.write_agents("Read `../outside.md`.\n")
        self.assertIn("leaves the repository", check_agents.check(self.root)[1][0])

    def test_symlink_cannot_escape_checkout(self):
        (self.root / "external.md").symlink_to(self.root.parent)
        self.write_agents("Read `external.md`.\n")
        self.assertIn("leaves the repository", check_agents.check(self.root)[1][0])

    def test_external_operator_paths_urls_and_commands_are_out_of_scope(self):
        self.write_agents(
            "`https://example.invalid/no-network` `/operator/guide.md` "
            "`~/private.md` `make verify` `31/32`\n"
            "[External](https://example.invalid/) [Email](mailto:owner@example.invalid)\n"
            "`docs/`\n"
        )
        self.assertEqual(list(check_agents.references("`make verify` `96/100` `9.5/10`")), [])
        self.assertEqual(check_agents.check(self.root), (1, []))

    def test_missing_empty_or_reference_free_instructions_fail(self):
        (self.root / "AGENTS.md").unlink()
        self.assertIn("cannot read", check_agents.check(self.root)[1][0])
        self.write_agents(" \n")
        self.assertIn("empty", check_agents.check(self.root)[1][0])
        self.write_agents("# Instructions\nWork carefully.\n")
        self.assertIn("no repository references", check_agents.check(self.root)[1][0])

    def test_main_returns_failure_and_prints_actionable_diagnostic(self):
        self.write_agents("Read `missing.md`.\n")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            self.assertEqual(check_agents.main(self.root), 1)
        self.assertIn("AGENTS.md:1: missing.md", stderr.getvalue())

    def test_cli_works_from_outside_checkout(self):
        result = subprocess.run(
            [sys.executable, str(check_agents.ROOT / "scripts/check_agents.py")],
            cwd=self.root, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("repository references", result.stdout)


if __name__ == "__main__":
    unittest.main()
