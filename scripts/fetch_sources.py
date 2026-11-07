#!/usr/bin/env python3
"""Selectively refresh retained official bytes and receipts, failing closed.

Each accepted source is committed separately. A failed source keeps its previous
file and receipt; a mixed run exits nonzero without undoing accepted updates.
Run explicitly in an open-network environment, then review the Git diff and run
make verify. This command does not activate a workflow or publish anything.
"""

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import signal
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

if __package__:
    from .source_validation import validate_source
else:
    from source_validation import validate_source

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "fetched"
UA = {"User-Agent": "Mozilla/5.0 (Unpolitical source fetcher; +https://github.com/jnyross/unpoliticalaf)"}
REQUEST_TIMEOUT = 90
ATTEMPTS = 4


def get(url):
    """Return complete, identity-encoded HTTP bytes and actual response metadata."""
    if urllib.parse.urlsplit(url).scheme not in {"http", "https"}:
        raise ValueError("source URL must use HTTP(S)")
    for attempt in range(ATTEMPTS):
        try:
            request = urllib.request.Request(url, headers={**UA, "Accept-Encoding": "identity"})
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                if response.status != 200:
                    raise ValueError(f"expected HTTP 200, got {response.status}")
                if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                    raise ValueError("unexpected content encoding")
                body = response.read()
                length = response.headers.get("Content-Length")
                if length is not None and len(body) != int(length):
                    raise ValueError(f"incomplete response: {len(body)} bytes, expected {length}")
                return body, {
                    "url": response.geturl(),
                    "content_type": response.headers.get("Content-Type", ""),
                    "retrieved": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
        except Exception as error:
            if attempt == ATTEMPTS - 1:
                raise
            time.sleep(30 * (attempt + 1) if "429" in str(error) else 2 ** attempt)


def retained_path(name):
    path = OUT / name
    if not name or Path(name).is_absolute() or ".." in Path(name).parts:
        raise ValueError("unsafe retained filename")
    if path.resolve() == (OUT / "receipts.json").resolve() or not path.resolve().is_relative_to(OUT.resolve()):
        raise ValueError("unsafe retained filename")
    if any(parent.is_symlink() for parent in [path, *path.parents] if parent != OUT.parent):
        raise ValueError("symlink in retained path")
    return path


def promote(staged, path, receipts, receipt, source_id):
    """Rollback a failed pair replacement; defer normal termination mid-commit.

    POSIX has no two-file rename. The short critical section handles Python/I/O
    failures and SIGINT/SIGTERM, not power loss or SIGKILL. Writers serialize on
    the output directory; readers/builds must run after refresh has finished.
    """
    receipts_before = receipts.get(source_id)
    next_receipts = dict(receipts, **{source_id: receipt})
    staged_receipts = staged.parent / "receipts.json"
    staged_receipts.write_text(json.dumps(dict(sorted(next_receipts.items())), indent=1) + "\n")
    backup = staged.parent / "previous"
    if path.exists():
        shutil.copyfile(path, backup)
    for candidate in (staged, staged_receipts):
        with candidate.open("rb") as handle:
            os.fsync(handle.fileno())
    path.parent.mkdir(parents=True, exist_ok=True)
    interrupted = False

    def defer_interrupt(signum, frame):
        nonlocal interrupted
        interrupted = True

    handlers = {signum: signal.getsignal(signum)
                for signum in (signal.SIGINT, signal.SIGTERM)}
    try:
        for signum in handlers:
            signal.signal(signum, defer_interrupt)
        os.replace(staged, path)
        try:
            os.replace(staged_receipts, OUT / "receipts.json")
        except BaseException:
            if backup.exists():
                os.replace(backup, path)
            else:
                path.unlink()
            raise
        receipts[source_id] = receipt
        try:
            print("ok  ", source_id, json.dumps({
                "old_sha256": receipts_before["sha256"] if receipts_before else None,
                "new_sha256": receipt["sha256"], "bytes": receipt["bytes"],
                "url": receipt["url"], "retrieved": receipt["retrieved"],
            }), flush=True)
        except OSError as error:
            print("Accepted", source_id, "but could not write acquisition log:", error, file=sys.stderr)
    finally:
        for signum, handler in handlers.items():
            signal.signal(signum, handler)
    if interrupted:
        raise KeyboardInterrupt


def refresh_sources(manifest, receipts, only, refresh):
    failures = []
    accepted = 0
    skipped = 0
    for source in manifest["sources"]:
        source_id = source["id"]
        if only and source_id not in only:
            continue
        try:
            previous = receipts.get(source_id)
            old_path = retained_path(previous["file"]) if previous else None
            if previous:
                old_body = old_path.read_bytes()
                if len(old_body) != previous["bytes"] or hashlib.sha256(old_body).hexdigest() != previous["sha256"]:
                    raise ValueError("retained file/receipt mismatch; review before refreshing")
            if previous and not refresh and not only:
                skipped += 1
                continue
            time.sleep(3)  # be polite to official publishers
            url = source.get("url")
            name = source["file"]
            if "find" in source:
                page, page_response = get(source["page"])
                match = re.search(source["find"], page.decode("utf-8"))
                if not match:
                    raise ValueError("no link matching " + source["find"])
                url = urllib.parse.urljoin(page_response["url"], match.group(0).replace("&amp;", "&"))
                parsed = urllib.parse.urlparse(url)
                inner = urllib.parse.parse_qs(parsed.query).get("uri", [""])[0]
                name += Path(parsed.path).suffix or Path(inner).suffix or ".bin"
                if previous and url != previous.get("requested_url", previous["url"]):
                    raise ValueError("discovered URL changed vintage; review and pin the manifest first")
            path = retained_path(name)
            if previous and path != old_path:
                raise ValueError("retained filename changed; review migration first")
            owners = [key for key, value in receipts.items() if value["file"] == name and key != source_id]
            if owners:
                raise ValueError("retained filename belongs to another source: " + ", ".join(owners))
            if not previous and path.exists():
                raise ValueError("unreceipted existing file; refusing to overwrite")
            body, response = get(url)
            with tempfile.TemporaryDirectory(prefix=".refresh-", dir=OUT) as directory:
                staged = Path(directory) / ("download" + path.suffix)
                staged.write_bytes(body)
                validate_source(source_id, staged, response["content_type"], old_path)
                receipt = {
                    "url": response["url"], "file": name, "bytes": len(body),
                    "content_type": response["content_type"],
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "retrieved": response["retrieved"], "requested_url": url,
                }
                promote(staged, path, receipts, receipt, source_id)
            accepted += 1
        except KeyboardInterrupt:
            if receipts.get(source_id) is not previous:
                print("interrupted after accepting", source_id, flush=True)
            else:
                print("FAIL interrupted while refreshing", source_id, flush=True)
            raise
        except Exception as error:
            failures.append(source_id)
            print("FAIL", source_id, error, flush=True)
    outcome = "partial" if failures and accepted else "failed" if failures else "success"
    print(f"{outcome}: accepted={accepted} skipped={skipped} failed={len(failures)}; failures: {failures}")
    return 1 if failures else 0


def _run(only, refresh):
    try:
        manifest = json.loads((ROOT / "sources/manifest.json").read_text())
        ids = [source["id"] for source in manifest["sources"]]
        names = [source["file"] for source in manifest["sources"]]
        if len(set(ids)) != len(ids) or len(set(names)) != len(names):
            raise ValueError("duplicate source ID or retained filename")
        if only and only - set(ids):
            raise ValueError("unknown source IDs: " + ", ".join(sorted(only - set(ids))))
        OUT.mkdir(parents=True, exist_ok=True)
        # Lock the directory itself, avoiding a persistent extra tracked lock file.
        lock = os.open(OUT, os.O_RDONLY)
        try:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError("another source refresh is running") from None
            receipts_path = OUT / "receipts.json"
            receipts = json.loads(receipts_path.read_text()) if receipts_path.exists() else {}
            return refresh_sources(manifest, receipts, only, refresh)
        finally:
            os.close(lock)
    except KeyboardInterrupt:
        print("FAIL interrupted; completed sources remain accepted", file=sys.stderr)
        return 130
    except Exception as error:
        print("FAIL refresh:", error, file=sys.stderr)
        return 1


def _terminate(signum, frame):
    raise KeyboardInterrupt


def main(only=None, refresh=False):
    previous_handler = signal.signal(signal.SIGTERM, _terminate)
    try:
        return _run(only, refresh)
    finally:
        signal.signal(signal.SIGTERM, previous_handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="also reacquire existing retained sources")
    parser.add_argument("sources", nargs="*", help="source IDs; selected IDs are always reacquired")
    args = parser.parse_args()
    sys.exit(main(set(args.sources) or None, refresh=args.refresh))
