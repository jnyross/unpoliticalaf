"""Real HTTP refresh failures must leave the retained file/receipt pair intact."""

import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import pytest

from scripts import fetch_sources


@pytest.fixture
def http_origin():
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            if self.path == "/error":
                self.send_error(503)
                return
            if self.path == "/redirect":
                self.send_response(302)
                self.send_header("Location", "/good")
                self.end_headers()
                return
            if self.path == "/page":
                body = b'<html><title>Publisher</title><a href="/good.csv">Table</a></html>'
            else:
                body = (
                    b"<html><title>Access denied</title></html>"
                    if self.path == "/invalid"
                    else b"period,value\n2025,2\n"
                )
            self.send_response(200)
            self.send_header("Content-Type", "text/html" if self.path == "/invalid" else "text/csv")
            self.send_header(
                "Content-Length", str(len(body) + (100 if self.path == "/truncated" else 0))
            )
            self.end_headers()
            if self.path == "/timeout":
                threading.Event().wait(0.3)
            if self.path == "/interrupt":
                threading.Event().wait(1)
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 3181), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        yield "http://127.0.0.1:3181", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def retained_sources(tmp_path, monkeypatch, origin, routes):
    out = tmp_path / "data/fetched"
    out.mkdir(parents=True)
    (tmp_path / "sources").mkdir()
    sources = []
    receipts = {}
    for source_id, route in routes.items():
        name = source_id + ".csv"
        body = b"period,value\n2025,1\n"
        (out / name).write_bytes(body)
        receipts[source_id] = {
            "url": origin + route,
            "file": name,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "retrieved": "2026-01-01T00:00:00Z",
            "content_type": "text/csv",
        }
        sources.append({"id": source_id, "url": origin + route, "file": name})
    (tmp_path / "sources/manifest.json").write_text(json.dumps({"sources": sources}))
    (out / "receipts.json").write_text(json.dumps(receipts))
    monkeypatch.setattr(fetch_sources, "ROOT", tmp_path)
    monkeypatch.setattr(fetch_sources, "OUT", out)
    monkeypatch.setattr(fetch_sources.time, "sleep", lambda _: None)
    monkeypatch.setattr(fetch_sources, "ATTEMPTS", 1)
    monkeypatch.setattr(fetch_sources, "REQUEST_TIMEOUT", 0.1)
    return out, receipts


@pytest.mark.parametrize("route", ["/error", "/invalid", "/truncated", "/timeout"])
def test_real_http_failure_preserves_last_good_pair(tmp_path, monkeypatch, http_origin, route):
    origin, requests = http_origin
    out, _ = retained_sources(tmp_path, monkeypatch, origin, {"failed": route})
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    assert fetch_sources.main({"failed"}, refresh=True) == 1
    assert {p.name: p.read_bytes() for p in out.iterdir()} == before
    assert route in requests
    print(f"observed {requests}; retained pair unchanged for {route}")


def test_real_http_mixed_result_is_nonzero_and_keeps_matching_pairs(
    tmp_path, monkeypatch, http_origin, capsys
):
    origin, requests = http_origin
    out, before = retained_sources(
        tmp_path, monkeypatch, origin, {"good": "/good", "bad": "/invalid"}
    )
    assert fetch_sources.main({"good", "bad"}, refresh=True) == 1
    after = json.loads((out / "receipts.json").read_text())
    assert after["bad"] == before["bad"]
    assert (out / "bad.csv").read_bytes() == b"period,value\n2025,1\n"
    assert (out / "good.csv").read_bytes() == b"period,value\n2025,2\n"
    assert after["good"]["sha256"] == hashlib.sha256((out / "good.csv").read_bytes()).hexdigest()
    assert "partial" in capsys.readouterr().out.lower()
    assert requests == ["/good", "/invalid"]


def test_redirect_receipt_uses_actual_url_bytes_and_time(tmp_path, monkeypatch, http_origin):
    from datetime import datetime, timezone

    origin, requests = http_origin
    out, _ = retained_sources(tmp_path, monkeypatch, origin, {"good": "/redirect"})
    started = datetime.now(timezone.utc).replace(microsecond=0)
    assert fetch_sources.main({"good"}) == 0
    receipt = json.loads((out / "receipts.json").read_text())["good"]
    body = (out / receipt["file"]).read_bytes()
    assert receipt["requested_url"] == origin + "/redirect"
    assert receipt["url"] == origin + "/good"
    assert receipt["bytes"] == len(body)
    assert receipt["sha256"] == hashlib.sha256(body).hexdigest()
    # Python 3.10's ISO parser requires an explicit UTC offset rather than Z.
    retrieved = datetime.fromisoformat(receipt["retrieved"].replace("Z", "+00:00"))
    assert started <= retrieved <= datetime.now(timezone.utc)
    assert requests == ["/redirect", "/good"]


def test_receipt_promotion_failure_restores_old_file(tmp_path, monkeypatch, http_origin):
    origin, _ = http_origin
    out, _ = retained_sources(tmp_path, monkeypatch, origin, {"good": "/good"})
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    replace = os.replace

    def fail_receipt(source, destination):
        if destination == out / "receipts.json":
            raise OSError("simulated receipt rename failure")
        return replace(source, destination)

    monkeypatch.setattr(fetch_sources.os, "replace", fail_receipt)
    assert fetch_sources.main({"good"}) == 1
    assert {p.name: p.read_bytes() for p in out.iterdir()} == before


def test_interrupt_before_promotion_cleans_staging(tmp_path, monkeypatch, http_origin):
    origin, _ = http_origin
    out, _ = retained_sources(tmp_path, monkeypatch, origin, {"good": "/good"})
    before = {p.name: p.read_bytes() for p in out.iterdir()}

    def interrupt(*args):
        raise KeyboardInterrupt

    monkeypatch.setattr(fetch_sources, "validate_source", interrupt)
    assert fetch_sources.main({"good"}) == 130
    assert {p.name: p.read_bytes() for p in out.iterdir()} == before


def test_unknown_id_and_retained_corruption_fail_without_http(tmp_path, monkeypatch, http_origin):
    origin, requests = http_origin
    out, _ = retained_sources(tmp_path, monkeypatch, origin, {"good": "/good"})
    assert fetch_sources.main({"typo"}) == 1
    (out / "good.csv").write_bytes(b"corrupted")
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    assert fetch_sources.main({"good"}) == 1
    assert not requests
    assert {p.name: p.read_bytes() for p in out.iterdir()} == before


def test_concurrent_writer_cannot_enter(tmp_path, monkeypatch, http_origin):
    import fcntl

    origin, requests = http_origin
    out, _ = retained_sources(tmp_path, monkeypatch, origin, {"good": "/good"})
    descriptor = os.open(out, os.O_RDONLY)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert fetch_sources.main({"good"}) == 1
        assert not requests
    finally:
        os.close(descriptor)


@pytest.mark.parametrize("route,terminate", [("/invalid", False), ("/interrupt", True)])
def test_actual_cli_exits_nonzero_and_keeps_last_good(
    tmp_path, monkeypatch, http_origin, route, terminate
):
    origin, requests = http_origin
    out, _ = retained_sources(tmp_path, monkeypatch, origin, {"failed": route})
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    original = os.path.dirname(fetch_sources.__file__)
    for name in ("fetch_sources.py", "source_validation.py"):
        shutil.copyfile(os.path.join(original, name), scripts / name)
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    process = subprocess.Popen(
        [sys.executable, str(scripts / "fetch_sources.py"), "failed"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        if terminate:
            # Wait for the server-observed request, not a guessed download delay.
            for _ in range(200):
                if requests:
                    break
                threading.Event().wait(0.05)
            assert requests == [route]
            process.send_signal(signal.SIGTERM)
        output, _ = process.communicate(timeout=20)
        assert process.returncode == (130 if terminate else 1), output
        assert {p.name: p.read_bytes() for p in out.iterdir()} == before
        print(
            f"CLI route={route} exit={process.returncode} requests={requests}; pair unchanged; {output}"
        )
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def test_sigterm_during_staged_validation_cleans_up(tmp_path, monkeypatch, http_origin):
    origin, requests = http_origin
    out, _ = retained_sources(tmp_path, monkeypatch, origin, {"good": "/good"})
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    marker = tmp_path / "validating"
    # Run the actual module/main in a separate process and pause only validation.
    code = (
        "import pathlib, threading\n"
        "from scripts import fetch_sources as fetch\n"
        f"fetch.ROOT=pathlib.Path({str(tmp_path)!r})\n"
        f"fetch.OUT=pathlib.Path({str(out)!r})\n"
        "fetch.time.sleep=lambda _: None\n"
        "def validate(*args):\n"
        f"    pathlib.Path({str(marker)!r}).touch()\n"
        "    threading.Event().wait(20)\n"
        "fetch.validate_source=validate\n"
        "raise SystemExit(fetch.main({'good'}))\n"
    )
    process = subprocess.Popen(
        [sys.executable, "-c", code], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    try:
        for _ in range(200):
            if marker.exists():
                break
            threading.Event().wait(0.05)
        assert marker.exists()
        process.send_signal(signal.SIGTERM)
        output, _ = process.communicate(timeout=5)
        assert process.returncode == 130, output
        assert "interrupted" in output
        assert requests == ["/good"]
        assert {p.name: p.read_bytes() for p in out.iterdir()} == before
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def test_sigterm_during_commit_is_deferred_until_pair_matches(
    tmp_path, monkeypatch, http_origin, capsys
):
    origin, _ = http_origin
    out, _ = retained_sources(tmp_path, monkeypatch, origin, {"good": "/good"})
    replace = os.replace

    def terminate_after_data(source, destination):
        replace(source, destination)
        if destination == out / "good.csv":
            os.kill(os.getpid(), signal.SIGTERM)

    monkeypatch.setattr(fetch_sources.os, "replace", terminate_after_data)
    assert fetch_sources.main({"good"}) == 130
    receipt = json.loads((out / "receipts.json").read_text())["good"]
    assert receipt["sha256"] == hashlib.sha256((out / "good.csv").read_bytes()).hexdigest()
    assert (out / "good.csv").read_bytes() == b"period,value\n2025,2\n"
    assert sorted(p.name for p in out.iterdir()) == ["good.csv", "receipts.json"]
    assert "ok   good" in capsys.readouterr().out


@pytest.mark.parametrize("changed_link", [False, True])
def test_discovery_preserves_suffix_and_rejects_new_vintage(
    tmp_path, monkeypatch, http_origin, changed_link
):
    origin, requests = http_origin
    out, receipts = retained_sources(tmp_path, monkeypatch, origin, {"found": "/good.csv"})
    if changed_link:
        receipts["found"]["url"] = origin + "/old.csv"
    (out / "receipts.json").write_text(json.dumps(receipts))
    manifest = {
        "sources": [
            {"id": "found", "page": origin + "/page", "find": r"/good\.csv", "file": "found"}
        ]
    }
    (tmp_path / "sources/manifest.json").write_text(json.dumps(manifest))
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    assert fetch_sources.main({"found"}) == (1 if changed_link else 0)
    if changed_link:
        assert {p.name: p.read_bytes() for p in out.iterdir()} == before
        assert requests == ["/page"]
    else:
        assert requests == ["/page", "/good.csv"]
        assert json.loads((out / "receipts.json").read_text())["found"]["file"] == "found.csv"


@pytest.mark.parametrize("mode", ["filename", "unreceipted", "owner", "traversal"])
def test_filename_ownership_guards_fail_before_download(tmp_path, monkeypatch, http_origin, mode):
    origin, requests = http_origin
    out, receipts = retained_sources(tmp_path, monkeypatch, origin, {"good": "/good"})
    manifest_path = tmp_path / "sources/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if mode in {"filename", "traversal"}:
        manifest["sources"][0]["file"] = "different.csv" if mode == "filename" else "../escape.csv"
        manifest_path.write_text(json.dumps(manifest))
    else:
        previous = receipts.pop("good")
        if mode == "owner":
            receipts["other"] = previous
        (out / "receipts.json").write_text(json.dumps(receipts))
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    assert fetch_sources.main({"good"}) == 1
    assert {p.name: p.read_bytes() for p in out.iterdir()} == before
    assert not requests


def test_new_source_receipt_failure_removes_uncommitted_file(tmp_path, monkeypatch, http_origin):
    origin, _ = http_origin
    out, _ = retained_sources(tmp_path, monkeypatch, origin, {"new": "/good"})
    (out / "new.csv").unlink()
    (out / "receipts.json").write_text("{}")
    before = (out / "receipts.json").read_bytes()
    replace = os.replace

    def fail_receipt(source, destination):
        if destination == out / "receipts.json":
            raise OSError("receipt write failed")
        replace(source, destination)

    monkeypatch.setattr(fetch_sources.os, "replace", fail_receipt)
    assert fetch_sources.main({"new"}) == 1
    assert not (out / "new.csv").exists()
    assert (out / "receipts.json").read_bytes() == before
