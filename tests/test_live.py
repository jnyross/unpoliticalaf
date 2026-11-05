"""The live-site check: matches an identical copy, catches a changed file or commit."""
import functools
import hashlib
import http.server
import importlib.util
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("check_live", ROOT / "scripts/check_live.py")
check_live = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_live)


def make_site(folder, commit="a" * 40, pages=None):
    pages = pages or {"index.html": "<p>home</p>", "life/2020.html": "<p>2020</p>"}
    files = {}
    for path, text in pages.items():
        p = Path(folder) / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        files[path] = hashlib.sha256(text.encode()).hexdigest()
    (Path(folder) / "build.json").write_text(json.dumps({"commit": commit, "files": files}))


class LiveCheck(unittest.TestCase):
    def setUp(self):
        self.live = tempfile.TemporaryDirectory()
        self.local = tempfile.TemporaryDirectory()
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=self.live.name)
        handler.log_message = lambda *a: None
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/"
        os.environ["NO_PROXY"] = os.environ["no_proxy"] = "127.0.0.1"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.live.cleanup()
        self.local.cleanup()

    def run_check(self):
        return check_live.main(["--url", self.url, "--site", self.local.name])

    def test_identical_copy_passes(self):
        make_site(self.live.name)
        make_site(self.local.name)
        self.assertEqual(self.run_check(), 0)

    def test_older_commit_fails(self):
        make_site(self.live.name, commit="b" * 40)
        make_site(self.local.name)
        self.assertEqual(self.run_check(), 1)

    def test_changed_page_fails(self):
        make_site(self.live.name)
        make_site(self.local.name)
        (Path(self.live.name) / "life/2020.html").write_text("<p>edited</p>")
        self.assertEqual(self.run_check(), 1)

    def test_missing_record_fails(self):
        make_site(self.local.name)
        self.assertEqual(self.run_check(), 1)

    def test_matching_flag_snapshots_pass(self):
        for folder in (self.live.name, self.local.name):
            make_site(folder)
            path = Path(folder) / "build.json"
            record = json.loads(path.read_text())
            record["feature_flags"] = {"chart_interactions": False}
            path.write_text(json.dumps(record))
        self.assertEqual(self.run_check(), 0)

    def test_different_flags_fail_even_if_page_hashes_match(self):
        make_site(self.live.name)
        make_site(self.local.name)
        path = Path(self.local.name) / "build.json"
        record = json.loads(path.read_text())
        record["feature_flags"] = {"chart_interactions": False}
        path.write_text(json.dumps(record))
        self.assertEqual(self.run_check(), 1)


class BuildRecord(unittest.TestCase):
    def test_record_lists_every_built_file(self):
        site = ROOT / "site"
        record = site / "build.json"
        if not record.exists():
            self.skipTest("run make build first")
        files = json.loads(record.read_text())["files"]
        built = {p.relative_to(site).as_posix() for p in site.rglob("*") if p.is_file()} - {"build.json"}
        self.assertEqual(set(files), built)
        self.assertEqual(files["index.html"], hashlib.sha256((site / "index.html").read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
