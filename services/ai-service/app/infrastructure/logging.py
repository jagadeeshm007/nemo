# ==============================================================================
# AI Service — Structured Logging (Loki-compatible)
# ==============================================================================

import logging
import sys
from pythonjsonlogger import jsonlogger


def setup_logging(level: str = "info", format: str = "json") -> None:
    """Configure structured JSON logging for centralized log aggregation."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if format == "json":
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={
                "asctime": "timestamp",
                "levelname": "level",
                "name": "logger",
            },
            datefmt="%Y-%m-%dT%H:%M:%S.%fZ",
        )
        # Add static fields
        formatter.add_fields = _add_static_fields
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Suppress noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def _add_static_fields(self, log_record, record, message_dict):
    """Add static fields to every log record."""
    log_record["service"] = "ai-service"
    if hasattr(record, "request_id"):
        log_record["request_id"] = record.request_id
    jsonlogger.JsonFormatter.add_fields(self, log_record, record, message_dict)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger instance."""
    return logging.getLogger(name)
