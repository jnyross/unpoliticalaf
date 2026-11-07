"""Post diff-scoped Python correctness/security reviews without executing PR code."""
from __future__ import annotations

import base64
import html
from http.client import HTTPSConnection
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

MAX_FILES = 100
MAX_FILE_BYTES = 1_000_000
MAX_TOTAL_BYTES = 5_000_000
MAX_COMMENTS = 50
RUFF_RULES = "E9,F63,F7,F82"


class ReviewError(RuntimeError):
    """An incomplete scan must not be reported as a clean review."""


class GitHub:
    def __init__(self, repository, token):
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", repository, flags=re.ASCII):
            raise ReviewError("Invalid repository name")
        self.repository = repository
        self.token = token

    def request(self, path, payload=None):
        # Fixed HTTPS host, with no redirects that could forward the token.
        connection = HTTPSConnection("api.github.com", timeout=30)
        try:
            connection.request(
                "POST" if payload is not None else "GET",
                f"/repos/{self.repository}/{path}",
                body=json.dumps(payload).encode() if payload is not None else None,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                    "Content-Type": "application/json",
                    "User-Agent": "unpoliticalaf-static-review",
                },
            )
            response = connection.getresponse()
            if response.status not in (200, 201):
                raise ReviewError(f"GitHub API request failed (HTTP {response.status})")
            return json.load(response)
        finally:
            connection.close()

    def pages(self, path):
        for page in range(1, 32):
            items = self.request(f"{path}?per_page=100&page={page}")
            yield from items
            if len(items) < 100:
                return
        raise ReviewError("GitHub pagination limit reached")


def added_lines(patch):
    """Return new-side added lines, not unchanged context or deleted lines."""
    result = set()
    line = None
    # Git patch records are LF-delimited. Python's splitlines() also splits
    # valid source characters such as form-feed and Unicode line separators.
    for text in patch.split("\n"):
        hunk = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", text)
        if hunk:
            line = int(hunk[1])
        elif line is not None:
            if text.startswith("+"):
                result.add(line)
                line += 1
            elif text.startswith(" "):
                line += 1
    return result


def run_json(module, arguments, directory):
    # The analyzers receive no token, repo configuration, source imports or shell.
    process = subprocess.run(
        [sys.executable, "-m", module, *arguments],
        cwd=directory,
        env={"PATH": os.environ.get("PATH", ""), "HOME": str(directory),
             "PYTHONIOENCODING": "utf-8"},
        capture_output=True, text=True, timeout=120, check=False,
    )
    if process.returncode not in (0, 1):
        raise ReviewError(f"{module} could not complete (exit {process.returncode})")
    try:
        return json.loads(process.stdout)
    except ValueError as error:
        raise ReviewError(f"{module} returned invalid JSON") from error


def analyze(directory, sources):
    """Map isolated numeric filenames back to paths and changed lines."""
    ruff = run_json("ruff", [
        "check", "--isolated", "--no-cache", "--ignore-noqa",
        "--select", RUFF_RULES, "--output-format", "json", str(directory),
    ], directory)
    bandit = run_json("bandit", [
        "-q", "-r", str(directory), "-f", "json", "-ll", "-ii", "--ignore-nosec",
    ], directory)
    if bandit.get("errors"):
        raise ReviewError("Bandit could not parse all Python files")
    findings = []
    for issue in ruff:
        path, changed = sources[Path(issue["filename"]).name]
        line = issue["location"]["row"]
        if line in changed:
            findings.append((path, line, f"Ruff {issue['code']}", issue["message"]))
    for issue in bandit["results"]:
        path, changed = sources[Path(issue["filename"]).name]
        # Multi-line calls can start on unchanged context.
        lines = set(issue.get("line_range") or [issue["line_number"]]) & changed
        if lines:
            rule = f"Bandit {issue['test_id']} ({issue['issue_severity'].lower()})"
            findings.append((path, min(lines), rule, issue["issue_text"]))
    return sorted(set(findings))


def scan(files, github):
    python_files = [f for f in files if f["filename"].endswith(".py")
                    and f["status"] != "removed"]
    if len(python_files) > MAX_FILES:
        raise ReviewError(f"More than {MAX_FILES} changed Python files; split this PR")
    if not python_files:
        return [], 0
    sources = {}
    total = 0
    with tempfile.TemporaryDirectory(prefix="pr-review-") as temporary:
        directory = Path(temporary)
        for index, file in enumerate(python_files):
            if "patch" not in file and file["additions"]:
                raise ReviewError("GitHub omitted a Python diff; cannot scope the review")
            changed = added_lines(file.get("patch", ""))
            if len(changed) != file["additions"]:
                raise ReviewError("GitHub truncated a Python diff; cannot scope the review")
            sha = file["sha"]
            if not re.fullmatch(r"[0-9a-f]{40}", sha):
                raise ReviewError("Invalid blob SHA")
            blob = github.request(f"git/blobs/{sha}")
            if blob["size"] > MAX_FILE_BYTES or blob["encoding"] != "base64":
                raise ReviewError("Python blob exceeds the size limit or is not base64")
            content = base64.b64decode(blob["content"])
            total += len(content)
            if len(content) > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
                raise ReviewError("Python content exceeds review size limits")
            # Never use an attacker-controlled path on disk (including symlinks).
            name = f"{index}.py"
            (directory / name).write_bytes(content)
            sources[name] = (file["filename"], changed)
        return analyze(directory, sources), len(python_files)


def safe_text(value, limit=500):
    text = str(value)
    escaped = html.escape(text[:limit]).replace("@", "@\u200b")
    shortened = len(text) > limit or len(escaped) > limit
    return escaped[:limit] + ("…" if shortened else "")


def review_payload(sha, marker, findings, scanned, file_count):
    comments = [
        {"path": path, "line": line, "side": "RIGHT",
         "body": f"**{safe_text(rule)}**: {safe_text(message)}"}
        for path, line, rule, message in findings[:MAX_COMMENTS]
    ]
    body = [
        marker,
        "## Automated Python code and security review",
        f"Reviewed commit `{sha}`: {scanned} Python file(s) out of "
        f"{file_count} changed file(s).",
        "",
        f"- Correctness: Ruff `{RUFF_RULES}` checks syntax, undefined names, "
        "invalid control flow and suspicious comparisons.",
        "- Security: Bandit checks for medium/high-severity issues with at least "
        "medium confidence, including injection and unsafe deserialization.",
        "- Findings are limited to added/modified lines; existing code is not "
        "reported as a new regression.",
        "",
    ]
    if findings:
        body.append(f"Found **{len(findings)}** potential issue(s):")
        for path, line, rule, message in findings[:MAX_COMMENTS]:
            body.append(f"- <code>{safe_text(path)}:{line}</code> "
                        f"**{safe_text(rule)}**: {safe_text(message)}")
        if len(findings) > MAX_COMMENTS:
            body.append(f"Only the first {MAX_COMMENTS} findings are shown; "
                        "fix these and push again for another review.")
    elif scanned:
        body.append("No selected correctness or security findings on changed Python lines.")
    else:
        body.append("No changed Python files to analyze. Non-Python changes were not assessed.")
    body.extend([
        "",
        "This is a static review, **not an approval**. It does not assess fiscal "
        "accuracy, data provenance, accessibility, behavior or non-Python code. "
        "Keep the existing checks and independent human/model review.",
    ])
    return {"commit_id": sha, "event": "COMMENT", "body": "\n".join(body),
            "comments": comments}


def review(github, number, expected_sha):
    pr = github.request(f"pulls/{number}")
    if pr["state"] != "open" or pr["draft"] or pr["head"]["sha"] != expected_sha:
        return False
    sha = pr["head"]["sha"]
    marker = f"<!-- automated-python-review:{sha}:{pr['base']['sha']} -->"
    reviews = github.pages(f"pulls/{number}/reviews")
    if any(r["user"]["login"] == "github-actions[bot]" and marker in (r["body"] or "")
           for r in reviews):
        return False
    files = list(github.pages(f"pulls/{number}/files"))
    if len(files) != pr["changed_files"]:
        raise ReviewError("GitHub did not return the complete changed-file list")
    # PR blobs belong to the shared repository network. Use the authorized base
    # client, not a fork repository outside GITHUB_TOKEN's permission scope.
    findings, scanned = scan(files, github)
    latest = github.request(f"pulls/{number}")
    if (latest["state"] != "open" or latest["draft"]
            or latest["head"]["sha"] != sha
            or latest["base"]["sha"] != pr["base"]["sha"]):
        return False
    github.request(f"pulls/{number}/reviews",
                   review_payload(sha, marker, findings, scanned, len(files)))
    return True


def main():
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    pr = event["pull_request"]
    github = GitHub(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])
    try:
        posted = review(github, int(pr["number"]), pr["head"]["sha"])
    except Exception:
        # Do not print tool output, source text, tokens or API response bodies.
        print("Review failed or was incomplete; no clean review was posted.", file=sys.stderr)
        raise SystemExit(1) from None
    print("Review posted." if posted else "Draft, closed, stale or already reviewed; no review posted.")


if __name__ == "__main__":
    main()
