"""One fail-closed test path: fresh pytest workers, timings and retained outcomes."""

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import tempfile
from time import perf_counter


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
        "successful": bool(runs)
        and bool(stable_passed)
        and not flaky
        and all(
            run["exit_code"] == 0
            and run["successful"]
            and run["complete"]
            and not run.get("problem")
            for run in runs
        )
        and all("missing" not in data["outcomes"] for data in tests.values()),
    }


def markdown(report):
    lines = [
        "# Test stability",
        "",
        f"Result: **{'PASS' if report['successful'] else 'FAIL'}**",
        f"Runs: {len(report['runs'])}; test IDs: {report['total_tests']}; "
        f"passed every run: {report['stable_passed']}; changing outcomes: "
        f"{len(report['flaky_tests'])}.",
        "",
        "| Run | Hash seed | Exit code | Tests run | Runner problem |",
        "| --- | --- | --- | --- | --- |",
    ]
    for run in report["runs"]:
        lines.append(
            f"| {run['run']} | {run['hash_seed']} | {run['exit_code']} | "
            f"{run['tests_run']} | {run.get('problem', '')} |"
        )
    lines += [
        "",
        "## Tests not passing every run",
        "",
        "| Test ID | Outcomes by run | Pass rate | Flaky |",
        "| --- | --- | --- | --- |",
    ]
    for test, data in report["tests"].items():
        if data["pass_rate"] < 1:
            safe_id = test.replace("|", r"\|").replace("\n", " ").replace("`", "'")
            lines.append(
                f"| `{safe_id}` | {', '.join(data['outcomes'])} | "
                f"{data['pass_rate']:.0%} | {'yes' if data['flaky'] else 'no'} |"
            )
    lines += [
        "",
        "All attempts count. A later pass never clears an earlier failure. Stable skips "
        "and expected failures are recorded, not counted as passing tests.",
        "See report.json, run-*/timings.json and run-*.log for outcomes, timings and tracebacks.",
        "",
    ]
    return "\n".join(lines)


def read_worker_report(path, run):
    """Validate worker evidence without letting it replace the process exit status."""
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
        rows = report["tests"]
        tests = {row["test"]: row["outcome"] for row in rows}
        allowed = {
            "passed",
            "failure",
            "error",
            "skipped",
            "expected_failure",
            "unexpected_success",
            "missing",
        }
        if (
            report["schema_version"] != 1
            or not isinstance(report["complete"], bool)
            or not isinstance(report["successful"], bool)
            or not isinstance(report["pid"], int)
            or report["hash_seed"] != run["hash_seed"]
            or len(tests) != len(rows)
            or report["tests_run"] != len(rows)
            or any(outcome not in allowed for outcome in tests.values())
        ):
            raise ValueError("invalid worker report")
        run.update(
            tests=tests,
            tests_run=report["tests_run"],
            collected=report["collected"],
            pid=report["pid"],
            complete=report["complete"],
            successful=report["successful"],
            collection_errors=report["collection_errors"],
            pytest_args=report["pytest_args"],
            pytest_addopts=report["pytest_addopts"],
            deselected=report["deselected"],
        )
        if report["collection_errors"]:
            run["problem"] = "collection errors; see timing report and log"
        elif not tests:
            run["problem"] = "no tests executed"
        elif set(report["collected"]) != set(tests):
            run["problem"] = "incomplete collected/executed population"
        elif not report["complete"] or "missing" in tests.values():
            run["problem"] = "incomplete worker report"
        if any(outcome in {"failure", "error", "unexpected_success"} for outcome in tests.values()):
            run["successful"] = False
    except (OSError, ValueError, KeyError, TypeError) as error:
        run["problem"] = f"no report or invalid timing report ({type(error).__name__}); see log"
        run["successful"] = False
        run["complete"] = False


def run_attempt(number, args, output):
    run = {
        "run": number,
        "hash_seed": str(number),
        "tests": {},
        "collected": [],
        "tests_run": 0,
        "successful": False,
        "complete": False,
        "exit_code": None,
    }
    path = output / f"run-{number}"
    command = [
        sys.executable,
        "-m",
        "scripts.test_performance",
        "--report-dir",
        str(path),
        "--",
        *args.pytest_args,
    ]
    started = perf_counter()
    with (output / f"run-{number}.log").open("w", encoding="utf-8") as log:
        try:
            with subprocess.Popen(
                command,
                env={**os.environ, "PYTHONHASHSEED": str(number)},
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=os.name == "posix",
            ) as process:
                try:
                    run["exit_code"] = process.wait(timeout=args.timeout)
                except subprocess.TimeoutExpired:
                    run.update(exit_code=124, problem="worker timed out")
                finally:
                    try:
                        if os.name == "posix":
                            os.killpg(process.pid, signal.SIGKILL)
                        elif process.poll() is None:
                            process.kill()
                    except ProcessLookupError:
                        pass
                    process.wait()
        except OSError as error:
            run.update(exit_code=127, problem=f"worker launch failed: {error}")
    run["duration_seconds"] = perf_counter() - started
    original_problem = run.get("problem")
    read_worker_report(path / "timings.json", run)
    if original_problem:
        run["problem"] = original_problem
    return run


def check_stability(args):
    args.output.mkdir(parents=True, exist_ok=True)
    # Every invocation and attempt has a fresh path. Crashes cannot reuse old success.
    output = Path(tempfile.mkdtemp(prefix="invocation-", dir=args.output)).resolve()
    print(f"Test evidence: {output}", flush=True)
    runs = []
    for number in range(1, args.runs + 1):
        run = run_attempt(number, args, output)
        runs.append(run)
        print(
            f"Run {number}/{args.runs}: seed {number}, exit {run['exit_code']}, "
            f"{run['tests_run']} tests ({run['duration_seconds']:.3f}s)",
            flush=True,
        )
        if args.runs == 1:
            print((output / f"run-{number}.log").read_text(encoding="utf-8", errors="replace"))
    report = summarize(runs)
    report.update(
        schema_version=1,
        generated_at=datetime.now(timezone.utc).isoformat(),
        python=platform.python_version(),
        platform=platform.platform(),
        commit=os.environ.get("GITHUB_SHA") or os.environ.get("VERCEL_GIT_COMMIT_SHA"),
        pytest_args=args.pytest_args,
        pytest_addopts=os.environ.get("PYTEST_ADDOPTS", ""),
    )
    summary = markdown(report)
    (output / "summary.md").write_text(summary, encoding="utf-8")
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(summary)
    return 0 if report["successful"] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=900, help="seconds per fresh process")
    parser.add_argument("--output", type=Path, default=Path("test-results/stability"))
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.runs < 1 or not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--runs must be positive and --timeout must be finite and positive")
    if args.pytest_args[:1] == ["--"]:
        args.pytest_args = args.pytest_args[1:]
    previous_handler = signal.signal(signal.SIGTERM, _terminate)
    try:
        return check_stability(args)
    except OSError as error:
        print(f"Test reporting failed: {error}", file=sys.stderr)
        return 1
    finally:
        signal.signal(signal.SIGTERM, previous_handler)


def _terminate(signum, frame):
    raise SystemExit(128 + signum)


if __name__ == "__main__":
    sys.exit(main())
