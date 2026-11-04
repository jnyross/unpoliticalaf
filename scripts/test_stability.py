"""Repeat unittest discovery in fresh processes; retain failures and changing outcomes."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


class StabilityResult(unittest.TextTestResult):
    """Record parent-test outcomes, including subtests and class/module fixtures."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outcomes = {}

    def record(self, test, outcome):
        test = getattr(test, "test_case", test)  # A skipped subtest has a parent.
        previous = self.outcomes.get(test.id())
        if previous not in {"failure", "error", "unexpected_success"}:
            self.outcomes[test.id()] = outcome

    def addSuccess(self, test):
        super().addSuccess(test)
        self.record(test, "passed")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.record(test, "failure")

    def addError(self, test, err):
        super().addError(test, err)
        self.record(test, "error")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.record(test, "skipped")

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.record(test, "expected_failure")

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.record(test, "unexpected_success")

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self.record(test, "failure" if issubclass(err[0], test.failureException) else "error")


def worker(args):
    suite = unittest.defaultTestLoader.discover(args.start_directory, pattern=args.pattern)
    result = unittest.TextTestRunner(verbosity=2, resultclass=StabilityResult).run(suite)
    args.worker_report.write_text(json.dumps({
        "tests": result.outcomes,
        "tests_run": result.testsRun,
        "successful": result.wasSuccessful(),
    }), encoding="utf-8")
    return 0 if result.wasSuccessful() and result.testsRun else 1


def summarize(runs):
    ids = sorted({test for run in runs for test in run["tests"]})
    tests = {}
    for test in ids:
        outcomes = [run["tests"].get(test, "missing") for run in runs]
        tests[test] = {
            "outcomes": outcomes,
            "flaky": len(set(outcomes) - {"missing"}) > 1,
            "pass_rate": outcomes.count("passed") / len(runs),
        }
    flaky = [test for test, data in tests.items() if data["flaky"]]
    stable_passed = sum(data["pass_rate"] == 1 for data in tests.values())
    return {
        "runs": runs,
        "tests": tests,
        "total_tests": len(tests),
        "stable_passed": stable_passed,
        "flaky_tests": flaky,
        "successful": bool(stable_passed) and not flaky
        and all(run["exit_code"] == 0 and run["successful"] for run in runs)
        and all("missing" not in data["outcomes"] for data in tests.values()),
    }


def markdown(report):
    lines = [
        "# Test stability",
        "",
        f"Result: **{'PASS' if report['successful'] else 'FAIL'}**",
        f"Runs: {len(report['runs'])}; test IDs: {report['total_tests']}; "
        f"passed every run: {report['stable_passed']}; "
        f"changing outcomes (flaky): {len(report['flaky_tests'])}.",
        "",
        "| Run | Hash seed | Exit code | Tests run | Runner problem |",
        "| --- | --- | --- | --- | --- |",
    ]
    for run in report["runs"]:
        lines.append(f"| {run['run']} | {run['hash_seed']} | {run['exit_code']} | "
                     f"{run['tests_run']} | {run.get('problem', '')} |")
    lines += ["", "## Tests not passing every run", "",
              "| Test ID | Outcomes by run | Pass rate | Flaky |",
              "| --- | --- | --- | --- |"]
    for test, data in report["tests"].items():
        if data["pass_rate"] < 1:
            safe_id = test.replace("|", r"\|").replace("\n", " ")
            lines.append(f"| `{safe_id}` | {', '.join(data['outcomes'])} | "
                         f"{data['pass_rate']:.0%} | {'yes' if data['flaky'] else 'no'} |")
    lines += ["", "All attempts count. A later pass never clears an earlier failure.",
              "See report.json and run-*.log for per-test outcomes and tracebacks.", ""]
    return "\n".join(lines)


def check_stability(args):
    args.output.mkdir(parents=True, exist_ok=True)
    runs = []
    # Fresh report paths prevent a crashed worker from reusing an earlier report.
    with tempfile.TemporaryDirectory(prefix="test-stability-") as folder:
        for number in range(1, args.runs + 1):
            path = Path(folder) / f"run-{number}.json"
            command = [
                sys.executable, "-m", "scripts.test_stability",
                "--worker-report", str(path), "--start-directory", args.start_directory,
                "--pattern", args.pattern,
            ]
            run = {"run": number, "hash_seed": str(number), "tests": {},
                   "tests_run": 0, "successful": False}
            started = time.monotonic()
            with (args.output / f"run-{number}.log").open("w", encoding="utf-8") as log:
                try:
                    process = subprocess.run(
                        command, env={**os.environ, "PYTHONHASHSEED": str(number)},
                        stdout=log, stderr=subprocess.STDOUT, timeout=args.timeout,
                    )
                    run["exit_code"] = process.returncode
                except subprocess.TimeoutExpired:
                    run.update(exit_code=124, problem="worker timed out")
            run["duration_seconds"] = round(time.monotonic() - started, 3)
            if path.exists():
                run.update(json.loads(path.read_text(encoding="utf-8")))
            else:
                run.setdefault("problem", "worker produced no report; see run log")
            runs.append(run)
            print(f"Run {number}/{args.runs}: exit {run['exit_code']}, "
                  f"{run['tests_run']} tests ({run['duration_seconds']}s)", flush=True)
    report = summarize(runs)
    report["python"] = sys.version
    report["commit"] = os.environ.get("GITHUB_SHA")
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    summary = markdown(report)
    (args.output / "summary.md").write_text(summary, encoding="utf-8")
    print(summary)
    return 0 if report["successful"] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=300, help="seconds per run")
    parser.add_argument("--output", type=Path, default=Path("artifacts/test-stability"))
    parser.add_argument("--start-directory", default="tests")
    parser.add_argument("--pattern", default="test*.py")
    parser.add_argument("--worker-report", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.runs < 2 or args.timeout <= 0:
        parser.error("--runs must be at least 2 and --timeout must be positive")
    return worker(args) if args.worker_report else check_stability(args)


if __name__ == "__main__":
    sys.exit(main())
