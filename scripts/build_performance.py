"""Time a real, fresh-process build and retain a machine-readable result.

Run with make benchmark. Setup, independent make check and tests are excluded;
the build's source hash and quote validation remain inside the timed workload.
"""

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parent.parent
# The 2026-11-04 CI build took ~44s. Allow roughly 2x for runner variation.
DEFAULT_MAX_SECONDS = 90.0


def positive_seconds(value):
    try:
        seconds = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("budget must be a finite, positive number") from error
    if not math.isfinite(seconds) or seconds <= 0:
        raise argparse.ArgumentTypeError("budget must be a finite, positive number")
    return seconds


def measure_build(max_seconds):
    # Observe before starting the clock; never import the producer to collect context.
    cache = {
        "pip_cache_hit": {"true": True, "false": False}.get(os.environ.get("BUILD_PIP_CACHE_HIT")),
        "site_existed": (ROOT / "site").exists(),
        "builder_bytecode_existed": (ROOT / "builder/__pycache__").exists(),
        "glossary_maxsize": 4096,
        "glossary_initial_entries": 0,
        "restored_build_output": False,
        "filesystem": "OS-managed; not flushed or assumed cold",
    }
    started_at = datetime.now(timezone.utc).isoformat()
    start = perf_counter()
    try:
        result = subprocess.run(["make", "build"], cwd=ROOT, check=False)
        exit_code = result.returncode
    except OSError as error:
        print(f"Could not start build: {error}", file=sys.stderr)
        exit_code = 127
    duration = perf_counter() - start
    status = "failed" if exit_code else "over_budget" if duration > max_seconds else "passed"
    return {
        "schema_version": 1,
        "command": ["make", "build"],
        "measurement": (
            "wall-clock fresh make build; source hash/quote validation included; "
            "setup and independent make check/tests excluded"
        ),
        "started_at": started_at,
        "duration_seconds": duration,
        "max_seconds": max_seconds,
        "exit_code": exit_code,
        "status": status,
        "python": platform.python_version(),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "cache": cache,
        "commit": os.environ.get("GITHUB_SHA") or os.environ.get("VERCEL_GIT_COMMIT_SHA"),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
    }


def summary(report):
    return (
        "## Build performance\n\n"
        "| Command | Duration | Budget | Result |\n"
        "| --- | ---: | ---: | --- |\n"
        f"| `make build` | {report['duration_seconds']:.2f}s | "
        f"{report['max_seconds']:.2f}s | {report['status']} "
        f"(exit {report['exit_code']}) |\n\n"
        "Fresh Python process; setup, independent make check and tests are excluded. "
        "Build source hash/quote validation is included. "
        "No generated site or parsed source data is restored from cache.\n\n"
        f"Cache context: `{json.dumps(report['cache'], sort_keys=True)}`\n"
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-seconds", type=positive_seconds, default=DEFAULT_MAX_SECONDS)
    parser.add_argument("--output", type=Path, default=ROOT / ".cache/build-performance.json")
    args = parser.parse_args(argv)
    report = measure_build(args.max_seconds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    text = summary(report)
    print(text, flush=True)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as stream:
            stream.write(text)
    # Do not let a fast, broken build pass or mask its original failure.
    return report["exit_code"] or int(report["status"] != "passed")


if __name__ == "__main__":
    sys.exit(main())
