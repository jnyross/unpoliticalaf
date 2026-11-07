"""Hook policy and real pre-commit execution in disposable Git metadata only."""

import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HAS_PRE_COMMIT = importlib.util.find_spec("pre_commit") is not None


def record_fixture_commit(root):
    """Write deterministic test data, without configuring/overriding a Git identity."""
    tree = subprocess.check_output(["git", "write-tree"], cwd=root, text=True).strip()
    # The sandbox has no author configuration. This serialized fixture is not
    # an authored project commit and must never be published.
    commit = (
        f"tree {tree}\n"
        "author Hook fixture <hook@example.invalid> 0 +0000\n"
        "committer Hook fixture <hook@example.invalid> 0 +0000\n\n"
        "Disposable hook fixture\n"
    )
    revision = subprocess.check_output(
        ["git", "hash-object", "-t", "commit", "-w", "--stdin"],
        cwd=root,
        input=commit,
        text=True,
    ).strip()
    subprocess.run(["git", "update-ref", "HEAD", revision], cwd=root, check=True)


class HookPolicy(unittest.TestCase):
    def test_checked_in_config_exists(self):
        self.assertTrue((ROOT / ".pre-commit-config.yaml").is_file())

    def test_developer_pin_and_explicit_reinstallation(self):
        self.assertIn("pre-commit==4.3.0", (ROOT / "requirements-dev.txt").read_text())
        result = subprocess.run(["make", "-n", "hooks"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(".venv/bin/python -m pre_commit install", result.stdout)
        for target in ("setup", "setup-test", "setup-quality"):
            result = subprocess.run(
                ["make", "-n", target], cwd=ROOT, capture_output=True, text=True, check=True
            )
            self.assertNotIn("pre_commit install", result.stdout)

    @unittest.skipUnless(HAS_PRE_COMMIT, "development tool; run make setup-dev")
    def test_whole_project_gate_has_no_path_or_type_filters(self):
        from pre_commit.clientlib import load_config

        config = load_config(str(ROOT / ".pre-commit-config.yaml"))
        self.assertEqual(config["default_stages"], ["pre-commit"])
        self.assertEqual(len(config["repos"]), 1)
        repository = config["repos"][0]
        self.assertEqual(repository["repo"], "local")
        self.assertEqual(len(repository["hooks"]), 1)
        hook = repository["hooks"][0]
        self.assertEqual(hook["entry"], "make verify")
        self.assertEqual(hook["language"], "system")
        self.assertTrue(hook["always_run"])
        self.assertFalse(hook["pass_filenames"])
        self.assertEqual(hook["files"], "")
        self.assertEqual(hook["exclude"], "^$")
        self.assertEqual(hook["types"], ["file"])


@unittest.skipUnless(HAS_PRE_COMMIT, "development tool; run make setup-dev")
class HookExecution(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.run_command("git", "init", "-q", check=True)
        shutil.copyfile(ROOT / ".pre-commit-config.yaml", self.root / ".pre-commit-config.yaml")
        # This tiny Makefile characterizes routing and fail-closed status, not
        # the full site's verification. Full-site fixtures run separately in Boat.
        (self.root / "Makefile").write_text(
            ".PHONY: verify build check test\n"
            "verify: build check test\n"
            "build check test:\n"
            "\t@echo $@ >> trace\n"
            "\t@test ! -e fail-$@\n"
            "\t@test -f input.txt\n"
            "\t@if test -f notes.md; then ! grep -q BROKEN notes.md; fi\n"
        )
        (self.root / "input.txt").write_text("Required input.\n")
        (self.root / "notes.md").write_text("Documentation fixture.\n")
        self.run_command("git", "add", ".", check=True)
        record_fixture_commit(self.root)
        self.run_command(sys.executable, "-m", "pre_commit", "install", check=True)
        self.hook = str(self.root / ".git/hooks/pre-commit")

    def run_command(self, *arguments, check=False):
        return subprocess.run(arguments, cwd=self.root, capture_output=True, text=True, check=check)

    def trace(self):
        return (self.root / "trace").read_text().splitlines()

    def test_actual_installed_hook_runs_build_check_and_test_once(self):
        result = self.run_command(self.hook)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.trace(), ["build", "check", "test"])

    def test_docs_only_selection_runs_full_gate_without_filename_arguments(self):
        (self.root / "notes.md").write_text("Updated documentation.\n")
        self.run_command("git", "add", "notes.md", check=True)
        staged = self.run_command("git", "diff", "--cached", "--name-only", check=True)
        self.assertEqual(staged.stdout.splitlines(), ["notes.md"])
        result = self.run_command(self.hook)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.trace(), ["build", "check", "test"])

    def test_empty_selection_still_runs_full_gate(self):
        result = self.run_command(sys.executable, "-m", "pre_commit", "run", "--files")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.trace(), ["build", "check", "test"])

    def test_deletion_only_selection_runs_and_missing_input_blocks(self):
        self.run_command("git", "rm", "input.txt", check=True)
        staged = self.run_command("git", "diff", "--cached", "--name-status", check=True)
        self.assertEqual(staged.stdout.strip(), "D\tinput.txt")
        result = self.run_command(self.hook)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.trace(), ["build"])
        self.assertIn("exit code: 2", result.stdout)
        self.run_command("git", "restore", "--staged", "--worktree", "input.txt", check=True)
        repaired = self.run_command(self.hook)
        self.assertEqual(repaired.returncode, 0, repaired.stdout + repaired.stderr)
        self.assertEqual(self.trace(), ["build", "build", "check", "test"])

    def test_unstaged_docs_repair_is_stashed_until_legitimately_restaged(self):
        notes = self.root / "notes.md"
        notes.write_text("BROKEN\n")
        self.run_command("git", "add", "notes.md", check=True)
        broken = self.run_command(self.hook)
        self.assertNotEqual(broken.returncode, 0)
        notes.write_text("Repaired documentation.\n")
        unstaged = self.run_command(self.hook)
        self.assertNotEqual(unstaged.returncode, 0)
        self.assertIn("Unstaged files detected", unstaged.stdout + unstaged.stderr)
        self.assertIn("Repaired documentation.", notes.read_text())
        self.run_command("git", "add", "notes.md", check=True)
        repaired = self.run_command(self.hook)
        self.assertEqual(repaired.returncode, 0, repaired.stdout + repaired.stderr)
        self.assertEqual(self.trace(), ["build", "build", "build", "check", "test"])

    def test_each_verification_failure_blocks_and_stops_later_phases(self):
        for index, phase in enumerate(("build", "check", "test")):
            with self.subTest(phase=phase):
                failure = self.root / f"fail-{phase}"
                failure.touch()
                result = self.run_command(self.hook)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("Failed", result.stdout)
                self.assertIn("exit code: 2", result.stdout)
                self.assertEqual(self.trace(), ["build", "check", "test"][: index + 1])
                failure.unlink()
                (self.root / "trace").unlink()
                # A separate legitimate rerun must actually execute all phases.
                repaired = self.run_command(self.hook)
                self.assertEqual(repaired.returncode, 0, repaired.stdout + repaired.stderr)
                self.assertEqual(self.trace(), ["build", "check", "test"])
                (self.root / "trace").unlink()


if __name__ == "__main__":
    unittest.main()
