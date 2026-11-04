"""Structured diagnostics and job integration, without network requests."""
import contextlib
import hashlib
import io
import json
import logging
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from builder.logging import LOGGER_NAME, configure_logging, get_logger, run_logged
from scripts import fetch_sources


class LogCapture(unittest.TestCase):
    def setUp(self):
        self.app = logging.getLogger(LOGGER_NAME)
        saved = self.app.handlers[:], self.app.level, self.app.propagate
        self.addCleanup(self.restore_logger, saved)
        self.env = patch.dict(os.environ, {"LOG_LEVEL": "INFO"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.stderr, self.stdout = io.StringIO(), io.StringIO()
        self.streams = contextlib.ExitStack()
        self.streams.enter_context(contextlib.redirect_stderr(self.stderr))
        self.streams.enter_context(contextlib.redirect_stdout(self.stdout))
        self.addCleanup(self.streams.close)
        configure_logging()

    def restore_logger(self, saved):
        for handler in self.app.handlers[:]:
            self.app.removeHandler(handler)
            handler.close()
        handlers, level, propagate = saved
        self.app.handlers[:] = handlers
        self.app.setLevel(level)
        self.app.propagate = propagate

    def records(self):
        return [json.loads(line) for line in self.stderr.getvalue().splitlines()]


class Logging(LogCapture):
    def test_typed_context_unicode_and_multiline_stay_one_json_line(self):
        get_logger("test").info("source.downloaded", extra={"context": {
            "bytes": 42, "cached": False, "note": "£5\nnext line", "ids": ["one"],
        }})
        record, = self.records()
        self.assertEqual(record["event"], "source.downloaded")
        self.assertEqual(record["level"], "INFO")
        self.assertEqual(record["logger"], "unpoliticalaf.test")
        self.assertEqual(record["context"], {
            "bytes": 42, "cached": False, "note": "£5\nnext line", "ids": ["one"],
        })
        self.assertEqual(datetime.fromisoformat(record["timestamp"]).utcoffset().total_seconds(), 0)
        self.assertEqual(self.stdout.getvalue(), "")

    def test_configuration_is_idempotent_and_does_not_change_root(self):
        root = logging.getLogger()
        before = root.handlers[:], root.level
        configure_logging()
        configure_logging()
        get_logger("test").info("once")
        self.assertEqual(len(self.records()), 1)
        self.assertEqual((root.handlers, root.level), before)

    def test_level_filter(self):
        os.environ["LOG_LEVEL"] = "warning"
        configure_logging()
        get_logger("test").info("hidden")
        get_logger("test").warning("visible")
        self.assertEqual([r["event"] for r in self.records()], ["visible"])

    def test_invalid_level_is_rejected(self):
        os.environ["LOG_LEVEL"] = "TYPO"
        with self.assertRaisesRegex(ValueError, "LOG_LEVEL"):
            configure_logging()

    def test_invalid_level_logs_json_and_does_not_run_job(self):
        os.environ["LOG_LEVEL"] = "TYPO"
        main = MagicMock()
        self.assertEqual(run_logged(main, get_logger("test")), 1)
        main.assert_not_called()
        record, = self.records()
        self.assertEqual(record["event"], "logging.configuration_failed")
        self.assertEqual(record["level"], "ERROR")
        self.assertIn("ValueError: LOG_LEVEL must be", record["exception"])

    def test_cli_entry_points_log_invalid_configuration_as_json(self):
        root = Path(__file__).resolve().parent.parent
        env = dict(os.environ, LOG_LEVEL="TYPO")
        for args in (["-m", "builder.build"], ["-m", "builder.check"], ["scripts/fetch_sources.py"]):
            with self.subTest(args=args):
                result = subprocess.run([sys.executable, *args], cwd=root, env=env,
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(result.stdout, "")
                record, = [json.loads(line) for line in result.stderr.splitlines()]
                self.assertEqual(record["event"], "logging.configuration_failed")
                self.assertIn("LOG_LEVEL", record["exception"])

    def test_exception_is_one_record_with_traceback_and_failure_status(self):
        def broken():
            raise ValueError("two\nlines")
        self.assertEqual(run_logged(broken, get_logger("test")), 1)
        record, = self.records()
        self.assertEqual(record["event"], "command.failed")
        self.assertEqual(record["level"], "ERROR")
        self.assertIn("Traceback", record["exception"])
        self.assertIn("ValueError: two\nlines", record["exception"])
        self.assertEqual(self.stdout.getvalue(), "")

    def test_intentional_exits_preserve_codes_and_log_text_reasons(self):
        for code, expected in [(None, None), (0, 0), (3, 3), ("source changed\nstop", 1)]:
            with self.subTest(code=code):
                self.stderr.seek(0)
                self.stderr.truncate()
                def stop():
                    raise SystemExit(code)
                self.assertEqual(run_logged(stop, get_logger("test")), expected)
                if expected:
                    self.assertEqual(self.records()[0]["context"]["reason"], str(code))
                else:
                    self.assertEqual(self.records(), [])

    def test_stdout_report_and_return_value_are_preserved(self):
        def report():
            print('{"report": true}')
            return 7
        self.assertEqual(run_logged(report, get_logger("test")), 7)
        self.assertEqual(self.stdout.getvalue(), '{"report": true}\n')


class JobLogging(LogCapture):
    def test_build_logs_counts_and_warnings_without_changing_output(self):
        from builder import build
        with tempfile.TemporaryDirectory() as folder, contextlib.ExitStack() as stack:
            root = Path(folder)
            (root / "assets").mkdir()
            (root / "assets/icon.svg").write_text("<svg/>")
            facts = MagicMock()
            facts.__len__.return_value = 3
            facts.to_json.return_value = {}
            num = SimpleNamespace(used={"a"}, absent={"missing"})
            stack.enter_context(patch.object(build, "ROOT", root))
            stack.enter_context(patch.object(build, "OUT", root / "site"))
            stack.enter_context(patch.object(build, "render", return_value=(facts, {}, {"index.html": "<p>site</p>"}, num)))
            stack.enter_context(patch.object(build.downloads, "FILES", {}))
            stack.enter_context(patch.object(build.version, "commit", return_value="a" * 40))
            self.assertEqual(run_logged(build.main, build.logger), 0)
            first = (root / "site/build.json").read_bytes()
            self.assertEqual(run_logged(build.main, build.logger), 0)
            self.assertEqual((root / "site/build.json").read_bytes(), first)
            self.assertEqual((root / "site/index.html").read_text(), "<p>site</p>")
        completed = next(r for r in self.records() if r["event"] == "build.completed")
        self.assertEqual(completed["context"]["facts"], 3)
        warning = next(r for r in self.records() if r["event"] == "build.figures_unavailable")
        self.assertEqual(warning["level"], "WARNING")
        self.assertEqual(warning["context"], {"count": 1, "examples": ["missing"]})
        self.assertEqual(self.stdout.getvalue(), "")

    def test_check_reports_counts_and_bounded_problems_with_failure_status(self):
        from builder import check
        with tempfile.TemporaryDirectory() as folder, contextlib.ExitStack() as stack:
            site = Path(folder)
            (site / "data").mkdir()
            (site / "data/facts.json").write_text("{}")
            stack.enter_context(patch.object(check, "SITE", site))
            stack.enter_context(patch.object(check, "problems", []))
            stack.enter_context(patch.object(check.sys, "argv", ["check"]))
            for name, result in {
                "check_facts": ({}, 10, 2), "check_structure": (3, 4),
                "check_pages": (8, 20), "check_explanations": 1, "check_downloads": 5,
                "check_findings": 6, "check_trend_titles": 7, "check_axis_notes": 9,
            }.items():
                stack.enter_context(patch.object(check, name, return_value=result))
            self.assertEqual(run_logged(check.main, check.logger), 0)
            self.assertEqual(self.records()[-1]["event"], "check.passed")
            check.problems.extend(f"problem {i}" for i in range(201))
            self.assertEqual(run_logged(check.main, check.logger), 1)
        records = self.records()
        self.assertEqual(sum(r["event"] == "check.problem" for r in records), 200)
        self.assertEqual(records[-1]["context"], {"problems": 201, "reported": 200})
        summary = next(r for r in records if r["event"] == "check.completed")
        self.assertEqual(summary["context"]["source_figures"], 10)
        self.assertEqual(summary["context"]["comparison_pages"], 4)

    def test_fetch_logs_success_failure_and_retains_receipts(self):
        with tempfile.TemporaryDirectory() as folder, contextlib.ExitStack() as stack:
            root = Path(folder)
            (root / "sources").mkdir()
            sources = [{"id": key, "file": key + ".csv", "url": "https://example.org/" + key}
                       for key in ("good", "bad")]
            (root / "sources/manifest.json").write_text(json.dumps({"sources": sources}))
            out = root / "data/fetched"
            stack.enter_context(patch.object(fetch_sources, "ROOT", root))
            stack.enter_context(patch.object(fetch_sources, "OUT", out))
            stack.enter_context(patch.object(fetch_sources.time, "sleep"))
            download = stack.enter_context(patch.object(fetch_sources, "get", side_effect=[
                (b"official data", "text/csv"), OSError("publisher unavailable"),
            ]))
            run_logged(fetch_sources.main, fetch_sources.logger)
            receipts = json.loads((out / "receipts.json").read_text())
            self.assertEqual(receipts["good"]["sha256"], hashlib.sha256(b"official data").hexdigest())
            self.assertNotIn("bad", receipts)
            self.assertEqual((out / "good.csv").read_bytes(), b"official data")
            download.reset_mock(side_effect=True)
            (root / "sources/manifest.json").write_text(json.dumps({"sources": sources[:1]}))
            run_logged(fetch_sources.main, fetch_sources.logger)
            download.assert_not_called()
            self.assertEqual(json.loads((out / "receipts.json").read_text()), receipts)
            self.assertEqual(self.records()[-1]["context"], {
                "downloaded": 0, "skipped": 1, "failures": [],
            })
        records = self.records()
        success = next(r for r in records if r["event"] == "source.downloaded")
        self.assertEqual(success["context"]["source_id"], "good")
        self.assertEqual(success["context"]["bytes"], 13)
        failure = next(r for r in records if r["event"] == "source.failed")
        self.assertEqual(failure["level"], "ERROR")
        self.assertIn("OSError: publisher unavailable", failure["exception"])
        summary = next(r for r in records if r["event"] == "fetch.completed")
        self.assertEqual(summary["context"], {"downloaded": 1, "skipped": 0, "failures": ["bad"]})
        self.assertEqual(self.stdout.getvalue(), "")

    def test_retry_diagnostics_preserve_backoff_and_attempt_limit(self):
        with patch.object(fetch_sources.urllib.request, "urlopen", side_effect=OSError("429 rate limited")) as request:
            with patch.object(fetch_sources.time, "sleep") as sleep:
                self.assertEqual(run_logged(lambda: fetch_sources.get("https://example.org"), fetch_sources.logger), 1)
        self.assertEqual(request.call_count, 4)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [30, 60, 90])
        retries = [r["context"] for r in self.records() if r["event"] == "source.retry"]
        self.assertEqual([r["attempt"] for r in retries], [1, 2, 3])
        self.assertEqual([r["delay_seconds"] for r in retries], [30, 60, 90])
        self.assertEqual(self.records()[-1]["event"], "command.failed")

    def test_retry_can_recover_without_an_error_record(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b"data"
        response.__enter__.return_value.headers = {"Content-Type": "text/csv"}
        with patch.object(fetch_sources.urllib.request, "urlopen", side_effect=[OSError("offline"), response]):
            with patch.object(fetch_sources.time, "sleep") as sleep:
                self.assertEqual(fetch_sources.get("https://example.org"), (b"data", "text/csv"))
        sleep.assert_called_once_with(1)
        retry, = self.records()
        self.assertEqual(retry["event"], "source.retry")
        self.assertEqual(retry["level"], "WARNING")


if __name__ == "__main__":
    unittest.main()
