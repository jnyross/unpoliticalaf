"""The live-site check: matches an identical copy, catches a changed file or commit."""
import functools
import hashlib
import http.server
import importlib.util
import json
import os
import shutil
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from builder import build, feature_flags, html
from builder.data import Facts

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


def make_production_site(folder, config):
    """Exercise the actual --production entry point without all fiscal rendering.

    Only the expensive page/data producers are replaced. Configuration loading,
    optional-script gating, output writing and build manifests are real.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "assets").mkdir()
        (root / "assets/icon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')

        def render(settings):
            facts = Facts()
            body = html.line_chart("Example", ["2020", "2021"], [("Rate", [1, 2], "a")], "units", kind="int")
            body += "<table><caption>Example data</caption><tr><th>Year</th><td>2020</td></tr></table>"
            output = html.page("index.html", "Example", body, folded=False, contents=False)
            return facts, {}, build.apply_feature_flags({"index.html": output}, settings), html.Num(facts)

        with patch.dict(os.environ, {}, clear=True), patch.object(feature_flags, "PRODUCTION_CONFIG", config):
            with patch.object(build, "ROOT", root), patch.object(build, "OUT", root / "site"):
                with patch.object(build, "render", side_effect=render), patch.object(build.downloads, "FILES", {}):
                    with patch.object(build.version, "commit", return_value="a" * 40):
                        if build.main(["--production"]) != 0:
                            raise AssertionError("Production fixture build failed")
                shutil.copytree(root / "site", folder, dirs_exist_ok=True)


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

    def test_nondefault_production_deployment_matches_independent_rebuild(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "production.json"
            config.write_text('{"chart_interactions":false,"sticky_navigation":false}')
            # Both builds read the trusted configuration, not the served manifest.
            make_production_site(self.live.name, config)
            make_production_site(self.local.name, config)
        expected = json.loads((Path(self.local.name) / "build.json").read_text())
        self.assertEqual(expected["feature_flags"], {"chart_interactions": False, "sticky_navigation": False})
        output = (Path(self.local.name) / "index.html").read_text()
        self.assertNotIn(html.CHART_JS, output)
        self.assertNotIn(html.BACKTOP_JS, output)
        self.assertIn("Example data", output)
        self.assertEqual(self.run_check(), 0)

    def test_remote_manifest_cannot_choose_expected_flags_or_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "production.json"
            config.write_text('{"chart_interactions":false,"sticky_navigation":false}')
            make_production_site(self.local.name, config)
            config.write_text('{"chart_interactions":true,"sticky_navigation":true}')
            make_production_site(self.live.name, config)
        self.assertEqual(self.run_check(), 1)
        # Even lying about the settings cannot make different served bytes pass.
        path = Path(self.live.name) / "build.json"
        remote = json.loads(path.read_text())
        remote["feature_flags"] = {"chart_interactions": False, "sticky_navigation": False}
        path.write_text(json.dumps(remote))
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
