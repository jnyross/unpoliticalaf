"""Read-only release gate linking a production build to durable deployment evidence.

The caller still owns independent checks and release activation. This gate does
not deploy, record receipts, or substitute a new provider check for the original
live-byte verification. Reusable live verification logs its caller's run URL.
"""

import argparse
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import package_release  # noqa: E402
from scripts import record_deployment as deploy  # noqa: E402

ALLOWED_EVENTS = frozenset({"push", "workflow_dispatch"})
RUN_ID_PATTERN = r"[1-9][0-9]{0,19}"


def _verified_run(api, commit, run_id):
    run = api.request(f"actions/runs/{run_id}")
    deploy.validate_run(run, commit, int(run_id), completed=True)
    run_url = f"https://github.com/{deploy.REPOSITORY}/actions/runs/{run_id}"
    if not (run.get("event") in ALLOWED_EVENTS and run.get("html_url") == run_url):
        raise ValueError("Upstream run is not an approved production workflow")
    comparison = api.request(f"compare/main...{commit}")
    if not isinstance(comparison, dict) or comparison.get("status") not in {"identical", "behind"}:
        raise ValueError("Release commit is not reachable from main")
    return run_url


def verify(api, commit, run_id, site):
    """Return an owned receipt ID only for the exact build and successful run.

    Receipt recovery preserves the original payload recording_run. Therefore the
    success status, not that original field, must link the upstream run supplied
    here. Historical success remains evidence after an auto-inactive status.
    """
    package_release._validate_commit(commit)
    if not isinstance(run_id, str) or not re.fullmatch(RUN_ID_PATTERN, run_id):
        raise ValueError("Run ID must be a positive bounded decimal GitHub run ID")
    bodies = package_release._site_bodies(Path(site), commit)
    build_sha256 = hashlib.sha256(bodies["build.json"]).hexdigest()
    run_url = _verified_run(api, commit, run_id)
    query = urlencode({"sha": commit, "environment": deploy.ENVIRONMENT, "task": "deploy"})
    for receipt in api.pages(f"deployments?{query}"):
        if not (
            deploy.owned(receipt)
            and receipt["sha"] == commit
            and receipt["payload"]["build_sha256"] == build_sha256
        ):
            continue
        # Shared validation requires the verified Actions bot on both the
        # receipt and success status, plus the production URL and run URL schema.
        if run_url in deploy.successful_runs(api, receipt):
            return receipt["id"]
    raise ValueError("No successful production receipt links this build and upstream run")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--commit", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--site", type=Path, default=ROOT / "site")
    args = parser.parse_args(argv)
    try:
        api = deploy.GitHub(os.environ.get("GITHUB_REPOSITORY", deploy.REPOSITORY))
        receipt_id = verify(api, args.commit, args.run_id, args.site)
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error:
        # Never echo gh output, tokens, API bodies, or caller-controlled values.
        print(f"Release evidence failed ({type(error).__name__}).", file=sys.stderr)
        return 1
    print(f"Release evidence verified: production receipt {receipt_id}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
