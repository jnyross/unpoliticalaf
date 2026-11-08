"""Real fresh-process fixtures for the canonical pytest timing/stability path."""

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import time

import pytest

ROOT = Path(__file__).resolve().parents[2]


def probe(tmp_path, source, *options, runs=3):
    suite = tmp_path / "suite"
    suite.mkdir()
    (suite / "test_sample.py").write_text(textwrap.dedent(source))
    output = tmp_path / "reports"
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.test_stability",
            "--output",
            str(output),
            "--runs",
            str(runs),
            *options,
            "--",
            str(suite),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=40,
        env={**os.environ, "PYTHONHASHSEED": "99", "PYTEST_ADDOPTS": ""},
    )
    reports = list(output.glob("*/report.json"))
    assert reports, process.stdout + process.stderr
    report_path = reports[0]
    return process, json.loads(report_path.read_text()), report_path.parent


def test_fresh_seeds_keep_first_failure_after_later_passes(tmp_path):
    process, report, folder = probe(
        tmp_path,
        """
        import os
        def test_changes():
            print("worker", os.getpid(), os.environ["PYTHONHASHSEED"])
            assert os.environ["PYTHONHASHSEED"] != "1"
        """,
    )
    assert process.returncode == 1
    assert not report["successful"]
    assert [run["hash_seed"] for run in report["runs"]] == ["1", "2", "3"]
    assert [run["exit_code"] for run in report["runs"]] == [1, 0, 0]
    assert len({run["pid"] for run in report["runs"]}) == 3
    data = next(iter(report["tests"].values()))
    assert data["outcomes"] == ["failure", "passed", "passed"]
    assert data["pass_rate"] == 2 / 3
    assert data["flaky"]
    assert "AssertionError" in (folder / "run-1.log").read_text()
    assert all((folder / f"run-{number}" / "timings.json").exists() for number in (1, 2, 3))


@pytest.mark.parametrize(
    "source,outcome",
    [
        ("def test_bad(): assert False", "failure"),
        ("def test_bad(): raise RuntimeError('test error')", "failure"),
        (
            "import pytest\n@pytest.fixture\ndef broken(): raise RuntimeError('fixture')\n"
            "def test_bad(broken): pass",
            "error",
        ),
        (
            "import pytest\n@pytest.fixture\ndef broken():\n yield\n"
            " raise RuntimeError('teardown')\ndef test_bad(broken): pass",
            "error",
        ),
        (
            "import unittest\nclass Sample(unittest.TestCase):\n"
            " def test_bad(self):\n  with self.subTest(value=1): self.fail('subtest')",
            "failure",
        ),
        (
            "import unittest\nclass Sample(unittest.TestCase):\n"
            " @unittest.expectedFailure\n def test_bad(self): pass",
            "failure",
        ),
    ],
)
def test_original_failed_outcomes_remain_failed(tmp_path, source, outcome):
    process, report, _ = probe(tmp_path, source, runs=1)
    assert process.returncode == 1
    assert not report["successful"]
    assert next(iter(report["tests"].values()))["outcomes"] == [outcome]
    assert report["flaky_tests"] == []


@pytest.mark.parametrize(
    "source,options,problem",
    [
        ("raise ImportError('discovery error')", (), "collection"),
        ("# empty suite", (), "no tests"),
        ("import os; os._exit(0)", (), "no report"),
        ("import os; os._exit(7)", (), "no report"),
        ("import time; time.sleep(10)", ("--timeout", "0.1"), "timed out"),
    ],
)
def test_incomplete_runs_fail_without_fabricating_success(tmp_path, source, options, problem):
    process, report, folder = probe(tmp_path, source, *options, runs=1)
    assert process.returncode == 1
    assert not report["successful"]
    assert problem in json.dumps(report).lower()
    assert "**FAIL**" in (folder / "summary.md").read_text()


def test_skip_xfail_and_slowest_full_timing_population(tmp_path):
    source = (
        "import pytest\n"
        "@pytest.mark.skip(reason='fixture')\ndef test_skip(): pass\n"
        "@pytest.mark.xfail(reason='fixture')\ndef test_expected(): assert False\n"
        + "\n".join(f"def test_ok_{number}(): pass" for number in range(12))
    )
    process, report, folder = probe(tmp_path, source, runs=1)
    assert process.returncode == 0, process.stdout + process.stderr
    assert report["stable_passed"] == 12
    assert report["total_tests"] == 14
    timing = json.loads((folder / "run-1" / "timings.json").read_text())
    assert timing["successful"] and timing["complete"]
    assert len(timing["tests"]) == 14
    assert [row["seconds"] for row in timing["tests"]] == sorted(
        (row["seconds"] for row in timing["tests"]), reverse=True
    )
    assert (folder / "run-1" / "summary.md").read_text().count("| `") == 10
    for key in ("python", "platform", "generated_at", "commit", "suite_seconds", "pid"):
        assert key in timing
    outcomes = [data["outcomes"][0] for data in report["tests"].values()]
    assert outcomes.count("skipped") == 1
    assert outcomes.count("expected_failure") == 1


def test_missing_and_changing_skips_fail(tmp_path):
    process, report, _ = probe(
        tmp_path,
        """
        import os
        import pytest
        @pytest.mark.skipif(os.environ["PYTHONHASHSEED"] == "1", reason="changing")
        def test_changes(): pass
        if os.environ["PYTHONHASHSEED"] != "1":
            def test_missing(): pass
        """,
    )
    assert process.returncode == 1
    assert any(data["flaky"] for data in report["tests"].values())
    assert any("missing" in data["outcomes"] for data in report["tests"].values())


def test_pytest_fixture_time_includes_setup_and_teardown(tmp_path):
    source = """
        import time
        import pytest
        @pytest.fixture
        def measured():
            time.sleep(0.02)
            yield
            time.sleep(0.02)
        def test_ok(measured): pass
    """
    process, report, folder = probe(tmp_path, source, runs=1)
    assert process.returncode == 0
    timing = json.loads((folder / "run-1" / "timings.json").read_text())
    assert timing["tests"][0]["seconds"] >= 0.04
    assert timing["tests"][0]["phases"]["setup"] >= 0.02
    assert timing["tests"][0]["phases"]["teardown"] >= 0.02
    assert report["runs"][0]["collected"] == list(report["tests"])


def test_report_write_error_cannot_leave_success_marker(tmp_path):
    from scripts.test_performance import run_tests

    suite = tmp_path / "test_example.py"
    suite.write_text("def test_ok(): pass\n")
    output = tmp_path / "output"
    output.mkdir()
    (output / "summary.md").mkdir()
    assert run_tests([str(suite)], output) != 0
    assert not (output / "timings.json").exists()


def test_malformed_report_and_original_exit_cannot_be_forgiven():
    from scripts.test_stability import summarize

    run = {
        "tests": {"example": "passed"},
        "collected": ["example"],
        "complete": True,
        "exit_code": 1,
        "successful": True,
    }
    assert not summarize([run, {**run, "exit_code": 0}])["successful"]


def test_invocations_never_reuse_stale_success(tmp_path):
    process, _, folder = probe(tmp_path, "def test_ok(): pass", runs=1)
    assert process.returncode == 0
    suite = tmp_path / "suite"
    (suite / "test_sample.py").write_text("import os; os._exit(0)\n")
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.test_stability",
            "--runs",
            "1",
            "--output",
            str(folder.parent),
            "--",
            str(suite),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "PYTEST_ADDOPTS": ""},
    )
    assert process.returncode == 1
    reports = [json.loads(path.read_text()) for path in folder.parent.glob("*/report.json")]
    assert sorted(report["successful"] for report in reports) == [False, True]


@pytest.mark.parametrize("payload", ["not json", "{}", '{"tests": null}', "[]"])
def test_invalid_worker_evidence_fails_closed(tmp_path, payload):
    from scripts.test_stability import read_worker_report

    path = tmp_path / "timings.json"
    path.write_text(payload)
    run = {"exit_code": 0, "successful": True, "complete": True, "hash_seed": "1"}
    read_worker_report(path, run)
    assert run["exit_code"] == 0
    assert not run["successful"]
    assert not run["complete"]
    assert "invalid timing report" in run["problem"]


def test_nonstrict_xpass_is_not_forgiven_by_pytest_zero_exit(tmp_path):
    process, report, _ = probe(
        tmp_path,
        "import pytest\n@pytest.mark.xfail(reason='unexpected')\ndef test_xpass(): pass",
        runs=1,
    )
    assert process.returncode == 1
    assert next(iter(report["tests"].values()))["outcomes"] == ["unexpected_success"]


def test_all_skips_do_not_fabricate_passing_tests(tmp_path):
    process, report, _ = probe(
        tmp_path,
        "import pytest\n@pytest.mark.skip(reason='fixture')\ndef test_skip(): pass",
        runs=1,
    )
    assert process.returncode == 1
    assert report["stable_passed"] == 0


def test_incomplete_report_keeps_original_failed_outcomes(tmp_path):
    from scripts.test_stability import read_worker_report

    path = tmp_path / "timings.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "tests": [
                    {"test": "failed", "outcome": "failure"},
                    {"test": "interrupted", "outcome": "missing"},
                ],
                "tests_run": 2,
                "collected": ["failed", "interrupted"],
                "complete": False,
                "successful": False,
                "pid": 123,
                "hash_seed": "1",
                "collection_errors": [],
                "pytest_args": [],
                "pytest_addopts": "",
                "deselected": 0,
            }
        )
    )
    run = {"exit_code": 2, "hash_seed": "1"}
    read_worker_report(path, run)
    assert run["tests"] == {"failed": "failure", "interrupted": "missing"}
    assert run["exit_code"] == 2
    assert run["problem"] == "incomplete worker report"


def test_selection_metadata_and_nested_collection(tmp_path):
    suite = tmp_path / "suite"
    nested = suite / "architecture"
    nested.mkdir(parents=True)
    (nested / "test_boundary.py").write_text("def test_keep(): pass\ndef test_deselect(): pass\n")
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.test_stability",
            "--runs",
            "1",
            "--output",
            str(tmp_path / "reports"),
            "--",
            str(suite),
            "-k",
            "keep",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "PYTEST_ADDOPTS": "-q"},
    )
    assert process.returncode == 0, process.stdout + process.stderr
    report = json.loads(next((tmp_path / "reports").glob("*/report.json")).read_text())
    assert report["pytest_args"] == [str(suite), "-k", "keep"]
    assert report["pytest_addopts"] == "-q"
    assert report["runs"][0]["deselected"] == 1
    assert "architecture/test_boundary.py::test_keep" in next(iter(report["tests"]))


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group cancellation")
def test_parent_termination_stops_its_worker(tmp_path):
    suite = tmp_path / "suite"
    suite.mkdir()
    marker = tmp_path / "worker-pid"
    (suite / "test_wait.py").write_text(
        f"import os, pathlib, time\npathlib.Path({str(marker)!r}).write_text(str(os.getpid()))\n"
        "time.sleep(60)\n"
    )
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "scripts.test_stability",
            "--runs",
            "1",
            "--output",
            str(tmp_path / "reports"),
            "--",
            str(suite),
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env={**os.environ, "PYTEST_ADDOPTS": ""},
    )
    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert marker.exists()
        worker_pid = int(marker.read_text())
        process.terminate()
        assert process.wait(timeout=10) == 143
        with pytest.raises(ProcessLookupError):
            os.kill(worker_pid, 0)
        assert not list((tmp_path / "reports").glob("*/report.json"))
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)


def test_three_stable_fresh_processes_pass(tmp_path):
    process, report, _ = probe(tmp_path, "def test_ok(): assert 2 + 2 == 4")
    assert process.returncode == 0
    assert report["stable_passed"] == 1
    assert report["flaky_tests"] == []
    assert [run["hash_seed"] for run in report["runs"]] == ["1", "2", "3"]
    assert [run["exit_code"] for run in report["runs"]] == [0, 0, 0]
    assert len({run["pid"] for run in report["runs"]}) == 3


def test_unittest_class_fixture_error_is_retained(tmp_path):
    process, report, _ = probe(
        tmp_path,
        """
        import unittest
        class Sample(unittest.TestCase):
            @classmethod
            def setUpClass(cls): raise RuntimeError("class fixture")
            def test_not_run(self): pass
        """,
        runs=1,
    )
    assert process.returncode == 1
    assert next(iter(report["tests"].values()))["outcomes"] == ["error"]


def test_default_collection_retains_all_nested_populations():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "PYTEST_ADDOPTS": ""},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "tests/tooling/test_test_stability.py::" in result.stdout
    assert "quality/tests/test_report.py::" in result.stdout
