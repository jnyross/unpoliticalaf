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
DELIVERY_GATE = "vars.REVIEWED_PRODUCTION_DELIVERY == 'true'"
REVIEW_ANALYZERS = {"ruff": "0.14.3", "bandit": "1.8.6"}
# Python package managers by name (pip, pip3.12, python -m pip, uv, pipx, pipenv,
# poetry, pdm, hatch, rye, pixi, conda, mamba, easy_install), their setup actions
# and setup-python caches. A name-based check: a script that installs indirectly
# is caught only through the make setup assertions.
PACKAGE_INSTALLER = re.compile(
    r"(?<![\w-])(?:pip(?:\d+(?:\.\d+)*)?|pipx|pipenv|uvx?|poetry|pdm|hatch|rye|pixi"
    r"|(?:micro)?mamba|conda|easy_install)(?![\w-])"
    r"|-m\s*pip(?![\w-])"
    r"|\bsetup-(?:uv|pdm|poetry|pixi|micromamba|miniconda)\b"
)
# [^\n] rather than ".", because job_section matches with re.S.
JOB_KEY = r"^  ([\w-]+):[ \t]*(?:#[^\n]*)?\n"
PERMISSION_SCOPE = re.compile(r"^([\w-]+): (read|write|none)$")
MAKE_SETUP = re.compile(r"\bmake\b.*\bsetup(?:-[\w-]+)?\b")


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
    match = re.search(
        rf"^  {re.escape(job)}:[ \t]*(?:#[^\n]*)?\n(.*?)(?={JOB_KEY}|\Z)", text, re.M | re.S
    )
    if not match:
        raise AssertionError(f"Missing job {job}")
    return match.group(1)


def jobs(text):
    """Return {job id: section} for the top-level jobs mapping only."""
    body = text.split("\njobs:\n", 1)[1]
    # Fail on any job key or trailing top-level key these text checks cannot read.
    for line in re.findall(r"(?m)^ {0,2}\S.*$", body):
        if not line.lstrip().startswith("#") and not re.fullmatch(JOB_KEY[1:-2], line):
            raise AssertionError(f"Unparsed line under jobs: {line!r}")
    names = re.findall(rf"(?m){JOB_KEY}", body)
    return {name: job_section("jobs:\n" + body, name) for name in names}


def job_header(section):
    """Job keys before its steps (or the whole section for a reusable call)."""
    return section.split("\n    steps:", 1)[0]


def permission_blocks(text, indent):
    """Return each permissions value declared at exactly this indentation."""
    pad = " " * indent
    blocks = []
    # Blank lines may sit inside a YAML mapping without ending it.
    for match in re.finditer(rf"(?m)^{pad}permissions:(.*)\n((?:(?:{pad}  .*)?\n)*)", text):
        blocks.append((match.group(1).strip() + "\n" + match.group(2)).strip())
    return blocks


def write_scopes(block):
    """Return a permissions value's write scopes, failing on unreadable forms."""
    lines = [re.sub(r"(?:^|\s+)#.*$", "", line).strip() for line in block.splitlines()]
    lines = [line for line in lines if line]
    if lines in (["write-all"], ["read-all"], ["{}"]):
        return {"write-all"} if lines == ["write-all"] else set()
    scopes = set()
    for line in lines:
        match = PERMISSION_SCOPE.match(line)
        if not match:
            raise AssertionError(f"Unparsed permissions line: {line!r}")
        if match.group(2) == "write":
            scopes.add(match.group(1))
    return scopes


def own_permission_blocks(section):
    # Steps nest at six or more spaces, so a four-space key belongs to the job,
    # even when written after steps.
    return permission_blocks(section + "\n", 4)


def effective_write_scopes(workflow, section):
    """A job's own permissions replace the workflow's; otherwise it inherits them."""
    own = own_permission_blocks(section)
    blocks = own or permission_blocks(workflow, 0)
    return set().union(*(write_scopes(b) for b in blocks)) if blocks else {"undeclared"}


def job_condition(section):
    """Return a job's if expression, joining a folded block scalar."""
    header = job_header(section) + "\n"
    match = re.search(r"(?m)^    if: >-\n((?:      .*\n)+)", header)
    if match:
        return " ".join(line.strip() for line in match.group(1).splitlines())
    match = re.search(r"(?m)^    if: (.+)$", header)
    return match.group(1).strip() if match else ""


def assert_delivery_gated(case, condition):
    """The reviewed delivery variable must be a required conjunct of the job guard."""
    expression = condition.strip()
    if expression.startswith("${{") and expression.endswith("}}"):
        expression = expression[3:-2].strip()
    case.assertNotIn("||", expression)
    case.assertNotRegex(expression, r"!(?!=)")
    case.assertIn(DELIVERY_GATE, [part.strip() for part in expression.split("&&")])


def executable_lines(section):
    lines = section.splitlines()
    code = "\n".join(line for line in lines if not line.strip().startswith("#"))
    # Comments are dropped first because they never continue; joining the rest
    # keeps a split "python -m \ pip" visible.
    return re.sub(r"\\\n\s*", " ", code).splitlines()


def make_dry_run(*arguments):
    # An outer make (make test) exports MAKELEVEL, which adds directory banners.
    environment = {
        k: v for k, v in os.environ.items() if k not in {"MAKEFLAGS", "MAKELEVEL", "MFLAGS"}
    }
    return subprocess.run(
        ["make", "--no-print-directory", "-n", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        env=environment,
    ).stdout


def setup_commands(text):
    """Every make setup invocation on an executable line, inside run blocks too."""
    return [
        line.strip().removeprefix("- ").removeprefix("run: ").strip()
        for line in executable_lines(text)
        if MAKE_SETUP.search(line)
    ]


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
            if path.name not in PUSHING_WORKFLOWS:
                # Catches checkouts written in a form step_blocks does not parse.
                with self.subTest(workflow=path.name):
                    self.assertEqual(
                        len(re.findall(r"uses: actions/checkout@", text)),
                        len(re.findall(r"(?m)^\s+persist-credentials: false$", text)),
                    )
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
            blocks = permission_blocks(text, 0)
            blocks += [b for s in jobs(text).values() for b in own_permission_blocks(s)]
            if set().union(*(write_scopes(b) for b in blocks)):
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
        stdout = make_dry_run("setup-release", "VENV=/tmp/release-venv")
        installs = [line for line in stdout.splitlines() if "pip install" in line]
        self.assertEqual(len(installs), 1, stdout)
        for flag in ("--require-hashes", "--only-binary=:all:", "-r requirements-release.txt"):
            self.assertIn(flag, installs[0])
        self.assertNotIn("--no-deps", installs[0])
        self.assertIn("/tmp/release-venv/bin/python -m pip check", stdout)
        # The lock has no 3.10 backports such as tomli or exceptiongroup.
        self.assertIn("sys.version_info[:2] == (3, 12)", stdout)

    def test_write_jobs_install_only_the_hash_locked_closure(self):
        release = (WORKFLOWS / "release.yml").read_text(encoding="utf-8")
        record = job_section((WORKFLOWS / "deploy.yml").read_text(encoding="utf-8"), "record")
        for name, text in (("release", release), ("record", record)):
            with self.subTest(job=name):
                self.assertEqual(setup_commands(text), ["make setup-release"])
                for line in executable_lines(text):
                    self.assertNotRegex(line, PACKAGE_INSTALLER)

    def test_package_installer_detection_covers_every_python_installer(self):
        for line in (
            "run: pip install -q -r requirements.txt",
            "run: pip3 install ruff",
            "run: pip3.12 install ruff",
            "run: python3 -m pip install ruff",
            "run: python -mpip install ruff",
            "run: .venv/bin/python -m pip install -r requirements-test.txt",
            "run: uv pip install -r requirements.txt",
            "run: uv sync --frozen",
            "run: uvx ruff check",
            "run: pipx install bandit",
            "run: poetry install",
            "run: pdm install",
            "run: pipenv sync",
            "run: hatch env create",
            "run: rye sync",
            "run: pixi install",
            "run: conda install ruff",
            "run: micromamba install ruff",
            "- uses: astral-sh/setup-uv@0000000000000000000000000000000000000000 # v6",
            "- uses: conda-incubator/setup-miniconda@v3",
            "cache: pip",
            "cache: pipenv",
            "- run: make setup && pip install x",
            executable_lines("        run: python -m \\\n          pip install x\n")[0],
        ):
            with self.subTest(line=line):
                self.assertRegex(line, PACKAGE_INSTALLER)
        for line in (
            "run: make setup-release",
            "run: make production-verify",
            "run: python -I -S scripts/review_pr.py",
            "run: docker build --file config/review-analyzers.Dockerfile .",
            "cp requirements-review.txt build/",
            "run: bash scripts/publish_release.sh",
            "- uses: actions/setup-python@0000000000000000000000000000000000000000 # v6",
            "name: Pipeline summary",
            "run: echo pipeline",
        ):
            with self.subTest(line=line):
                self.assertNotRegex(line, PACKAGE_INSTALLER)

    def test_every_privileged_job_installs_only_the_hash_locked_closure(self):
        privileged = set()
        for path in workflow_files():
            if path.name in PRESERVED_DISABLED_WRITERS:
                continue
            text = path.read_text(encoding="utf-8")
            for job, section in jobs(text).items():
                scopes = effective_write_scopes(text, section)
                if not scopes:
                    continue
                privileged.add(f"{path.name}:{job}")
                with self.subTest(workflow=path.name, job=job):
                    if re.search(r"(?m)^    uses: ", section):
                        # Reusable calls are checked through their called workflow's jobs.
                        self.assertEqual(path.name, "live.yml")
                        continue
                    self.assertNotIn("undeclared", scopes)
                    for line in executable_lines(section):
                        self.assertNotRegex(line, PACKAGE_INSTALLER)
                    self.assertIn(setup_commands(section), ([], ["make setup-release"]))
        self.assertEqual(
            privileged,
            {
                "deploy.yml:record",
                "live.yml:live",
                "pr-review.yml:review",
                "release-notes.yml:release",
                "release.yml:release",
            },
        )

    def test_called_receipt_workflow_scopes_write_tokens_to_locked_jobs(self):
        # live.yml calls deploy.yml with deployments: write, so every called job
        # must narrow its own token; only hash-locked jobs may keep a write scope.
        caller = (WORKFLOWS / "live.yml").read_text(encoding="utf-8")
        self.assertIn("deployments: write", caller)
        self.assertIn("uses: ./.github/workflows/deploy.yml", caller)
        text = (WORKFLOWS / "deploy.yml").read_text(encoding="utf-8")
        called = jobs(text)
        self.assertEqual(list(called), ["live", "record"])
        for job, section in called.items():
            header = job_header(section)
            with self.subTest(job=job):
                # A second permissions key could silently replace the narrowed first one.
                self.assertEqual(len(re.findall(r"(?m)^\s*permissions:", section)), 1)
                self.assertRegex(header, r"(?m)^    permissions:\n      contents: read$")
                if re.search(r"(?m)^      [\w-]+: write$", header):
                    self.assertIn("run: make setup-release", section)
                else:
                    self.assertNotIn("setup-release", section)


class Callers(unittest.TestCase):
    def test_live_is_the_only_caller_of_the_receipt_workflow(self):
        callers = {}
        for path in workflow_files():
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"(?m)^\s*(?:- )?uses:\s*['\"]?(\S*?\.ya?ml)\b", text):
                callers.setdefault(target.rsplit("/", 1)[-1], set()).add(path.name)
        self.assertEqual(callers, {"deploy.yml": {"live.yml"}})
        live = jobs((WORKFLOWS / "live.yml").read_text(encoding="utf-8"))
        self.assertEqual(list(live), ["live"])
        self.assertEqual(live["live"].strip(), "uses: ./.github/workflows/deploy.yml")

    def test_called_workflows_declare_every_job_token(self):
        # A called job without its own block would inherit the caller's write scopes.
        text = (WORKFLOWS / "deploy.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_call:", text)
        for job, section in jobs(text).items():
            with self.subTest(job=job):
                self.assertEqual(len(own_permission_blocks(section)), 1)


class PermissionBlocks(unittest.TestCase):
    def test_every_workflow_and_job_declares_at_most_one_permissions_block(self):
        for path in workflow_files():
            text = path.read_text(encoding="utf-8")
            with self.subTest(workflow=path.name):
                self.assertEqual(len(permission_blocks(text, 0)), 1)
                # Workflow permissions appear before jobs, never repeated afterwards.
                self.assertNotRegex(text.split("\njobs:\n", 1)[1], r"(?m)^permissions:")
            for job, section in jobs(text).items():
                with self.subTest(workflow=path.name, job=job):
                    self.assertLessEqual(len(re.findall(r"(?m)^    permissions:", section)), 1)
                    self.assertNotRegex(section, r"(?m)^(?: {1,3}| {5,})permissions:")

    def test_permission_parsing_detects_duplicates_and_inheritance(self):
        workflow = (
            "permissions:\n  contents: read\n  deployments: write\n\njobs:\n"
            "  inherits:\n    runs-on: ubuntu-24.04\n    steps:\n      - run: true\n"
            "  narrowed:\n    permissions:\n      contents: read\n    steps:\n      - run: true\n"
            "  doubled:\n    permissions:\n      contents: read\n"
            "    permissions:\n      contents: write\n    steps:\n      - run: true\n"
        )
        parsed = jobs(workflow)
        self.assertEqual(effective_write_scopes(workflow, parsed["inherits"]), {"deployments"})
        self.assertEqual(effective_write_scopes(workflow, parsed["narrowed"]), set())
        self.assertEqual(effective_write_scopes(workflow, parsed["doubled"]), {"contents"})
        self.assertEqual(len(own_permission_blocks(parsed["doubled"])), 2)
        self.assertEqual(write_scopes("write-all"), {"write-all"})
        self.assertEqual(write_scopes("read-all"), set())
        self.assertEqual(write_scopes("contents: read  # pinned\nstatuses: write"), {"statuses"})
        spaced = "permissions:\n  contents: read\n\n  deployments: write\njobs:\n"
        self.assertEqual(write_scopes(permission_blocks(spaced, 0)[0]), {"deployments"})
        commented = "      # note \\\n      pip install x\n"
        self.assertEqual(executable_lines(commented), ["      pip install x"])

    def test_permission_parsing_fails_on_forms_it_cannot_read(self):
        late = (
            "permissions:\n  contents: read\n\njobs:\n"
            "  late:  # permissions after steps\n    steps:\n      - run: true\n"
            "    permissions:\n      deployments: write\n"
        )
        self.assertEqual(effective_write_scopes(late, jobs(late)["late"]), {"deployments"})
        for block in ("{ contents: write }", "contents: 'write'", "contents: write-all"):
            with self.subTest(block=block), self.assertRaises(AssertionError):
                write_scopes(block)
        for workflow in (
            "permissions: {}\njobs:\n  odd job:\n    steps:\n      - run: true\n",
            "permissions: {}\njobs:\n  ok:\n    steps:\n      - run: true\nenv:\n  A: b\n",
        ):
            with self.subTest(workflow=workflow), self.assertRaises(AssertionError):
                jobs(workflow)

    def test_setup_commands_include_run_blocks(self):
        section = "    steps:\n      - run: |\n          make setup\n          true\n"
        self.assertEqual(setup_commands(section), ["make setup"])
        self.assertEqual(setup_commands("      # make setup\n      - run: make test\n"), [])


class ReviewAnalyzerLock(unittest.TestCase):
    def test_review_lock_pins_the_analyzers_and_hashes_every_entry(self):
        lock = locked_entries(ROOT / "requirements-review.txt")
        for name, version in REVIEW_ANALYZERS.items():
            with self.subTest(analyzer=name):
                self.assertEqual(lock[name][0], version)
        self.assertGreater(len(lock), len(REVIEW_ANALYZERS))
        for name, (version, hashes) in lock.items():
            with self.subTest(locked=name):
                self.assertRegex(version, r"^[0-9][0-9A-Za-z.+!-]*$")
                self.assertTrue(hashes)
                for digest in hashes:
                    self.assertRegex(digest, r"^sha256:[0-9a-f]{64}$")
        # The analyzers stay separate from project dependencies and their pins.
        self.assertNotIn("pytest", lock)
        self.assertNotIn("openpyxl", lock)

    def test_analyzer_image_installs_only_hash_verified_wheels(self):
        dockerfile = (ROOT / "config/review-analyzers.Dockerfile").read_text(encoding="utf-8")
        instructions = [
            line.strip()
            for line in dockerfile.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        self.assertEqual(
            [line for line in instructions if line.startswith("COPY ")],
            ["COPY requirements-review.txt /tmp/requirements-review.txt"],
        )
        runs = [line for line in instructions if line.startswith("RUN ")]
        self.assertEqual(len(runs), 1, runs)
        commands = [part.strip() for part in runs[0].removeprefix("RUN ").split("&&")]
        self.assertEqual(len(commands), 2, commands)
        install, check = commands
        self.assertTrue(install.startswith("python -m pip install "), install)
        for flag in (
            "--require-hashes",
            "--only-binary=:all:",
            "--no-cache-dir",
            "-r /tmp/requirements-review.txt",
        ):
            self.assertIn(flag, install)
        self.assertEqual(check, "python -m pip check")
        workflow = (WORKFLOWS / "pr-review.yml").read_text(encoding="utf-8")
        build = job_section(workflow, "review")
        # The build context holds only the hash lock, never repository or PR files.
        self.assertEqual(
            re.findall(r"(?m)^\s+cp .+$", build),
            ['          cp requirements-review.txt "$RUNNER_TEMP/review-build/"'],
        )


class DeliveryGate(unittest.TestCase):
    def test_every_delivery_writer_job_requires_the_reviewed_variable(self):
        for name, job in (
            ("release.yml", "release"),
            ("deploy.yml", "record"),
            ("release-notes.yml", "release"),
        ):
            section = job_section((WORKFLOWS / name).read_text(encoding="utf-8"), job)
            with self.subTest(workflow=name, job=job):
                assert_delivery_gated(self, job_condition(section))

    def test_release_notes_are_a_no_op_without_the_delivery_variable(self):
        text = (WORKFLOWS / "release-notes.yml").read_text(encoding="utf-8")
        parsed = jobs(text)
        # One gated job owns every step; nothing runs at workflow level.
        self.assertEqual(list(parsed), ["release"])
        self.assertEqual(job_condition(parsed["release"]), DELIVERY_GATE)
        self.assertEqual(text.count("steps:"), 1)
        for condition in (
            "",
            "always()",
            f"{DELIVERY_GATE} || github.ref_type == 'tag'",
            f"!({DELIVERY_GATE})",
            "vars.REVIEWED_PRODUCTION_DELIVERY != 'true'",
        ):
            with self.subTest(condition=condition):
                with self.assertRaises(AssertionError):
                    assert_delivery_gated(self, condition)

    def test_exactly_one_workflow_publishes_version_notes(self):
        publishers = set()
        for path in workflow_files():
            text = path.read_text(encoding="utf-8")
            if re.search(r"release_notes\.cjs|createRelease|gh release|action-gh-release", text):
                publishers.add(path.name)
        # Text check only; scripts/publish_release.sh is reviewed separately as a
        # site-archive writer.
        self.assertEqual(publishers, {"release-notes.yml"})
        release = (WORKFLOWS / "release.yml").read_text(encoding="utf-8")
        # The site archive writer is separate and never loads the notes helper.
        self.assertIn("run: bash scripts/publish_release.sh", release)
        self.assertNotIn("v[0-9]", release)


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
            # A skipped required job would count as passing, so the job itself must run.
            self.assertRegex(section.split("    steps:", 1)[0], r"(?m)^    if: always\(\)$")
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
        metrics = make_dry_run("-f", "quality/Makefile", "metrics")
        coverage = make_dry_run("verify-coverage")
        tooling = make_dry_run("-f", "quality/Makefile", "tooling-tests")
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
