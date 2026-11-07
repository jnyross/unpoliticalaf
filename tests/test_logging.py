"""Output contracts for the real jobs, not just a synthetic printable callable."""

import contextlib
import csv
import io
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from builder import build, check
from builder.logging import LOGGER_NAME, configure_logging, get_logger, run_logged

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def diagnostics(monkeypatch, capsys):
    app = logging.getLogger(LOGGER_NAME)
    saved = app.handlers[:], app.level, app.propagate
    stream = io.StringIO()
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    with contextlib.redirect_stderr(stream):
        configure_logging()
        try:
            yield stream
        finally:
            for handler in app.handlers[:]:
                app.removeHandler(handler)
                handler.close()
            app.handlers[:], level, app.propagate = saved
            app.setLevel(level)


def records(stream):
    return [json.loads(line) for line in stream.getvalue().splitlines()]


def run_captured(main, logger, stream):
    # Pytest rebinds sys.stderr at the start of each test's call phase, after
    # fixture setup. Bind the real CLI handler during the call, not in setup.
    with contextlib.redirect_stderr(stream):
        return run_logged(main, logger)


def test_json_types_levels_namespace_and_idempotence(diagnostics):
    root = logging.getLogger()
    before = root.handlers[:], root.level
    with contextlib.redirect_stderr(diagnostics):
        configure_logging()
        configure_logging()
    get_logger("test").info(
        "source.downloaded",
        extra={"context": {"bytes": 42, "cached": False, "note": "£5\nline", "ids": ["one"]}},
    )
    (entry,) = records(diagnostics)
    assert entry["context"] == {"bytes": 42, "cached": False, "note": "£5\nline", "ids": ["one"]}
    assert datetime.fromisoformat(entry["timestamp"]).utcoffset().total_seconds() == 0
    assert entry["logger"] == "unpoliticalaf.test"
    assert (root.handlers, root.level) == before
    with contextlib.redirect_stderr(diagnostics):
        configure_logging("warning")
    get_logger("test").info("hidden")
    get_logger("test").warning("visible")
    assert [r["event"] for r in records(diagnostics)] == ["source.downloaded", "visible"]


@pytest.mark.parametrize("level", ["INFO", "WARNING", "CRITICAL"])
def test_original_machine_stdout_and_failure_status(diagnostics, capsys, monkeypatch, level):
    monkeypatch.setenv("LOG_LEVEL", level)
    for report in ('{"report":true}\n', "period,value\n2025,2\n"):

        def command():
            get_logger("test").warning("command.warning")
            print(report, end="")
            return 7

        assert run_logged(command, get_logger("test")) == 7
        output = capsys.readouterr().out
        assert output == report
        if report.startswith("{"):
            assert json.loads(output) == {"report": True}
        else:
            assert list(csv.DictReader(io.StringIO(output))) == [{"period": "2025", "value": "2"}]


@pytest.mark.parametrize("code,expected", [(None, None), (0, 0), (3, 3), ("stop", 1)])
def test_intentional_exit_codes(diagnostics, capsys, code, expected):
    def command():
        raise SystemExit(code)

    assert run_logged(command, get_logger("test")) == expected
    output = capsys.readouterr().err
    if isinstance(code, str):
        assert output.endswith("stop\n")


def test_sensitive_context_messages_and_exception_are_redacted(diagnostics):
    logger = get_logger("test")
    logger.info(
        "token=SYNTH_EVENT",
        extra={
            "context": {
                "api_key": "SYNTH_FIELD",
                "nested": [{"Authorization": "SYNTH_HEADER"}],
                "note": "password=SYNTH_PASSWORD Bearer SYNTH_BEARER person@example.test",
                "header_text": "Authorization: Bearer SYNTH_HEADER_TEXT",
                "url": "https://user:SYNTH_USER@example.test/file?token=SYNTH_QUERY#SYNTH_FRAGMENT",
            }
        },
    )

    def broken():
        raise ValueError("secret=SYNTH_EXCEPTION")

    assert run_captured(broken, logger, diagnostics) == 1
    output = diagnostics.getvalue()
    assert "SYNTH_" not in output
    assert "person@example.test" not in output
    assert "[REDACTED]" in output
    assert "ValueError" in records(diagnostics)[-1]["exception"]


def test_warning_and_text_exit_redact_synthetic_markers(diagnostics):
    get_logger("test").warning(
        "source.retry", extra={"context": {"error": "api_key=SYNTH_WARNING"}}
    )
    assert "SYNTH_" not in diagnostics.getvalue()

    def command():
        raise SystemExit("token=SYNTH_EXIT")

    assert run_captured(command, get_logger("test"), diagnostics) == 1
    assert "SYNTH_" not in diagnostics.getvalue()
    assert diagnostics.getvalue().endswith("token=[REDACTED]\n")


def test_broken_sink_and_unserializable_context_cannot_change_exit(
    diagnostics, monkeypatch, capsys
):
    attempts = []

    class BrokenSink:
        def write(self, value):
            attempts.append(value)
            raise OSError("token=SYNTH_SINK")

        def flush(self):
            raise OSError("token=SYNTH_FLUSH")

    monkeypatch.setattr(sys, "stderr", BrokenSink())

    def command():
        get_logger("test").info("command.started", extra={"context": {"unknown": object()}})
        raise ValueError("password=SYNTH_FAILURE")

    assert run_logged(command, get_logger("test")) == 1
    assert len(attempts) == 2
    assert all("SYNTH_" not in value for value in attempts)
    assert all(json.loads(value) for value in attempts)
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize(
    "args",
    [
        ["-m", "builder.build"],
        ["-m", "builder.check"],
        ["-m", "builder.check", "--axe"],
        ["scripts/fetch_sources.py"],
    ],
)
def test_actual_entrypoints_reject_invalid_log_level_before_job(args):
    result = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        env=dict(os.environ, LOG_LEVEL="SYNTH_INVALID"),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    (entry,) = [json.loads(line) for line in result.stderr.splitlines()]
    assert entry["event"] == "logging.configuration_failed"
    assert "SYNTH_INVALID" not in result.stderr


def test_fetch_argparse_help_and_errors_keep_their_exits():
    for arguments, expected in [(["--help"], 0), (["--unknown"], 2)]:
        result = subprocess.run(
            [sys.executable, "scripts/fetch_sources.py", *arguments],
            cwd=ROOT,
            env=dict(os.environ, LOG_LEVEL="INFO"),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == expected
        assert "usage:" in (result.stdout if expected == 0 else result.stderr)


def test_build_preserves_exact_reports_downloads_and_served_bytes(tmp_path, diagnostics, capsys):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets/icon.svg").write_text("<svg/>")
    facts = MagicMock()
    facts.__len__.return_value = 3
    facts.to_json.return_value = {"value": 2}
    num = SimpleNamespace(used={"a"}, absent={"missing"})
    with contextlib.ExitStack() as stack:
        for name, value in {
            "ROOT": tmp_path,
            "OUT": tmp_path / "site",
            "render": lambda: (facts, {}, {"index.html": "site"}, num),
        }.items():
            stack.enter_context(patch.object(build, name, value))
        stack.enter_context(patch.object(build.downloads, "FILES", {"data/a.csv": "a,b\n1,2\n"}))
        stack.enter_context(patch.object(build.version, "commit", return_value="a" * 40))
        snapshots = []
        for level in ("INFO", "CRITICAL"):
            stack.enter_context(patch.dict(os.environ, LOG_LEVEL=level))
            assert run_captured(build.main, get_logger("build"), diagnostics) == 0
            assert capsys.readouterr().out == (
                "Built 1 pages, 1 CSV downloads, 3 facts (1 shown) into site/\n"
                "1 requested figures do not exist and are shown as 'not available', e.g. ['missing']\n"
            )
            snapshots.append(
                {
                    p.relative_to(build.OUT): p.read_bytes()
                    for p in build.OUT.rglob("*")
                    if p.is_file()
                }
            )
        assert snapshots[0] == snapshots[1]
        assert json.loads(snapshots[0][Path("data/facts.json")])["facts"] == {"value": 2}
        assert snapshots[0][Path("data/a.csv")] == b"a,b\n1,2\n"
    assert any(
        r["event"] == "build.figures_unavailable" and r["level"] == "WARNING"
        for r in records(diagnostics)
    )


@pytest.mark.parametrize("axe", [False, True])
@pytest.mark.parametrize("failed", [False, True])
def test_check_preserves_every_report_and_bounded_problems(
    tmp_path, diagnostics, capsys, monkeypatch, axe, failed
):
    (tmp_path / "data").mkdir()
    (tmp_path / "data/facts.json").write_text("{}")
    monkeypatch.setattr(check, "SITE", tmp_path)
    monkeypatch.setattr(check, "problems", [f"problem {i}" for i in range(201)] if failed else [])
    monkeypatch.setattr(sys, "argv", ["check", "--axe"] if axe else ["check"])
    with contextlib.ExitStack() as stack:
        for name, value in {
            "check_facts": ({}, 10, 2),
            "check_structure": (3, 4),
            "check_pages": (8, 20),
            "check_explanations": 1,
            "check_downloads": 5,
            "check_findings": 6,
            "check_trend_titles": 7,
            "check_axis_notes": 9,
            "default_compare": "compare.html",
        }.items():
            stack.enter_context(patch.object(check, name, return_value=value))
        run_axe = stack.enter_context(patch.object(check, "run_axe"))
        assert run_captured(check.main, get_logger("check"), diagnostics) == int(failed)
        assert run_axe.call_count == int(axe)
    expected = (
        "Re-read 10 figures from source files; recalculated 2 derived figures.\n"
        "Checked 20 numbers on 8 pages (3 year pages, 4 comparison pages).\n"
        "Checked 5 CSV downloads beside the charts and tables.\n"
        "Checked that 6 chart headings state their finding in neutral words.\n"
        "Checked that 7 trend headings name every big rise and fall of their line.\n"
        "Checked that 9 line charts whose scale starts above zero say so.\n"
        "Matched 1 quoted explanations word for word against their sources.\n"
    )
    expected += (
        "\n201 problems:\n" + "".join(f" - problem {i}\n" for i in range(200))
        if failed
        else "All checks passed.\n"
    )
    assert capsys.readouterr().out == expected
    events = [record["event"] for record in records(diagnostics)]
    assert ("check.failed" if failed else "check.passed") in events


@pytest.mark.parametrize("level", ["INFO", "CRITICAL"])
def test_text_exit_and_crash_explain_failure_even_at_critical(
    diagnostics, capsys, monkeypatch, level
):
    monkeypatch.setenv("LOG_LEVEL", level)

    def intentional():
        raise SystemExit("Source files changed:\nsource.csv")

    assert run_logged(intentional, get_logger("test")) == 1
    assert capsys.readouterr().err.endswith("Source files changed:\nsource.csv\n")

    def broken():
        raise ValueError("password=SYNTH_CRASH")

    assert run_logged(broken, get_logger("test")) == 1
    output = capsys.readouterr()
    assert output.out == ""
    (entry,) = [json.loads(line) for line in output.err.splitlines()]
    assert entry["level"] == "CRITICAL"
    assert "ValueError" in entry["exception"]
    assert "SYNTH_" not in output.err


def test_closed_stderr_cannot_change_text_exit_status(diagnostics, monkeypatch):
    closed = io.StringIO()
    closed.close()
    monkeypatch.setattr(sys, "stderr", closed)

    def command():
        raise SystemExit("stop")

    assert run_logged(command, get_logger("test")) == 1


def test_formatter_failure_is_silent_and_does_not_change_success(diagnostics, capsys):
    from builder.logging import JsonFormatter

    def command():
        get_logger("test").info("success")
        return 0

    with patch.object(JsonFormatter, "format", side_effect=ValueError("token=SYNTH_FORMATTER")):
        assert run_logged(command, get_logger("test")) == 0
    assert capsys.readouterr() == ("", "")
