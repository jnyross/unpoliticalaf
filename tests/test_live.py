"""The live-site check: matches an identical copy, catches a changed file or commit."""
import contextlib
import functools
import hashlib
import http.server
import importlib.util
import io
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import call, patch

from prometheus_client.parser import text_string_to_metric_families

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("check_live", ROOT / "scripts/check_live.py")
check_live = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_live)


def samples(text):
    return {(sample.name, tuple(sorted(sample.labels.items()))): sample.value
            for family in text_string_to_metric_families(text) for sample in family.samples}


def value(data, name, **labels):
    return data[name, tuple(sorted(labels.items()))]


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
        self.metrics = tempfile.TemporaryDirectory()
        self.metrics_file = Path(self.metrics.name) / "nested/live.prom"
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
        self.metrics.cleanup()

    def run_check(self):
        return check_live.main(["--url", self.url, "--site", self.local.name,
                                "--metrics-file", str(self.metrics_file)])

    def read_metrics(self):
        return samples(self.metrics_file.read_text())

    def test_identical_copy_passes(self):
        make_site(self.live.name)
        make_site(self.local.name)
        self.assertEqual(self.run_check(), 0)
        data = self.read_metrics()
        self.assertEqual(value(data, "unpolitical_live_check_success"), 1)
        self.assertGreater(value(data, "unpolitical_live_check_duration_seconds"), 0)
        self.assertGreater(value(data, "unpolitical_live_check_completed_timestamp_seconds"), 0)
        self.assertEqual(value(data, "unpolitical_live_http_request_duration_seconds_count", outcome="2xx"), 3)
        self.assertEqual(value(data, "unpolitical_live_http_response_size_bytes_count"), 3)
        expected_bytes = sum(p.stat().st_size for p in Path(self.live.name).rglob("*") if p.is_file())
        self.assertEqual(value(data, "unpolitical_live_http_response_size_bytes_sum"), expected_bytes)
        self.assertEqual(list(self.metrics_file.parent.iterdir()), [self.metrics_file])
        self.assertNotIn(self.url, self.metrics_file.read_text())
        self.assertNotIn("index.html", self.metrics_file.read_text())
        self.assertEqual({p.relative_to(self.local.name).as_posix()
                          for p in Path(self.local.name).rglob("*") if p.is_file()},
                         {"index.html", "life/2020.html", "build.json"})

    def test_older_commit_fails(self):
        make_site(self.live.name, commit="b" * 40)
        make_site(self.local.name)
        self.assertEqual(self.run_check(), 1)
        self.assertEqual(value(self.read_metrics(), "unpolitical_live_check_success"), 0)

    def test_changed_page_fails(self):
        make_site(self.live.name)
        make_site(self.local.name)
        (Path(self.live.name) / "life/2020.html").write_text("<p>edited</p>")
        self.assertEqual(self.run_check(), 1)
        self.assertEqual(value(self.read_metrics(), "unpolitical_live_check_success"), 0)

    def test_missing_record_fails(self):
        make_site(self.local.name)
        self.assertEqual(self.run_check(), 1)
        data = self.read_metrics()
        self.assertEqual(value(data, "unpolitical_live_check_success"), 0)
        self.assertEqual(value(data, "unpolitical_live_http_request_duration_seconds_count", outcome="4xx"), 1)
        self.assertEqual(value(data, "unpolitical_live_http_response_size_bytes_sum"), 0)

    def test_missing_page_records_http_error_among_parallel_requests(self):
        make_site(self.live.name)
        make_site(self.local.name)
        (Path(self.live.name) / "life/2020.html").unlink()
        self.assertEqual(self.run_check(), 1)
        data = self.read_metrics()
        self.assertEqual(value(data, "unpolitical_live_http_request_duration_seconds_count", outcome="2xx"), 2)
        self.assertEqual(value(data, "unpolitical_live_http_request_duration_seconds_count", outcome="4xx"), 1)
        self.assertEqual(value(data, "unpolitical_live_check_success"), 0)

    def test_failed_run_replaces_success_and_resets_histograms(self):
        make_site(self.live.name)
        make_site(self.local.name)
        self.assertEqual(self.run_check(), 0)
        (Path(self.live.name) / "build.json").unlink()
        self.assertEqual(self.run_check(), 1)
        data = self.read_metrics()
        self.assertEqual(value(data, "unpolitical_live_check_success"), 0)
        self.assertEqual(value(data, "unpolitical_live_http_response_size_bytes_count"), 1)
        self.assertNotIn(("unpolitical_live_http_request_duration_seconds_count", (("outcome", "2xx"),)), data)

    def test_local_configuration_errors_still_export_failure(self):
        self.assertEqual(self.run_check(), 2)
        self.assertEqual(value(self.read_metrics(), "unpolitical_live_check_success"), 0)
        make_site(self.local.name, commit="unknown")
        self.assertEqual(self.run_check(), 2)
        self.assertEqual(value(self.read_metrics(), "unpolitical_live_check_success"), 0)

    def test_exception_still_exports_failure_and_is_not_swallowed(self):
        with patch.object(check_live, "check", side_effect=RuntimeError("check failed")):
            with self.assertRaisesRegex(RuntimeError, "check failed"):
                self.run_check()
        self.assertEqual(value(self.read_metrics(), "unpolitical_live_check_success"), 0)

    def test_export_failure_does_not_change_check_result_or_previous_file(self):
        self.metrics_file.parent.mkdir()
        self.metrics_file.write_text("previous snapshot\n")
        for result in (0, 1, 2):
            with self.subTest(result=result):
                with patch.object(check_live, "check", return_value=result), \
                     patch.object(check_live, "write_to_textfile", side_effect=PermissionError("read only")), \
                     contextlib.redirect_stderr(io.StringIO()) as stderr:
                    self.assertEqual(self.run_check(), result)
                self.assertIn("could not write live metrics", stderr.getvalue())
                self.assertEqual(self.metrics_file.read_text(), "previous snapshot\n")

    def test_metrics_cannot_be_written_to_public_build(self):
        path = Path(self.local.name) / "metrics.prom"
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            check_live.main(["--site", self.local.name, "--metrics-file", str(path)])
        self.assertEqual(raised.exception.code, 2)
        self.assertFalse(path.exists())


class RequestMetrics(unittest.TestCase):
    def test_retries_measure_each_attempt_without_backoff_or_error_text_bytes(self):
        metrics = check_live.LiveMetrics()
        error = check_live.urllib.error.URLError("private network error")
        with patch.object(check_live.urllib.request, "urlopen", side_effect=error), \
             patch.object(check_live.time, "sleep") as sleep, \
             patch.object(check_live.time, "perf_counter", side_effect=[10, 10.25, 20, 20.5, 30, 31]):
            status, body = check_live.fetch("https://example.invalid/private?token=secret", metrics=metrics)
        self.assertIsNone(status)
        self.assertIn(b"private network error", body)
        self.assertEqual(sleep.call_args_list, [call(1), call(2)])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "live.prom"
            metrics.finish(False, path)
            text = path.read_text()
        data = samples(text)
        self.assertEqual(value(data, "unpolitical_live_http_request_duration_seconds_count", outcome="network_error"), 3)
        self.assertEqual(value(data, "unpolitical_live_http_request_duration_seconds_sum", outcome="network_error"), 1.75)
        self.assertEqual(value(data, "unpolitical_live_http_request_duration_seconds_bucket",
                               outcome="network_error", le="0.5"), 2)
        self.assertEqual(value(data, "unpolitical_live_http_request_duration_seconds_bucket",
                               outcome="network_error", le="1.0"), 3)
        self.assertEqual(value(data, "unpolitical_live_http_response_size_bytes_sum"), 0)
        self.assertNotIn("private", text)
        self.assertNotIn("secret", text)

    def test_retries_can_recover_and_record_both_outcomes(self):
        metrics = check_live.LiveMetrics()
        response = unittest.mock.MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.read.return_value = b"OK"
        with patch.object(check_live.urllib.request, "urlopen",
                          side_effect=[TimeoutError(), response]), patch.object(check_live.time, "sleep"):
            self.assertEqual(check_live.fetch("https://example.invalid", metrics=metrics), (200, b"OK"))
        counts = {(s.name, tuple(sorted(s.labels.items()))): s.value
                  for metric in metrics.registry.collect() for s in metric.samples}
        self.assertGreaterEqual(value(counts, "unpolitical_live_http_request_duration_seconds_sum", outcome="network_error"), 0)
        self.assertEqual(value(counts, "unpolitical_live_http_request_duration_seconds_count", outcome="network_error"), 1)
        self.assertEqual(value(counts, "unpolitical_live_http_request_duration_seconds_count", outcome="2xx"), 1)
        self.assertEqual(value(counts, "unpolitical_live_http_response_size_bytes_sum"), 2)

    def test_server_error_is_not_retried_and_closes_the_error_response(self):
        metrics = check_live.LiveMetrics()
        body = io.BytesIO(b"unread private error body")
        error = check_live.urllib.error.HTTPError("https://example.invalid", 503, "unavailable", {}, body)
        with patch.object(check_live.urllib.request, "urlopen", side_effect=error) as request, \
             patch.object(check_live.time, "sleep") as sleep:
            self.assertEqual(check_live.fetch("https://example.invalid", metrics=metrics), (503, b""))
        request.assert_called_once()
        sleep.assert_not_called()
        self.assertTrue(body.closed)
        counts = {(s.name, tuple(sorted(s.labels.items()))): s.value
                  for metric in metrics.registry.collect() for s in metric.samples}
        self.assertEqual(value(counts, "unpolitical_live_http_request_duration_seconds_count", outcome="5xx"), 1)
        self.assertEqual(value(counts, "unpolitical_live_http_response_size_bytes_sum"), 0)


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
