"""Record real Vercel deployments only after the exact production build passes.

Run after make build in the main-only deployment workflow. --report is read-only
and also works locally with an authenticated gh CLI.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from urllib.parse import urlencode, urlparse

try:
    from . import check_live
except ImportError:
    import check_live

SOURCE = "verified-vercel-deployment"
ENVIRONMENT = "production"


class GitHub:
    def __init__(self, repository):
        self.prefix = f"repos/{repository}"

    def request(self, path, data=None):
        command = ["gh", "api", "--method", "POST" if data is not None else "GET",
                   f"{self.prefix}/{path}"]
        if data is not None:
            command += ["--input", "-"]
        result = subprocess.run(command, input=json.dumps(data) if data is not None else None,
                                text=True, capture_output=True, check=True)
        return json.loads(result.stdout)

    def pages(self, path):
        separator = "&" if "?" in path else "?"
        page = 1
        while True:
            rows = self.request(f"{path}{separator}per_page=100&page={page}")
            yield from rows
            if len(rows) < 100:
                return
            page += 1


def provider_time(value):
    if not isinstance(value, str):
        raise ValueError("Missing provider deployment timestamp")
    when = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if when.tzinfo is None:
        raise ValueError("Provider deployment timestamp needs a timezone")
    return when


def vercel_success(api, sha, wait):
    deadline = time.monotonic() + wait
    while True:
        combined = api.request(f"commits/{sha}/status")
        statuses = [s for s in combined["statuses"] if s["context"] == "Vercel"]
        status = statuses[0] if statuses else None
        if combined["sha"] != sha:
            raise ValueError("Vercel status is not for the checked-out commit")
        if status and status["state"] == "success":
            url = urlparse(status.get("target_url") or "")
            if url.scheme != "https" or url.hostname != "vercel.com" or not url.path.strip("/"):
                raise ValueError("Successful Vercel status has no Vercel deployment link")
            # Validate before retaining this as the actual deployment time.
            provider_time(status["created_at"])
            return status
        if status and status["state"] in {"failure", "error"}:
            raise ValueError(f"Vercel deployment {status['state']}; no deployment recorded")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("No successful Vercel deployment status before the deadline")
        time.sleep(min(15, remaining))


def owned(deployment):
    payload = deployment.get("payload")
    return (deployment.get("environment") == ENVIRONMENT
            and deployment.get("task") == "deploy"
            and isinstance(payload, dict) and payload.get("source") == SOURCE)


def was_successful(api, deployment):
    # A later deployment may have set the latest status to inactive. The earlier
    # success still counts, and a daily check must not create another deployment.
    return any(s["state"] == "success"
               for s in api.pages(f"deployments/{deployment['id']}/statuses"))


def record(api, sha, provider, run_url):
    query = urlencode({"sha": sha, "environment": ENVIRONMENT, "task": "deploy"})
    previous = [d for d in api.pages(f"deployments?{query}") if owned(d)]
    for deployment in previous:
        if was_successful(api, deployment):
            return deployment["id"], False
    # Reuse an incomplete record if a prior run stopped between these API writes.
    deployment = previous[0] if previous else api.request("deployments", {
        "ref": sha, "environment": ENVIRONMENT, "task": "deploy",
        "auto_merge": False, "required_contexts": [],
        "production_environment": True, "transient_environment": False,
        "description": "Automatic Vercel deployment, verified byte for byte",
        "payload": {"source": SOURCE, "provider_url": provider["target_url"],
                    "deployed_at": provider["created_at"], "recording_run": run_url},
    })
    api.request(f"deployments/{deployment['id']}/statuses", {
        "state": "success", "environment_url": check_live.DEFAULT_URL,
        "log_url": run_url, "auto_inactive": True,
        "description": "Vercel succeeded; every live file matches this commit",
    })
    return deployment["id"], True


def frequency_report(api, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    weeks = [set() for _ in range(4)]
    invalid = 0
    for deployment in api.pages("deployments?environment=production&task=deploy"):
        if not owned(deployment):
            continue
        try:
            when = provider_time(deployment["payload"].get("deployed_at"))
        except ValueError:
            invalid += 1
            continue
        age = (now - when).total_seconds()
        if 0 <= age < 28 * 86400 and was_successful(api, deployment):
            weeks[int(age // (7 * 86400))].add(deployment["sha"])
    lines = ["## Verified production deployment frequency", "",
             "Distinct deployed commits, by Vercel timestamp (target: at least 2 per week).", "",
             "| Days ago | Successful deployments |", "| --- | ---: |"]
    lines += [f"| {i * 7}–{(i + 1) * 7} | {len(shas)} |" for i, shas in enumerate(weeks)]
    lines += ["", "Daily checks and reruns are not additional deployments. "
              "Missing historical records are not proof of a shipping cadence."]
    if len(weeks[0]) < 2:
        lines += ["", "The last seven days do not yet demonstrate multiple deployments per week."]
    if invalid:
        lines += ["", f"Warning: excluded {invalid} record(s) with invalid provider timestamps."]
    return lines


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--wait", type=int, default=0)
    parser.add_argument("--report", action="store_true", help="read-only four-week frequency report")
    args = parser.parse_args(argv)
    if args.wait < 0:
        parser.error("--wait must not be negative")
    repository = os.environ.get("GITHUB_REPOSITORY", "jnyross/unpoliticalaf")
    api = GitHub(repository)
    if not args.report:
        sha = os.environ.get("GITHUB_SHA", "")
        if os.environ.get("GITHUB_REF") != "refs/heads/main" or not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError("Deployment recording is restricted to a pinned main workflow run")
        local = json.loads((check_live.ROOT / "site/build.json").read_text())
        if local["commit"] != sha:
            raise ValueError("Local build does not match the workflow SHA")
        run_id = os.environ["GITHUB_RUN_ID"]
        run_url = f"https://github.com/{repository}/actions/runs/{run_id}"
        deadline = time.monotonic() + args.wait
        provider = vercel_success(api, sha, args.wait)
        if check_live.main(["--wait", str(max(0, int(deadline - time.monotonic())))]):
            return 1
        deployment_id, created = record(api, sha, provider, run_url)
        lines = [f"## Production deployment {deployment_id}", "",
                 f"{'Recorded' if created else 'Already recorded'} commit `{sha}`.",
                 f"Vercel: {provider['target_url']}", f"Verification: {run_url}"]
        print("\n".join(lines))
        check_live.summary(lines)
    lines = frequency_report(api)
    print("\n".join(lines))
    check_live.summary(lines)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        print(f"Deployment evidence failed: {error}", file=sys.stderr)
        sys.exit(1)
