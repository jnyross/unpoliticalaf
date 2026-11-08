"""Check that the live site is exactly the latest build.

Usage:
    make production-build && .venv/bin/python scripts/check_live.py [--url URL] [--wait SECONDS]

It compares three things:
1. the commit in the live build.json with the commit of the local build;
2. the live build.json file list and SHA-256 hashes with the local build's;
3. every file the live site serves with the hash in the local build.

Exit code 0 means the live site matches the local build byte for byte.
Exports per-run synthetic metrics outside the published site.
"""

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from builder import feature_flags
from scripts.live_metrics import LiveMetrics

DEFAULT_URL = "https://unpoliticalaf.vercel.app/"
RECORD = "build.json"


def fetch(url, tries=3, metrics=None):
    """Return (status, body bytes). Retries network errors, not HTTP errors."""
    req = urllib.request.Request(
        url, headers={"User-Agent": "unpolitical-live-check", "Cache-Control": "no-cache"}
    )
    for attempt in range(tries):
        started = time.perf_counter()
        status, size = None, 0
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read()
                status, size = r.status, len(body)
                return status, body
        except urllib.error.HTTPError as e:
            status = e.code
            e.close()
            return e.code, b""
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt == tries - 1:
                return None, str(e).encode()
        finally:
            if metrics is not None:
                metrics.observe(status, size, time.perf_counter() - started)
        time.sleep(2**attempt)


def live_record(base, metrics=None):
    status, body = fetch(f"{base}{RECORD}?t={time.time_ns()}", metrics=metrics)
    if status != 200:
        why = f"HTTP {status}" if status else body.decode(errors="replace")
        return (
            None,
            f"could not read {base}{RECORD} ({why}); the live site may predate build records",
        )
    try:
        return json.loads(body), None
    except ValueError:
        return None, f"{base}{RECORD} is not valid JSON"


def compare(base, local, live, metrics=None):
    """Return a list of problems, empty if live matches local."""
    problems = []
    if not isinstance(live, dict):
        return ["Live build record is not an object."]
    lc, vc = local["commit"], live.get("commit")
    if lc != vc:
        problems.append(f"Live site is commit {vc}, latest build is {lc}.")
        return problems
    try:
        remote_settings = feature_flags.snapshot(live.get("feature_flags", {}))
    except (TypeError, ValueError):
        problems.append("Live feature flags are missing or invalid.")
    else:
        if dict(remote_settings) != local["feature_flags"]:
            problems.append("Live feature flags differ from the independently rebuilt local build.")
    lf, vf = local["files"], live.get("files", {})
    if not isinstance(vf, dict):
        return problems + ["Live file manifest is not an object."]
    for path in sorted(set(lf) - set(vf)):
        problems.append(f"Missing from live build record: {path}")
    for path in sorted(set(vf) - set(lf)):
        problems.append(f"Extra in live build record: {path}")
    for path in sorted(set(lf) & set(vf)):
        if lf[path] != vf[path]:
            problems.append(
                f"Same commit but a different build of {path} (build is not reproducible)"
            )

    def served(path):
        status, body = fetch(base + path, metrics=metrics)
        if status != 200:
            return path, f"HTTP {status}"
        return path, (
            None
            if hashlib.sha256(body).hexdigest() == lf[path]
            else "content differs from the build"
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        for path, err in pool.map(served, sorted(lf)):
            if err:
                problems.append(f"Live {path}: {err}")
    return problems


def summary(lines):
    out = os.environ.get("GITHUB_STEP_SUMMARY")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--url", default=DEFAULT_URL, help="live site address")
    ap.add_argument("--site", default=str(ROOT / "site"), help="local build folder")
    ap.add_argument(
        "--wait", type=int, default=0, help="seconds to keep waiting for the live commit to match"
    )
    ap.add_argument(
        "--metrics-file",
        default=str(ROOT / ".metrics/live.prom"),
        help="Prometheus textfile destination, outside the public site",
    )
    args = ap.parse_args(argv)
    metrics_path = Path(args.metrics_file).resolve()
    if metrics_path.is_relative_to(Path(args.site).resolve()):
        ap.error("--metrics-file must be outside --site")
    if not 0 <= args.wait <= 1800:
        ap.error("--wait must be between 0 and 1800 seconds")
    metrics = LiveMetrics()
    result = 1
    try:
        result = check(args, metrics)
        return result
    finally:
        metrics.finish(result == 0, metrics_path)


def check(args, metrics):
    base = args.url if args.url.endswith("/") else args.url + "/"
    path = Path(args.site) / RECORD
    if not path.exists():
        print(f"{path} not found: run `make production-build` first.")
        return 2
    try:
        local = json.loads(path.read_text(encoding="utf-8"))
        settings = feature_flags.snapshot(local["feature_flags"])
        if settings != feature_flags.production():
            raise ValueError("Local flags do not match the reviewed production configuration")
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(
            f"Cannot verify production flags ({type(error).__name__}); run `make production-build`."
        )
        return 2
    if local["commit"] == "unknown":
        print("The local build does not know its commit; build from a git checkout.")
        return 2

    deadline = time.time() + args.wait
    while True:
        live, err = live_record(base, metrics)
        if isinstance(live, dict) and live.get("commit") == local["commit"]:
            break
        if time.time() >= deadline:
            break
        print(f"Waiting for {base} to serve {local['commit'][:7]}.")
        time.sleep(30)

    problems = [err] if err else compare(base, local, live, metrics)
    n = len(local["files"])
    if problems:
        lines = [
            "## Live site does not match the latest build",
            "",
            f"Checked {base} against commit `{local['commit']}`.",
            "",
        ]
        lines += [f"- {p}" for p in problems[:50]]
        if len(problems) > 50:
            lines.append(f"- … and {len(problems) - 50} more")
    else:
        lines = [
            "## Live site matches the latest build",
            "",
            f"{base} serves commit `{local['commit']}`, and all {n} files match the build byte for byte.",
        ]
    print("\n".join(lines))
    summary(lines)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
