"""Run unittest discovery and retain suite and per-test timings (Python 3.10+)."""
import argparse
import json
import os
import platform
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter


class TimedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timings = []

    def startTest(self, test):
        super().startTest(test)
        self.started = perf_counter()

    def stopTest(self, test):
        self.timings.append({"test": test.id(), "seconds": perf_counter() - self.started})
        super().stopTest(test)


def run_suite(suite, report_dir, stream=None):
    """Keep unittest's outcomes and exit status, including failed imports/subtests."""
    started = perf_counter()
    result = unittest.TextTestRunner(
        stream=stream, verbosity=2, resultclass=TimedResult,
    ).run(suite)
    seconds = perf_counter() - started
    successful = result.wasSuccessful() and result.testsRun > 0
    timings = sorted(result.timings, key=lambda row: (-row["seconds"], row["test"]))
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "commit": os.environ.get("GITHUB_SHA"),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "suite_seconds": seconds,
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "expected_failures": len(result.expectedFailures),
        "unexpected_successes": len(result.unexpectedSuccesses),
        "successful": successful,
        "tests": timings,
    }
    lines = [
        "## Unit test performance",
        "",
        f"Result: **{'passed' if successful else 'failed'}**. "
        f"{result.testsRun} tests in **{seconds:.3f} seconds**.",
        f"Failures: {report['failures']}; errors: {report['errors']}; "
        f"skipped: {report['skipped']}; expected failures: {report['expected_failures']}; "
        f"unexpected successes: {report['unexpected_successes']}.",
        "",
        "### Slowest tests",
        "",
        "| Seconds | Test |",
        "| ---: | --- |",
    ]
    lines += [f"| {row['seconds']:.6f} | `{row['test']}` |" for row in timings[:10]]
    lines += [
        "",
        "Per-test times include setUp, tearDown and cleanups. Class/module fixtures "
        "are included only in suite time. Discovery is excluded.",
        "Download the test-performance artifact for every test's duration and run metadata.",
        "",
    ]
    if not result.testsRun:
        lines += ["No tests were discovered; this run fails.", ""]
    summary = "\n".join(lines)
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "timings.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (report_dir / "summary.md").write_text(summary, encoding="utf-8")
    print(summary)
    return 0 if successful else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-s", "--start-directory", default="tests")
    parser.add_argument("-p", "--pattern", default="test*.py")
    parser.add_argument("--report-dir", type=Path, default=Path("test-results"))
    args = parser.parse_args(argv)
    suite = unittest.TestLoader().discover(args.start_directory, pattern=args.pattern)
    return run_suite(suite, args.report_dir)


if __name__ == "__main__":
    sys.exit(main())
