"""Retain evidence of real Vercel deployments after exact production verification.

This command writes GitHub receipts, not Vercel deployments. --report is read-only.
Receipt writers must be serialized by their caller.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlencode, urlparse

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import check_live  # noqa: E402

SOURCE = "verified-vercel-deployment"
# GitHub environment names are case-insensitive, and Vercel's own GitHub
# integration may use Production and Preview. Receipts stay in their own
# non-production environment and never mark other deployments inactive.
ENVIRONMENT = "verified-site-receipts"
REPOSITORY = "jnyross/unpoliticalaf"
VERCEL_PROJECT_PATH = "/johns-projects-d6b53aae/unpoliticalaf/"
VERCEL_BOT_ID = 35613825
ACTIONS_BOT_ID = 41898282
WORKFLOW_PATHS = frozenset({".github/workflows/deploy.yml", ".github/workflows/live.yml"})
WORKFLOW_EVENTS = frozenset({"push", "workflow_dispatch", "workflow_call", "workflow_run"})
MAX_PAGES = 100
MAX_WAIT = 1800
SHA_PATTERN = r"[0-9a-f]{40}"
DIGEST_PATTERN = r"[0-9a-f]{64}"
ENDPOINT_PATTERN = (
    rf"(?:deployments(?:/[1-9][0-9]*/statuses)?|commits/{SHA_PATTERN}/status(?:es)?"
    rf"|compare/main\.\.\.{SHA_PATTERN}|actions/runs/[1-9][0-9]*)"
)


class GitHub:
    """Use only github.com and the approved repository, never an input URL."""

    def __init__(self, repository):
        if repository != REPOSITORY:
            raise ValueError("Deployment evidence is restricted to the approved repository")
        self.prefix = f"repos/{repository}"

    def request(self, path, data=None):
        endpoint = path.partition("?")[0]
        if not re.fullmatch(ENDPOINT_PATTERN, endpoint):
            raise ValueError("Untrusted GitHub endpoint")
        if data is not None and not (
            endpoint == "deployments" or re.fullmatch(r"deployments/[1-9][0-9]*/statuses", endpoint)
        ):
            raise ValueError("Only deployment receipt writes are supported")
        command = [
            "gh",
            "api",
            "--hostname",
            "github.com",
            "--method",
            "POST" if data is not None else "GET",
            f"{self.prefix}/{path}",
        ]
        if data is not None:
            command += ["--input", "-"]
        # Do not let caller-provided host/debug settings redirect or log a token.
        environment = dict(os.environ)
        for name in ("GH_HOST", "GH_DEBUG", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN"):
            environment.pop(name, None)
        result = subprocess.run(
            command,
            input=json.dumps(data) if data is not None else None,
            text=True,
            capture_output=True,
            check=True,
            timeout=60,
            env=environment,
        )
        return json.loads(result.stdout)

    def pages(self, path):
        separator = "&" if "?" in path else "?"
        for page in range(1, MAX_PAGES + 1):
            rows = self.request(f"{path}{separator}per_page=100&page={page}")
            if not isinstance(rows, list) or len(rows) > 100:
                raise ValueError("Invalid paginated GitHub response")
            yield from rows
            if len(rows) < 100:
                return
        raise ValueError("GitHub pagination limit reached; history is incomplete")


def provider_time(value):
    if not isinstance(value, str):
        raise ValueError("Missing provider deployment timestamp")
    when = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if when.tzinfo is None:
        raise ValueError("Provider deployment timestamp needs a timezone")
    return when


def trusted_url(value, host):
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and parsed.netloc == host
        and bool(re.fullmatch(r"/[A-Za-z0-9_./-]+", parsed.path))
        and bool(parsed.path.strip("/"))
        and not parsed.fragment
        and not parsed.query
    )


def valid_run_url(value):
    return trusted_url(value, "github.com") and bool(
        re.fullmatch(rf"/{REPOSITORY}/actions/runs/[1-9][0-9]*", urlparse(value).path)
    )


def trusted_creator(creator, login, identifier):
    return (
        isinstance(creator, dict)
        and creator.get("login") == login
        and type(creator.get("id")) is int
        and creator["id"] == identifier
        and creator.get("type") == "Bot"
    )


def valid_provider_url(value):
    return trusted_url(value, "vercel.com") and bool(
        re.fullmatch(rf"{re.escape(VERCEL_PROJECT_PATH)}[A-Za-z0-9_-]+", urlparse(value).path)
    )


def validate_provider(provider):
    if not isinstance(provider, dict) or not valid_provider_url(provider.get("target_url")):
        raise ValueError("Successful Vercel status has no trusted deployment link")
    if not trusted_creator(provider.get("creator"), "vercel[bot]", VERCEL_BOT_ID):
        raise ValueError("Vercel status must be authored by the verified Vercel bot")
    if provider.get("context") != "Vercel" or provider.get("state") != "success":
        raise ValueError("Successful Vercel status is required")
    provider_time(provider.get("created_at"))


def latest_vercel_status(api, sha):
    combined = api.request(f"commits/{sha}/status")
    if not isinstance(combined, dict) or combined.get("sha") != sha:
        raise ValueError("Vercel status is not for the checked-out commit")
    statuses = [
        status
        for status in api.pages(f"commits/{sha}/statuses")
        if isinstance(status, dict) and status.get("context") == "Vercel"
    ]
    # The statuses endpoint is reverse chronological, including across pages.
    return statuses[0] if statuses else None


def vercel_success(api, sha, wait):
    deadline = time.monotonic() + wait
    while True:
        status = latest_vercel_status(api, sha)
        if status and status.get("state") == "success":
            validate_provider(status)
            return status
        if status and status.get("state") in {"failure", "error"}:
            raise ValueError("Vercel deployment failed; no deployment recorded")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("No successful Vercel deployment status before the deadline")
        time.sleep(min(15, remaining))


def marked(deployment):
    return (
        isinstance(deployment, dict)
        and isinstance(deployment.get("payload"), dict)
        and deployment["payload"].get("source") == SOURCE
    )


def owned(deployment):
    """Validate the receipt schema; the source marker is not an authentication boundary."""
    if not marked(deployment):
        return False
    payload = deployment["payload"]
    identifier = deployment.get("id")
    if not (
        type(identifier) is int
        and identifier > 0
        and deployment.get("environment") == ENVIRONMENT
        and deployment.get("task") == "deploy"
        and trusted_creator(deployment.get("creator"), "github-actions[bot]", ACTIONS_BOT_ID)
        and isinstance(deployment.get("sha"), str)
        and re.fullmatch(SHA_PATTERN, deployment["sha"])
        and valid_provider_url(payload.get("provider_url"))
        and valid_run_url(payload.get("recording_run"))
        and isinstance(payload.get("build_sha256"), str)
        and re.fullmatch(DIGEST_PATTERN, payload["build_sha256"])
    ):
        return False
    try:
        provider_time(payload.get("deployed_at"))
    except ValueError:
        return False
    return True


def was_successful(api, deployment):
    # Preserve success history even when a later deployment marked it inactive.
    return bool(successful_runs(api, deployment))


def successful_runs(api, deployment):
    """Return verified run URLs without treating a prior run as current proof."""
    if not owned(deployment):
        return set()
    return {
        status["log_url"]
        for status in api.pages(f"deployments/{deployment['id']}/statuses")
        if (
            isinstance(status, dict)
            and status.get("state") == "success"
            and status.get("environment_url") == check_live.DEFAULT_URL
            and valid_run_url(status.get("log_url"))
            and trusted_creator(status.get("creator"), "github-actions[bot]", ACTIONS_BOT_ID)
        )
    }


def matching_receipt(deployment, sha, provider, build_sha256):
    return (
        owned(deployment)
        and deployment["sha"] == sha
        and deployment["payload"]["provider_url"] == provider["target_url"]
        and deployment["payload"]["deployed_at"] == provider["created_at"]
        and deployment["payload"]["build_sha256"] == build_sha256
    )


def record(api, sha, provider, run_url, build_sha256):
    """Return (receipt ID, receipt created); a reused receipt may get new run proof."""
    validate_provider(provider)
    if not (
        re.fullmatch(SHA_PATTERN, sha)
        and re.fullmatch(DIGEST_PATTERN, build_sha256)
        and valid_run_url(run_url)
    ):
        raise ValueError("Invalid receipt identity or verification provenance")
    query = urlencode({"sha": sha, "environment": ENVIRONMENT, "task": "deploy"})
    previous = [
        deployment
        for deployment in api.pages(f"deployments?{query}")
        if matching_receipt(deployment, sha, provider, build_sha256)
    ]
    reusable = previous[0] if previous else None
    for deployment in previous:
        runs = successful_runs(api, deployment)
        if run_url in runs:
            return deployment["id"], False
        if runs:
            reusable = deployment
    # Recover only the same immutable provider event AND same verified build.
    # Keep the original recording_run; the new success status logs the recovery run.
    deployment = (
        reusable
        if reusable is not None
        else api.request(
            "deployments",
            {
                "ref": sha,
                "environment": ENVIRONMENT,
                "task": "deploy",
                "auto_merge": False,
                "required_contexts": [],
                "production_environment": False,
                "transient_environment": False,
                "description": "Automatic Vercel deployment, verified byte for byte",
                "payload": {
                    "source": SOURCE,
                    "provider_url": provider["target_url"],
                    "deployed_at": provider["created_at"],
                    "recording_run": run_url,
                    "build_sha256": build_sha256,
                },
            },
        )
    )
    if (
        not isinstance(deployment, dict)
        or type(deployment.get("id")) is not int
        or deployment["id"] <= 0
    ):
        raise ValueError("GitHub returned no deployment receipt ID")
    api.request(
        f"deployments/{deployment['id']}/statuses",
        {
            "state": "success",
            "environment_url": check_live.DEFAULT_URL,
            "log_url": run_url,
            "auto_inactive": False,
            "description": "Vercel succeeded; every live file matches this commit",
        },
    )
    return deployment["id"], reusable is None


def frequency_report(api, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    weeks = [set() for _ in range(4)]
    invalid = 0
    query = urlencode({"environment": ENVIRONMENT, "task": "deploy"})
    for deployment in api.pages(f"deployments?{query}"):
        if not owned(deployment):
            invalid += int(marked(deployment))
            continue
        when = provider_time(deployment["payload"]["deployed_at"])
        age = (now - when).total_seconds()
        if 0 <= age < 28 * 86400 and was_successful(api, deployment):
            weeks[int(age // (7 * 86400))].add(deployment["sha"])
    lines = [
        "## Verified production deployment frequency",
        "",
        "Distinct deployed commits, by Vercel timestamp (target: at least 2 per week).",
        "",
        "| Days ago | Successful deployments |",
        "| --- | ---: |",
    ]
    lines += [f"| {i * 7}–{(i + 1) * 7} | {len(shas)} |" for i, shas in enumerate(weeks)]
    lines += [
        "",
        "Daily checks and reruns are not additional deployments. "
        "Missing historical records are not proof of a shipping cadence.",
    ]
    if len(weeks[0]) < 2:
        lines += ["", "The last seven days do not yet demonstrate multiple deployments per week."]
    if invalid:
        lines += ["", f"Warning: excluded {invalid} record(s) with invalid receipt evidence."]
    return lines


def validate_workflow(api, sha):
    """Cross-check workflow inputs with GitHub, not just mutable environment labels."""
    if os.environ.get("GITHUB_REF") != "refs/heads/main" or not re.fullmatch(SHA_PATTERN, sha):
        raise ValueError("Deployment recording is restricted to a pinned main workflow run")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    if not re.fullmatch(r"[1-9][0-9]*", run_id):
        raise ValueError("Invalid workflow run ID")
    current = api.request(f"actions/runs/{run_id}")
    validate_run(current, sha, int(run_id), completed=False)
    event_name = os.environ.get("GITHUB_EVENT_NAME")
    if current.get("event") != event_name:
        raise ValueError("Workflow trigger does not match GitHub run evidence")
    if event_name == "workflow_run":
        # Retain completed-event guards for intentional future callers. The
        # current canonical workflow does not enable this trigger.
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
        if not isinstance(event, dict):
            raise ValueError("Missing completed workflow event")
        upstream = event.get("workflow_run")
        if event.get("action") != "completed":
            raise ValueError("Only completed workflow runs may record deployments")
        upstream_id = upstream.get("id") if isinstance(upstream, dict) else None
        if type(upstream_id) is not int or upstream_id <= 0:
            raise ValueError("Invalid completed workflow run ID")
        validate_run(upstream, sha, upstream_id, completed=True)
        validate_run(api.request(f"actions/runs/{upstream_id}"), sha, upstream_id, completed=True)
    elif event_name not in {"push", "workflow_dispatch", "workflow_call"}:
        raise ValueError("Unapproved deployment recording event")
    comparison = api.request(f"compare/main...{sha}")
    if not isinstance(comparison, dict) or comparison.get("status") not in {"identical", "behind"}:
        raise ValueError("Candidate SHA is not reachable from main")
    return f"https://github.com/{REPOSITORY}/actions/runs/{run_id}"


def validate_run(run, sha, run_id, completed):
    if not isinstance(run, dict):
        raise ValueError("Missing workflow run evidence")
    repository = run.get("repository")
    head_repository = run.get("head_repository")
    if not (
        type(run.get("id")) is int
        and run["id"] == run_id
        and run.get("head_sha") == sha
        and run.get("head_branch") == "main"
        and isinstance(repository, dict)
        and repository.get("full_name") == REPOSITORY
        and isinstance(head_repository, dict)
        and head_repository.get("full_name") == REPOSITORY
        and isinstance(run.get("path"), str)
        and run["path"] in WORKFLOW_PATHS
        and isinstance(run.get("event"), str)
        and run["event"] in WORKFLOW_EVENTS
    ):
        raise ValueError("Workflow run is not the approved main candidate")
    if completed and (run.get("status") != "completed" or run.get("conclusion") != "success"):
        raise ValueError("Upstream workflow run must be completed successfully")


def emit(lines):
    print("\n".join(lines))
    check_live.summary(lines)


def report_frequency(api, receipt_recorded=False):
    try:
        lines = frequency_report(api)
    except (ValueError, OSError, subprocess.SubprocessError):
        if not receipt_recorded:
            raise
        # Receipt success is durable; a separate read failure is not a failed write.
        lines = [
            "Warning: receipt retained, but frequency history is unavailable; no cadence inferred."
        ]
    emit(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--wait", type=int, default=0)
    parser.add_argument(
        "--report", action="store_true", help="read-only four-week frequency report"
    )
    args = parser.parse_args(argv)
    if not 0 <= args.wait <= MAX_WAIT:
        parser.error(f"--wait must be between 0 and {MAX_WAIT}")
    api = GitHub(os.environ.get("GITHUB_REPOSITORY", REPOSITORY))
    if args.report:
        report_frequency(api)
        return 0
    sha = os.environ.get("GITHUB_SHA", "")
    run_url = validate_workflow(api, sha)
    path = check_live.ROOT / "site/build.json"
    build_bytes = path.read_bytes()
    local = json.loads(build_bytes)
    if not isinstance(local, dict) or local.get("commit") != sha:
        raise ValueError("Local build does not match the workflow SHA")
    deadline = time.monotonic() + args.wait
    provider = vercel_success(api, sha, args.wait)
    if check_live.main(
        [
            "--url",
            check_live.DEFAULT_URL,
            "--site",
            str(path.parent),
            "--wait",
            str(max(0, int(deadline - time.monotonic()))),
        ]
    ):
        return 1
    if path.read_bytes() != build_bytes:
        raise ValueError("Local build record changed during verification")
    status, live_bytes = check_live.fetch(f"{check_live.DEFAULT_URL}build.json")
    if status != 200 or live_bytes != build_bytes:
        raise ValueError("Live build.json bytes do not match the verified production build")
    # A new pending/failed provider event must not inherit an earlier success.
    if vercel_success(api, sha, 0) != provider:
        raise ValueError("Vercel status changed during byte verification; rerun")
    build_sha256 = hashlib.sha256(build_bytes).hexdigest()
    deployment_id, created = record(api, sha, provider, run_url, build_sha256)
    emit(
        [
            f"## Production deployment {deployment_id}",
            "",
            f"{'Recorded new receipt for' if created else 'Reused receipt for'} commit `{sha}`.",
            f"Vercel: {provider['target_url']}",
            f"Verification: {run_url}",
            f"Verified build.json SHA-256: `{build_sha256}`",
        ]
    )
    report_frequency(api, receipt_recorded=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        # Do not echo subprocess output, tokens, or caller-controlled endpoints.
        print(f"Deployment evidence failed ({type(error).__name__}).", file=sys.stderr)
        sys.exit(1)
