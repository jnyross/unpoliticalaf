"""Synthetic real-HTTP measurements, resets and original failure preservation."""

import contextlib
import functools
import hashlib
import http.server
import io
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from builder import feature_flags
from scripts import check_live


def samples(metrics):
    return {
        (sample.name, tuple(sorted(sample.labels.items()))): sample.value
        for family in metrics.registry.collect()
        for sample in family.samples
    }


class LiveMetrics(unittest.TestCase):
    def setUp(self):
        # CI flag-matrix overrides belong to the outer build, not this fixture.
        environment = patch.dict(os.environ)
        environment.start()
        self.addCleanup(environment.stop)
        os.environ.pop(feature_flags.ENV_VAR, None)

    def test_each_retry_is_measured_without_backoff_or_private_labels(self):
        metrics = check_live.LiveMetrics()
        with (
            patch.object(check_live.urllib.request, "urlopen", side_effect=TimeoutError("private")),
            patch.object(check_live.time, "sleep") as sleep,
            patch.object(check_live.time, "perf_counter", side_effect=[1, 1.25, 2, 2.5, 3, 4]),
        ):
            status, _ = check_live.fetch("https://example.invalid/?token=private", metrics=metrics)
        self.assertIsNone(status)
        self.assertEqual(sleep.call_args_list, [call(1), call(2)])
        values = samples(metrics)
        self.assertEqual(
            values[
                "unpolitical_live_http_request_duration_seconds_count",
                (("outcome", "network_error"),),
            ],
            3,
        )
        self.assertEqual(
            values[
                "unpolitical_live_http_request_duration_seconds_sum",
                (("outcome", "network_error"),),
            ],
            1.75,
        )
        self.assertEqual(values["unpolitical_live_http_response_size_bytes_sum", ()], 0)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "live.prom"
            metrics.finish(False, path)
            self.assertNotIn("private", path.read_text())
            self.assertNotIn("example.invalid", path.read_text())

    def test_http_error_is_not_retried_or_counted_as_network_error(self):
        metrics = check_live.LiveMetrics()
        body = io.BytesIO(b"private error body")
        error = check_live.urllib.error.HTTPError("https://example.invalid", 503, "", {}, body)
        with patch.object(check_live.urllib.request, "urlopen", side_effect=error) as request:
            self.assertEqual(
                check_live.fetch("https://example.invalid", metrics=metrics), (503, b"")
            )
        request.assert_called_once()
        self.assertTrue(body.closed)
        self.assertEqual(
            samples(metrics)[
                "unpolitical_live_http_request_duration_seconds_count", (("outcome", "5xx"),)
            ],
            1,
        )

    def test_retry_recovery_retains_both_outcomes(self):
        metrics = check_live.LiveMetrics()
        response = MagicMock()
        response.__enter__.return_value = response
        response.status, response.read.return_value = 200, b"OK"
        with (
            patch.object(
                check_live.urllib.request, "urlopen", side_effect=[TimeoutError(), response]
            ),
            patch.object(check_live.time, "sleep"),
        ):
            self.assertEqual(
                check_live.fetch("https://example.invalid", metrics=metrics), (200, b"OK")
            )
        values = samples(metrics)
        for outcome in ("network_error", "2xx"):
            self.assertEqual(
                values[
                    "unpolitical_live_http_request_duration_seconds_count", (("outcome", outcome),)
                ],
                1,
            )
        self.assertEqual(values["unpolitical_live_http_response_size_bytes_sum", ()], 2)

    def test_export_failure_preserves_every_original_exit_and_previous_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "live.prom"
            path.write_text("previous")
            for result in (0, 1, 2):
                with (
                    patch.object(check_live, "check", return_value=result),
                    patch("scripts.live_metrics.write_to_textfile", side_effect=PermissionError()),
                    contextlib.redirect_stderr(io.StringIO()) as stderr,
                ):
                    self.assertEqual(check_live.main(["--metrics-file", str(path)]), result)
                self.assertIn("could not write live metrics", stderr.getvalue())
                self.assertEqual(path.read_text(), "previous")

    def test_unexpected_check_exception_exports_failure_and_still_raises(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "live.prom"
            with patch.object(check_live, "check", side_effect=RuntimeError("failure")):
                with self.assertRaises(RuntimeError):
                    check_live.main(["--metrics-file", str(path)])
            self.assertIn("unpolitical_live_check_success 0.0", path.read_text())

    def test_metrics_cannot_be_inside_public_site_even_through_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            site = root / "site"
            site.mkdir()
            alias = root / "alias"
            alias.symlink_to(site, target_is_directory=True)
            for path in (site / "live.prom", alias / "live.prom"):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    check_live.main(["--site", str(site), "--metrics-file", str(path)])
                self.assertFalse(path.exists())

    def test_real_http_parallel_requests_and_per_run_reset(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            site = root / "site"
            site.mkdir()
            files = {"index.html": b"home", "other.html": b"other"}
            for name, body in files.items():
                (site / name).write_bytes(body)
            (site / "build.json").write_text(
                json.dumps(
                    {
                        "commit": "a" * 40,
                        "feature_flags": dict(feature_flags.production({})),
                        "files": {
                            name: hashlib.sha256(body).hexdigest() for name, body in files.items()
                        },
                    }
                )
            )
            handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(site))
            handler.log_message = lambda *args: None
            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            path = root / "metrics/live.prom"
            args = [
                "--site",
                str(site),
                "--url",
                f"http://127.0.0.1:{server.server_port}",
                "--metrics-file",
                str(path),
            ]
            try:
                self.assertEqual(check_live.main(args), 0)
                text = path.read_text()
                self.assertIn('outcome="2xx"} 3.0', text)
                self.assertIn("unpolitical_live_check_success 1.0", text)
                (site / "other.html").unlink()
                self.assertEqual(check_live.main(args), 1)
                text = path.read_text()
                self.assertIn('outcome="2xx"} 2.0', text)
                self.assertIn('outcome="4xx"} 1.0', text)
                self.assertIn("unpolitical_live_check_success 0.0", text)
                self.assertEqual(list(path.parent.iterdir()), [path])
                self.assertNotIn("index.html", text)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
