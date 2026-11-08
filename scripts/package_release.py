"""Package exact production bytes; optionally publish through a gated caller.

Packaging validates content, not CI or deployment. Only the caller can establish
that the commit passed independent checks and a real live-byte comparison.
"""

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from builder import feature_flags  # noqa: E402

ARTIFACT_NAMES = ("build.json", "site.tar.gz")
ASSET_NAMES = (*ARTIFACT_NAMES, "SHA256SUMS")
APPROVED_REPOSITORY = "jnyross/unpoliticalaf"
GH_SCRUBBED_VARIABLES = (
    "GH_HOST",
    "GH_DEBUG",
    "GH_REPO",
    "GH_ENTERPRISE_TOKEN",
    "GITHUB_ENTERPRISE_TOKEN",
)


def _validate_commit(commit):
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Release commit must be a full Git SHA")


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate build record key: {key}")
        result[key] = value
    return result


def _build_record(body, commit):
    record = json.loads(body, object_pairs_hook=_unique_pairs)
    if not isinstance(record, dict) or record.get("commit") != commit:
        raise ValueError("Build commit does not match the verified commit")
    flags = feature_flags.snapshot(record.get("feature_flags"))
    if flags != feature_flags.production({}):
        raise ValueError("Build feature flags do not match production")
    files = record.get("files")
    if not isinstance(files, dict) or not files or "build.json" in files:
        raise ValueError("Build record must list the site files, excluding itself")
    for name, digest in files.items():
        _validate_path(name)
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"Invalid build hash: {name}")
    return record


def _validate_path(name):
    # Paths are URL-relative POSIX spellings, not normalized local filenames.
    if (
        not isinstance(name, str)
        or not name
        or "\\" in name
        or any(ord(char) < 32 or ord(char) == 127 for char in name)
        or any(part in ("", ".", "..") for part in name.split("/"))
        or ":" in name
    ):
        raise ValueError(f"Unsafe manifest path: {name!r}")


def _site_bodies(site, commit):
    if site.is_symlink():
        raise ValueError("Symlinks are not release directories")
    actual = set()
    for path in site.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Symlinks are not release files: {path}")
        if path.is_file():
            actual.add(path.relative_to(site).as_posix())
        elif not path.is_dir():
            raise ValueError(f"Special files are not release files: {path}")
    record_bytes = (site / "build.json").read_bytes()
    record = _build_record(record_bytes, commit)
    if actual != set(record["files"]) | {"build.json"}:
        raise ValueError("Site files differ from the build record")
    bodies = {"build.json": record_bytes}
    for name, expected in sorted(record["files"].items()):
        body = (site / name).read_bytes()
        if hashlib.sha256(body).hexdigest() != expected:
            raise ValueError(f"Site file does not match its build hash: {name}")
        bodies[name] = body
    return bodies


def _checksums(bodies):
    return "".join(
        f"{hashlib.sha256(body).hexdigest()}  {name}\n" for name, body in sorted(bodies.items())
    ).encode("utf-8")


def _archive_bytes(bodies):
    raw = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode="w", format=tarfile.PAX_FORMAT) as tar:
            for name, body in sorted(bodies.items()):
                info = tarfile.TarInfo(name)
                info.size = len(body)
                info.mode = 0o644
                tar.addfile(info, io.BytesIO(body))
    return raw.getvalue()


def _validate_archive(archive_bytes, record_bytes, record):
    expected_names = sorted(set(record["files"]) | {"build.json"})
    bodies = {}
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tar:
        members = tar.getmembers()
        # Comparing the list, not just its set, rejects duplicates and disorder.
        if [member.name for member in members] != expected_names:
            raise ValueError("Archive members differ from the complete build manifest")
        for member in members:
            _validate_path(member.name)
            if not member.isfile():
                raise ValueError("Archive members must be regular files")
            body = tar.extractfile(member).read()
            if member.name == "build.json":
                if body != record_bytes:
                    raise ValueError("Archive build record differs from the release asset")
            elif hashlib.sha256(body).hexdigest() != record["files"][member.name]:
                raise ValueError("Archive file does not match its build hash")
            bodies[member.name] = body
    # Re-encoding also checks all tar/gzip metadata, hidden extension records,
    # trailing bytes and concatenated streams without extracting onto disk.
    if archive_bytes != _archive_bytes(bodies):
        raise ValueError("Archive is not in the normalized deterministic format")


def package(site, output, commit):
    """Validate all input before writing; archive the same bytes that were hashed."""
    _validate_commit(commit)
    site, output = Path(site).absolute(), Path(output).resolve()
    resolved_site = site.resolve()
    if output == resolved_site or resolved_site in output.parents:
        raise ValueError("Release output must be outside the site directory")
    bodies = _site_bodies(site, commit)
    output.mkdir(parents=True, exist_ok=True)
    if any((output / name).is_symlink() for name in ASSET_NAMES):
        raise ValueError("Symlinks are not release output files")
    archive = output / "site.tar.gz"
    archive.write_bytes(_archive_bytes(bodies))
    (output / "build.json").write_bytes(bodies["build.json"])
    artifacts = {name: (output / name).read_bytes() for name in ARTIFACT_NAMES}
    (output / "SHA256SUMS").write_bytes(_checksums(artifacts))
    return archive


def _gh(*args):
    # Keep intended local authentication/config, never inherited host routing,
    # enterprise credentials, repository overrides or HTTP debug output.
    environ = {key: value for key, value in os.environ.items() if key not in GH_SCRUBBED_VARIABLES}
    hostname = ("--hostname", "github.com") if args[0] == "api" else ()
    result = subprocess.run(
        ["gh", *args, *hostname], check=True, capture_output=True, env=environ, timeout=60
    )
    return result.stdout


def _gh_json(endpoint, paginate=False):
    options = ("--paginate", "--slurp") if paginate else ()
    result = json.loads(_gh("api", endpoint, *options))
    return [item for page in result for item in page] if paginate else result


def _find_release(repo, tag):
    releases = _gh_json(f"repos/{repo}/releases", paginate=True)
    matches = [item for item in releases if item["tag_name"] == tag]
    if len(matches) > 1:
        raise ValueError("Duplicate release tag")
    return matches[0] if matches else None


def _validate_tag(repo, tag, commit, required):
    refs = _gh_json(f"repos/{repo}/git/matching-refs/tags/{tag}")
    exact = [ref for ref in refs if ref["ref"] == f"refs/tags/{tag}"]
    if not exact:
        if required:
            raise ValueError("Published release tag is missing")
        return
    target = exact[0]["object"]
    seen = set()
    while target["type"] == "tag":
        sha = target["sha"]
        _validate_commit(sha)
        if sha in seen or len(seen) >= 16:
            raise ValueError("Release tag chain is invalid")
        seen.add(sha)
        target = _gh_json(f"repos/{repo}/git/tags/{sha}")["object"]
    if target["type"] != "commit" or target["sha"] != commit:
        raise ValueError("Release tag does not point to the verified commit")


def _validate_target(record, tag, commit):
    if record["tag_name"] != tag or record.get("target_commitish") != commit:
        raise ValueError("Release target does not match the verified commit")
    if type(record.get("draft")) is not bool:
        raise ValueError("Release draft status is invalid")


def _validate_assets(repo, record, bodies):
    assets = _gh_json(f"repos/{repo}/releases/{record['id']}/assets", paginate=True)
    names = [asset["name"] for asset in assets]
    if len(names) != len(set(names)) or set(names) - bodies.keys():
        raise ValueError("Unexpected or duplicate release assets")
    if not record["draft"] and set(names) != bodies.keys():
        raise ValueError("Published release assets are missing")
    for asset in assets:
        remote = _gh(
            "api",
            f"repos/{repo}/releases/assets/{asset['id']}",
            "-H",
            "Accept: application/octet-stream",
        )
        if hashlib.sha256(remote).digest() != hashlib.sha256(bodies[asset["name"]]).digest():
            raise ValueError(f"Release asset hash does not match: {asset['name']}")
    return set(names)


def _publish_inputs(environ):
    commit = environ.get("COMMIT")
    _validate_commit(commit)
    repo = environ.get("GITHUB_REPOSITORY", "")
    if repo != APPROVED_REPOSITORY:
        raise ValueError("GITHUB_REPOSITORY must be the approved repository")
    live_run = environ.get("LIVE_RUN", "")
    if not re.fullmatch(rf"https://github\.com/{re.escape(repo)}/actions/runs/[0-9]+", live_run):
        raise ValueError("LIVE_RUN must link the caller's actual verification run")
    if not environ.get("RUNNER_TEMP") or not environ.get("GITHUB_STEP_SUMMARY"):
        raise ValueError("Release temporary directory and step summary are required")
    output = Path(environ["RUNNER_TEMP"]) / "release"
    if any((output / name).is_symlink() for name in ASSET_NAMES):
        raise ValueError("Symlinks are not release assets")
    bodies = {name: (output / name).read_bytes() for name in ASSET_NAMES}
    if bodies["SHA256SUMS"] != _checksums({name: bodies[name] for name in ARTIFACT_NAMES}):
        raise ValueError("Local artifact checksums do not match")
    record = _build_record(bodies["build.json"], commit)
    _validate_archive(bodies["site.tar.gz"], bodies["build.json"], record)
    return commit, repo, live_run, output, bodies


def publish(environ=None):
    """Draft first; resume missing assets only, never overwrite remote bytes.

    The gated caller owns exact-candidate verification and per-SHA serialization.
    This function checks identities and bytes, not the truth of CI/live evidence.
    """
    environ = os.environ if environ is None else environ
    commit, repo, live_run, output, bodies = _publish_inputs(environ)
    tag = f"site-{commit}"
    record = _find_release(repo, tag)
    _validate_tag(repo, tag, commit, required=bool(record and not record["draft"]))
    if record is None:
        notes = output.parent / "release-notes.md"
        notes.write_text(
            f"Site built from commit `{commit}`.\n\n"
            f"Caller verification run: {live_run}\n\n"
            "Download all three assets and run `sha256sum -c SHA256SUMS`.\n"
            "Packaging alone is not proof of deployment or independent review.\n",
            encoding="utf-8",
        )
        _gh(
            "release",
            "create",
            tag,
            "--repo",
            repo,
            "--draft",
            "--latest=false",
            "--target",
            commit,
            "--title",
            f"Site {commit[:7]}",
            "--notes-file",
            str(notes),
        )
        record = _find_release(repo, tag)
        if record is None:
            raise ValueError("Created draft release cannot be found")
    _validate_target(record, tag, commit)
    present = _validate_assets(repo, record, bodies)
    if record["draft"]:
        for name in sorted(bodies.keys() - present):
            _gh("release", "upload", tag, str(output / name), "--repo", repo)
        record = _gh_json(f"repos/{repo}/releases/{record['id']}")
        _validate_target(record, tag, commit)
        if not record["draft"]:
            raise ValueError("Draft was published concurrently")
        if _validate_assets(repo, record, bodies) != bodies.keys():
            raise ValueError("Draft release assets are missing")
        _validate_tag(repo, tag, commit, required=False)
        _gh("release", "edit", tag, "--repo", repo, "--draft=false", "--latest=false")
        _validate_tag(repo, tag, commit, required=True)
    with Path(environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as summary:
        summary.write(record["html_url"] + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--site", type=Path, default=ROOT / "site")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--commit")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.publish:
            publish()
        else:
            if args.output is None or args.commit is None:
                parser.error("--output and --commit are required for packaging")
            archive = package(args.site, args.output, args.commit)
            print(f"Packaged {args.commit} into {archive}")
    except Exception as error:
        # API output, subprocess commands and local data may contain secrets or
        # attacker-controlled strings. Never replay them into CI logs.
        parser.exit(1, f"Release failed: {type(error).__name__}\n")


if __name__ == "__main__":
    main()
