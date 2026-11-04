"""Shared JSON diagnostics for CLI jobs, kept separate from stdout reports."""
import json
import logging
import os
import sys
from datetime import datetime, timezone

LOGGER_NAME = "unpoliticalaf"


class JsonFormatter(logging.Formatter):
    def format(self, record):
        entry = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
            "context": getattr(record, "context", {}),
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False, default=str)


def get_logger(component):
    return logging.getLogger(f"{LOGGER_NAME}.{component}")


def configure_logging(level=None):
    """Configure only our namespace; repeated calls never duplicate records."""
    level = (level if level is not None else os.environ.get("LOG_LEVEL", "INFO")).upper()
    if level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        raise ValueError("LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR or CRITICAL")
    logger = logging.getLogger(LOGGER_NAME)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False


def run_logged(main, logger):
    """Run a CLI with structured failures, preserving intentional exit codes."""
    try:
        configure_logging()
    except ValueError:
        configure_logging("INFO")
        logger.exception("logging.configuration_failed")
        return 1
    try:
        return main()
    except SystemExit as error:
        if error.code not in (None, 0):
            logger.error("command.failed", extra={"context": {"reason": str(error.code)}})
        return error.code if error.code is None or isinstance(error.code, int) else 1
    except Exception:
        logger.exception("command.failed")
        return 1
