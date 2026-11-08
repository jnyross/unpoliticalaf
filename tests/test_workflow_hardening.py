"""Pre-activation hardening of privileged workflows and the split CI pipeline."""

import os
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github/workflows"
# Disabled writers that intentionally push with the checkout token. They stay
# preserved and disabled; they are not hardened or activated here.
PUSHING_WORKFLOWS = frozenset({"fetch-sources.yml", "accuracy-check.yml"})
PRESERVED_DISABLED_WRITERS = PUSHING_WORKFLOWS | {"auto-merge.yml"}
PINNED_WORKFLOWS = frozenset(
    {"release.yml", "release-notes.yml", "deploy.yml", "live.yml", "pr-review.yml"}
)
PINNED_USE = re.compile(r"^[\w.-]+/[\w./-]+@[0-9a-f]{40} # v\d+(?:\.\d+){0,2}$")
LOCKED_ENTRY = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s\\;]+)")


def workflow_files():
    return sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml"))


def step_blocks(text, action):
    """Yield (first line, indented body) for each list-item step using an action."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = re.match(rf"^(\s*)- uses: {re.escape(action)}@", line)
        if not match:
            continue
        indent = len(match.group(1))
        body = []
        for following in lines[index + 1 :]:
            if following.strip() and len(following) - len(following.lstrip()) <= indent:
                break
            body.append(following)
        yield line, "\n".join(body)


def job_section(text, job):
    """Return one top-level job's text, up to the next job at the same indentation."""
    match = re.search(rf"^  {re.escape(job)}:\n(.*?)(?=^  [\w-]+:\n|\Z)", text, re.M | re.S)
    if not match:
        raise AssertionError(f"Missing job {job}")
    return match.group(1)


def run_lines(text):
    return [
        line.strip().removeprefix("- ").removeprefix("run: ")
        for line in text.splitlines()
        if re.match(r"^\s*(- )?run: ", line)
    ]


def requirement_pins(path, seen=None):
    seen = set() if seen is None else seen
    pins = {}
    if path in seen:
        return pins
    seen.add(path)
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("-r "):
            pins.update(requirement_pins((path.parent / line[3:].strip()).resolve(), seen))
            continue
        name, version = line.split("==")
        pins[normalize(name)] = version.strip()
    return pins


def normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def locked_entries(path):
    """Parse pip's hash-checking format into {name: (version, [hashes])}."""
    entries = {}
    current = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = LOCKED_ENTRY.match(line)
        if match:
            current = normalize(match.group(1))
            if current in entries:
                raise AssertionError(f"Duplicate locked entry {current}")
            entries[current] = (match.group(2), [])
        elif line.startswith("--hash=") and current:
            entries[current][1].append(line.removeprefix("--hash=").rstrip(" \\"))
        else:
            raise AssertionError(f"Unrecognised lock line: {raw!r}")
    return entries


class Credentials(unittest.TestCase):
    def test_every_non_pushing_checkout_drops_the_token(self):
        checked = 0
        for path in workflow_files():
            text = path.read_text(encoding="utf-8")
            for line, body in step_blocks(text, "actions/checkout"):
                if path.name in PUSHING_WORKFLOWS:
                    continue
                checked += 1
                with self.subTest(workflow=path.name, step=line.strip()):
                    self.assertRegex(body, r"(?m)^\s+persist-credentials: false$")
        self.assertGreater(checked, 15)

    def test_credential_exceptions_are_only_preserved_pushing_writers(self):
        for name in PUSHING_WORKFLOWS:
            text = (WORKFLOWS / name).read_text(encoding="utf-8")
            with self.subTest(workflow=name):
                self.assertIn("git push", text)
                self.assertIn("contents: write", text)
        pushing = {p.name for p in workflow_files() if "git push" in p.read_text(encoding="utf-8")}
        self.assertEqual(pushing, PUSHING_WORKFLOWS)


class Pinning(unittest.TestCase):
    def test_privileged_workflows_pin_every_external_action_to_a_commit(self):
        shas = {}
        for name in sorted(PINNED_WORKFLOWS):
            text = (WORKFLOWS / name).read_text(encoding="utf-8")
            uses = re.findall(r"^\s*(?:- )?uses: (.+)$", text, re.M)
            self.assertTrue(uses, name)
            for use in uses:
                if use.startswith("./"):
                    continue
                with self.subTest(workflow=name, use=use):
                    self.assertRegex(use, PINNED_USE)
                    action, sha = use.split(" ", 1)[0].split("@")
                    # One reviewed commit per action across every privileged workflow.
                    self.assertEqual(shas.setdefault(action, sha), sha)

    def test_every_writer_workflow_is_pinned_or_a_preserved_disabled_writer(self):
        for path in workflow_files():
            text = path.read_text(encoding="utf-8")
            if re.search(r"^\s+[\w-]+: write$", text, re.M):
                with self.subTest(workflow=path.name):
                    self.assertIn(path.name, PINNED_WORKFLOWS | PRESERVED_DISABLED_WRITERS)


class HashLockedInstall(unittest.TestCase):
    def test_release_lock_matches_setup_test_pins_and_hashes_every_entry(self):
        lock = locked_entries(ROOT / "requirements-release.txt")
        expected = requirement_pins((ROOT / "requirements-test.txt").resolve())
        self.assertTrue(expected)
        for name, version in expected.items():
            with self.subTest(package=name):
                self.assertIn(name, lock)
                self.assertEqual(lock[name][0], version)
        for name, (version, hashes) in lock.items():
            with self.subTest(locked=name):
                self.assertRegex(version, r"^[0-9][0-9A-Za-z.+!-]*$")
                self.assertTrue(hashes)
                for digest in hashes:
                    self.assertRegex(digest, r"^sha256:[0-9a-f]{64}$")

    def test_setup_release_requires_hashes_and_wheels(self):
        result = subprocess.run(
            ["make", "-n", "setup-release", "VENV=/tmp/release-venv"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        installs = [line for line in result.stdout.splitlines() if "pip install" in line]
        self.assertEqual(len(installs), 1, result.stdout)
        for flag in ("--require-hashes", "--only-binary=:all:", "-r requirements-release.txt"):
            self.assertIn(flag, installs[0])
        self.assertNotIn("--no-deps", installs[0])
        self.assertIn("/tmp/release-venv/bin/python -m pip check", result.stdout)

    def test_write_jobs_install_only_the_hash_locked_closure(self):
        release = (WORKFLOWS / "release.yml").read_text(encoding="utf-8")
        record = job_section((WORKFLOWS / "deploy.yml").read_text(encoding="utf-8"), "record")
        for name, text in (("release", release), ("record", record)):
            with self.subTest(job=name):
                commands = run_lines(text)
                setups = [c for c in commands if c.startswith("make setup")]
                self.assertEqual(setups, ["make setup-release"])
                self.assertFalse([c for c in commands if "pip " in c])
                self.assertNotIn("cache: pip", text)


class ReceiptEnvironment(unittest.TestCase):
    def test_receipt_jobs_never_declare_a_github_environment(self):
        # A job-level environment would make Actions write its own deployment records.
        for name in ("deploy.yml", "live.yml", "release.yml"):
            text = (WORKFLOWS / name).read_text(encoding="utf-8")
            with self.subTest(workflow=name):
                self.assertNotRegex(text, r"(?m)^\s+environment:")


class SplitPipeline(unittest.TestCase):
    def setUp(self):
        self.text = (WORKFLOWS / "check.yml").read_text(encoding="utf-8")

    def test_each_full_suite_runs_once_in_its_own_parallel_job(self):
        commands = run_lines(self.text)
        for command in (
            "make test-stability",
            "make verify-coverage",
            "make quality-checks",
            "make -f quality/Makefile tooling-tests",
            "make benchmark",
        ):
            with self.subTest(command=command):
                self.assertEqual(commands.count(command), 1)
        self.assertNotIn("make quality", commands)
        stability = job_section(self.text, "stability")
        coverage = job_section(self.text, "coverage")
        self.assertIn("run: make test-stability", stability)
        self.assertIn("run: make verify-coverage", coverage)
        for job in (stability, coverage, job_section(self.text, "quality")):
            # The development set is the quality job's original, larger population.
            self.assertIn("run: make setup-dev", job)
            self.assertIn("npm ci --ignore-scripts", job)
        for job in (stability, coverage):
            # The longest suites start at once instead of waiting for another job.
            self.assertNotIn("needs:", job.split("steps:", 1)[0])

    def test_required_aggregates_accept_only_successful_dependencies(self):
        for job, needs in (
            ("check", ("flag_configurations", "stability", "coverage")),
            ("quality", ("stability", "coverage")),
        ):
            section = job_section(self.text, job)
            self.assertIn("if: always()", section)
            self.assertNotIn("continue-on-error", section)
            declared = re.search(r"needs: \[([^\]]+)\]", section)
            self.assertIsNotNone(declared, job)
            self.assertEqual(tuple(n.strip() for n in declared.group(1).split(",")), needs)
            command = next(c for c in run_lines(section) if c.startswith('test "$'))
            variables = re.findall(r'"\$(\w+)"', command)
            self.assertEqual(len(variables), len(needs))
            for variable, need in zip(variables, needs):
                self.assertIn(f"{variable}: ${{{{ needs.{need}.result }}}}", section)
            for failing in variables:
                for result in ("failure", "cancelled", "skipped", ""):
                    environment = {v: "success" for v in variables}
                    environment[failing] = result
                    with self.subTest(job=job, variable=failing, result=result):
                        checked = subprocess.run(
                            ["sh", "-c", command], env={**os.environ, **environment}
                        )
                        self.assertNotEqual(checked.returncode, 0)
            passed = subprocess.run(
                ["sh", "-c", command], env={**os.environ, **{v: "success" for v in variables}}
            )
            self.assertEqual(passed.returncode, 0, job)

    def test_local_quality_is_exactly_the_ci_components(self):
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertRegex(
            makefile,
            r"(?m)^quality: quality-checks test-stability\n\t\$\(MAKE\) -f quality/Makefile metrics\n",
        )
        checks = re.search(r"(?m)^quality-checks: (.+)$", makefile).group(1).split()
        self.assertEqual(
            checks,
            [
                "lint",
                "format-check",
                "typecheck",
                "check-deps",
                "complexity",
                "duplication",
                "tracing",
                "delivery",
                "architecture",
            ],
        )
        metrics = subprocess.run(
            ["make", "-n", "-f", "quality/Makefile", "metrics"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        coverage = subprocess.run(
            ["make", "-n", "verify-coverage"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout
        tooling = subprocess.run(
            ["make", "-n", "-f", "quality/Makefile", "tooling-tests"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        # metrics = tooling-tests + the same single measurement as verify-coverage.
        self.assertEqual(metrics.splitlines(), tooling.splitlines() + coverage.splitlines())

    def test_long_jobs_keep_existing_timeouts_and_retain_artifacts(self):
        for job in ("stability", "coverage", "check", "quality"):
            with self.subTest(job=job):
                self.assertIn("timeout-minutes: 60", job_section(self.text, job))
        stability = job_section(self.text, "stability")
        coverage = job_section(self.text, "coverage")
        self.assertIn(
            "name: test-results-${{ github.run_id }}-${{ github.run_attempt }}", stability
        )
        self.assertIn(
            "name: verification-coverage-${{ github.run_id }}-${{ github.run_attempt }}", coverage
        )
        self.assertIn("if-no-files-found: error", coverage)


if __name__ == "__main__":
    unittest.main()
