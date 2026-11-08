"""The single pytest worker used by timing and seeded stability (Python 3.10+)."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import sys
from time import perf_counter

# Developer-only entry point, not an import in the production build/check graph.
import pytest  # deptry: ignore[DEP004]

BAD_OUTCOMES = {"failure", "error", "unexpected_success"}


class TimingReport:
    """Keep every phase; a passing teardown must never replace a failed call."""

    def __init__(self):
        self.tests = {}
        self.collected = []
        self.collection_errors = []
        self.deselected = 0
        self.started = None
        self.seconds = 0
        self.finished = False

    def pytest_collection_finish(self, session):
        self.collected = [item.nodeid for item in session.items]
        self.started = perf_counter()

    def pytest_collectreport(self, report):
        if report.failed:
            self.collection_errors.append({"test": report.nodeid, "message": str(report.longrepr)})

    def pytest_deselected(self, items):
        self.deselected += len(items)

    def pytest_runtest_logreport(self, report):
        row = self.tests.setdefault(
            report.nodeid,
            {"test": report.nodeid, "outcome": "missing", "phases": {}, "finished": False},
        )
        row["phases"][report.when] = report.duration
        if report.when == "teardown":
            row["finished"] = True
        outcome = None
        if report.failed:
            outcome = "failure" if report.when == "call" else "error"
        elif hasattr(report, "wasxfail"):
            outcome = "expected_failure" if report.skipped else "unexpected_success"
        elif report.skipped:
            outcome = "skipped"
        elif report.when == "call":
            outcome = "passed"
        if outcome and row["outcome"] not in BAD_OUTCOMES:
            row["outcome"] = outcome

    def pytest_sessionfinish(self, session, exitstatus):
        self.finished = True
        if self.started is not None:
            self.seconds = perf_counter() - self.started

    def report(self, exit_code, wall_seconds):
        rows = [{**row, "seconds": sum(row["phases"].values())} for row in self.tests.values()]
        rows.sort(key=lambda row: (-row["seconds"], row["test"]))
        complete = (
            self.finished
            and not self.collection_errors
            and len(self.collected) == len(set(self.collected))
            and set(self.collected) == set(self.tests)
            and all(row["finished"] and row["outcome"] != "missing" for row in rows)
        )
        successful = (
            exit_code == 0
            and complete
            and bool(rows)
            and not any(row["outcome"] in BAD_OUTCOMES for row in rows)
        )
        return {
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "commit": os.environ.get("GITHUB_SHA") or os.environ.get("VERCEL_GIT_COMMIT_SHA"),
            "python": platform.python_version(),
            "platform": platform.platform(),
            "pid": os.getpid(),
            "hash_seed": os.environ.get("PYTHONHASHSEED"),
            "pytest_exit_code": exit_code,
            "suite_seconds": self.seconds,
            "wall_seconds": wall_seconds,
            "collected": self.collected,
            "deselected": self.deselected,
            "tests_run": len(rows),
            "collection_errors": self.collection_errors,
            "outcome_counts": dict(Counter(row["outcome"] for row in rows)),
            "complete": complete,
            "successful": successful,
            "tests": rows,
        }


def markdown(report):
    lines = [
        "## Unit test performance",
        "",
        f"Result: **{'passed' if report['successful'] else 'failed'}**. "
        f"{report['tests_run']} tests in **{report['suite_seconds']:.3f} seconds**.",
        f"Complete: {report['complete']}; outcomes: {report['outcome_counts']}; "
        f"collection errors: {len(report['collection_errors'])}.",
        "",
        "### Slowest tests",
        "",
        "| Seconds | Test |",
        "| ---: | --- |",
    ]
    for row in report["tests"][:10]:
        safe_id = row["test"].replace("|", r"\|").replace("\n", " ").replace("`", "'")
        lines.append(f"| {row['seconds']:.6f} | `{safe_id}` |")
    lines += [
        "",
        "Per-test time sums pytest setup/call/teardown, including cleanups. Shared fixtures "
        "are charged to the test that executes them. Suite time excludes collection; "
        "wall time includes it. Timings are diagnostic, not a speed gate.",
        "",
    ]
    return "\n".join(lines)


def run_tests(pytest_args, report_dir):
    """Only publish a complete report after pytest and both report writes succeed."""
    reporter = TimingReport()
    started = perf_counter()
    exit_code = int(pytest.main(pytest_args, plugins=[reporter]))
    report = reporter.report(exit_code, perf_counter() - started)
    report.update(pytest_args=pytest_args, pytest_addopts=os.environ.get("PYTEST_ADDOPTS", ""))
    summary = markdown(report)
    report_dir = Path(report_dir)
    try:
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / "summary.md").write_text(summary, encoding="utf-8")
        # Written last: a missing timings.json is never a completed successful run.
        (report_dir / "timings.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
    except OSError as error:
        print(f"Timing report failed: {error}", file=sys.stderr)
        return exit_code or 1
    print(summary)
    return exit_code or (0 if report["successful"] else 1)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    pytest_args = args.pytest_args
    if pytest_args[:1] == ["--"]:
        pytest_args = pytest_args[1:]
    return run_tests(pytest_args, args.report_dir)


if __name__ == "__main__":
    sys.exit(main())
