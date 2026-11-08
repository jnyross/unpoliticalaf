"""Fresh combined verification coverage, using the canonical timed pytest worker."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from quality.report import source_hashes


def measure(root, output):
    root = root.resolve()
    output.mkdir(parents=True, exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix="invocation-", dir=output)).resolve()
    print(f"Coverage evidence: {output}", flush=True)
    measurement = {
        "schema_version": 1,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "source_hashes": source_hashes(root),
        "commit": os.environ.get("VERCEL_GIT_COMMIT_SHA") or os.environ.get("GITHUB_SHA"),
        "phases": [],
        "exports": [],
    }
    env = {
        **os.environ,
        "COVERAGE_RCFILE": str(root / "quality" / "coverage.ini"),
        "COVERAGE_FILE": str(output / ".coverage"),
        "PYTEST_ADDOPTS": "",
        "PYTHONHASHSEED": "1",
    }
    coverage = [sys.executable, "-m", "coverage"]

    def save():
        (output / "measurement.json").write_text(
            json.dumps(measurement, indent=2) + "\n", encoding="utf-8"
        )

    def execute(name, command, group):
        print(f"Coverage {name}: {' '.join(command)}", flush=True)
        with (output / f"{name}.log").open("w", encoding="utf-8") as log:
            result = subprocess.run(
                command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT
            )
        group.append({"name": name, "command": command, "exit_code": result.returncode})
        save()
        print((output / f"{name}.log").read_text(encoding="utf-8", errors="replace"), flush=True)
        return result.returncode

    phases = [
        ("build", ["-m", "builder.build"]),
        ("check", ["-m", "builder.check"]),
        (
            "tests",
            [
                "-m",
                "scripts.test_performance",
                "--report-dir",
                str(output / "test-timings"),
                "--",
            ],
        ),
    ]
    save()
    for index, (name, command) in enumerate(phases):
        code = execute(
            name,
            [*coverage, "run", *(["--append"] if index else []), *command],
            measurement["phases"],
        )
        if code:
            return code
    gate_code = execute("gate", [*coverage, "report"], measurement["exports"])
    if gate_code not in (0, 2):
        return gate_code
    # Keep useful reports for below-bar runs too. Only the report command enforces
    # the configured threshold; no exporter may accidentally suppress its status.
    for name, command in (
        ("html", ["html", "--fail-under=0", "-d", str(output / "coverage")]),
        ("xml", ["xml", "--fail-under=0", "-o", str(output / "coverage.xml")]),
        ("json", ["json", "--fail-under=0", "-o", str(output / "coverage.json")]),
    ):
        code = execute(name, [*coverage, *command], measurement["exports"])
        if code:
            return gate_code or code
    measurement["coverage_sha256"] = hashlib.sha256(
        (output / "coverage.json").read_bytes()
    ).hexdigest()
    save()
    code = execute(
        "dashboard",
        [sys.executable, "-m", "quality.report", "--root", str(root), "--output", str(output)],
        measurement["exports"],
    )
    return gate_code or code


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("quality-reports"))
    args = parser.parse_args(argv)
    try:
        return measure(args.root, args.output)
    except (OSError, ValueError) as error:
        print(f"Coverage measurement failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
