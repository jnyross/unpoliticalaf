"""Dependency-free, best-effort JSON diagnostics, separate from CLI reports."""

import json
import logging
import os
import re
import sys
import traceback
from collections.abc import Callable
from datetime import datetime, timezone
from typing import TextIO, TypeAlias
from urllib.parse import urlsplit, urlunsplit

LOGGER_NAME = "unpoliticalaf"
REDACTED = "[REDACTED]"
JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
_SENSITIVE_KEY = re.compile(
    r"password|passwd|secret|token|api.?key|authorization|cookie|credential", re.I
)
_URL = re.compile(r"https?://[^\s<>\"']+", re.I)
_ASSIGNMENT = re.compile(
    r"""(?i)((?:password|passwd|secret|token|api[_-]?key|authorization|cookie|credential)"""
    r"""[\w-]*["']?\s*[:=]\s*)(?:"[^"]*"|'[^']*'|[^\s,;}\]]+)"""
)
_BEARER = re.compile(r"(?i)\b(Bearer|Basic)\s+[a-z0-9+/_.=:-]+")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", re.I)


def _safe_url(match: re.Match[str]) -> str:
    try:
        url = urlsplit(match.group())
        host = url.netloc.rsplit("@", 1)[-1]
        return urlunsplit((url.scheme, host, url.path, "", "")) + (
            REDACTED if "@" in url.netloc or url.query or url.fragment else ""
        )
    except ValueError:
        return REDACTED


def redact_text(value: str) -> str:
    """Redact credential assignments, auth headers, URL credentials/query and email."""
    value = _URL.sub(_safe_url, value)
    value = _BEARER.sub(lambda match: match[1] + " " + REDACTED, value)
    value = _ASSIGNMENT.sub(lambda match: match[1] + REDACTED, value)
    return _EMAIL.sub(REDACTED, value)


def _safe_value(value: object, depth: int = 0) -> JsonValue:
    if depth > 10:
        return "[TRUNCATED]"
    if isinstance(value, str):
        return redact_text(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, dict):
        return {
            redact_text(key) if isinstance(key, str) else "[UNSUPPORTED_KEY]": (
                REDACTED
                if isinstance(key, str) and _SENSITIVE_KEY.search(key)
                else _safe_value(item, depth + 1)
            )
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list)):
        return [_safe_value(item, depth + 1) for item in value]
    # Never invoke arbitrary __str__/__repr__ methods on diagnostic context.
    return "[UNSUPPORTED]"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(
                timespec="milliseconds"
            ),
            "level": record.levelname,
            "logger": redact_text(record.name),
            "event": redact_text(record.getMessage()),
            "context": _safe_value(getattr(record, "context", {})),
        }
        if record.exc_info:
            error_type, error, tb = record.exc_info
            # Retain stack locations, but not source lines or locals (which can
            # themselves contain secrets). Redact the exception message as well.
            frames = traceback.extract_tb(tb)
            stack = "\n".join(
                f'  File "{frame.filename}", line {frame.lineno}, in {frame.name}'
                for frame in frames
            )
            name = error_type.__name__ if error_type else "Exception"
            entry["exception"] = redact_text(
                f"Traceback (most recent call last):\n{stack}\n{name}: {error}"
            )
        return json.dumps(entry, ensure_ascii=False, allow_nan=False)


class DiagnosticHandler(logging.Handler):
    def __init__(self, stream: TextIO) -> None:
        super().__init__()
        self.stream = stream

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.stream.write(self.format(record) + "\n")
            self.stream.flush()
        except Exception:
            # A failed sink/formatter must not change a job result, or dump raw
            # LogRecord/exception data through logging.handleError's fallback.
            pass


def get_logger(component: str) -> logging.Logger:
    return logging.getLogger(f"{LOGGER_NAME}.{component}")


def configure_logging(level: str | None = None) -> None:
    """Configure only our namespace; repeated calls never duplicate records."""
    level = (level if level is not None else os.environ.get("LOG_LEVEL", "INFO")).upper()
    if level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        raise ValueError("LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR or CRITICAL")
    logger = logging.getLogger(LOGGER_NAME)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    handler = DiagnosticHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False


def run_logged(main: Callable[[], int | None], logger: logging.Logger) -> int | None:
    """Run a CLI without changing returned statuses or intentional exit codes."""
    try:
        configure_logging()
    except ValueError:
        configure_logging("INFO")
        logger.error("logging.configuration_failed")
        return 1
    try:
        result = main()
        if result:
            logger.error("command.failed", extra={"context": {"exit_code": result}})
        return result
    except SystemExit as error:
        if error.code not in (None, 0):
            logger.error("command.failed", extra={"context": {"reason": str(error.code)}})
        if error.code is not None and not isinstance(error.code, int):
            try:
                print(redact_text(str(error.code)), file=sys.stderr)
            except (OSError, ValueError):
                pass
        return error.code if error.code is None or isinstance(error.code, int) else 1
    except Exception:
        logger.critical("command.failed", exc_info=True)
        return 1


# Importing a job must not configure the root logger or emit lastResort text.
logging.getLogger(LOGGER_NAME).addHandler(logging.NullHandler())
logging.getLogger(LOGGER_NAME).propagate = False
