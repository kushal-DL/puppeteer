"""Observability logging — redacting formatter, rotating handlers, session context.

Provides:
- RedactingFormatter: strips API keys, tokens, auth headers from log output
- setup_logging(): configures console + rotating file handlers
- set_session_context(): per-job log correlation via thread-local tags

Inspired by hermes-agent's hermes_logging.py.
"""

import logging
import os
import pathlib
import re
import threading
from logging.handlers import RotatingFileHandler

# Thread-local storage for session/job context
_context = threading.local()

# Patterns to redact from log output
_REDACT_PATTERNS = [
    # API keys (generic patterns)
    re.compile(r"(api[_-]?key|apikey)\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"(GEMINI_API_KEY|GITHUB_TOKEN|WEBHOOK_SECRET)\s*[=:]\s*\S+", re.IGNORECASE),
    # Bearer / Basic auth tokens
    re.compile(r"(Bearer|Basic)\s+[A-Za-z0-9+/=_-]{8,}", re.IGNORECASE),
    # Authorization headers
    re.compile(r"(Authorization)\s*:\s*\S+", re.IGNORECASE),
    # Generic token-like strings (40+ hex chars that look like secrets)
    re.compile(r"(ghp_|gho_|ghs_|github_pat_)[A-Za-z0-9_]{30,}"),
    re.compile(r"AIzaSy[A-Za-z0-9_-]{33}"),  # Google API key pattern
]

_REDACTED = "[REDACTED]"


def set_session_context(job_id: str) -> None:
    """Set the current job ID for log correlation (thread-local)."""
    _context.job_id = job_id


def get_session_context() -> str:
    """Get the current job ID, or empty string."""
    return getattr(_context, "job_id", "")


class RedactingFormatter(logging.Formatter):
    """Log formatter that strips secrets from output."""

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        for pattern in _REDACT_PATTERNS:
            msg = pattern.sub(_REDACTED, msg)
        # Inject session context if available
        job_id = get_session_context()
        if job_id:
            msg = f"[{job_id}] {msg}"
        return msg


# Noisy loggers to suppress
_NOISY_LOGGERS = [
    "httpx",
    "httpcore",
    "google.auth",
    "google.auth.transport",
    "urllib3",
    "urllib3.connectionpool",
    "openai",
    "grpc",
]


def setup_logging(
    log_dir: str = "",
    console_level: int = logging.INFO,
    file_level: int = logging.INFO,
    error_level: int = logging.WARNING,
    max_bytes: int = 5 * 1024 * 1024,  # 5MB
    backup_count: int = 3,
) -> None:
    """Configure structured logging with console + rotating file handlers.

    Args:
        log_dir: Directory for log files. Empty = use HIVESHIP_LOG_DIR env or skip files.
        console_level: Console handler log level.
        file_level: Main log file level.
        error_level: Error log file level.
        max_bytes: Max size per log file before rotation.
        backup_count: Number of backup files to keep.
    """
    log_dir = log_dir or os.environ.get("HIVESHIP_LOG_DIR", "")
    root = logging.getLogger()

    # Only configure if not already set up (avoid duplicate handlers on reload)
    if any(isinstance(h, RotatingFileHandler) for h in root.handlers):
        return

    root.setLevel(logging.DEBUG)

    fmt = "%(asctime)s %(levelname)-8s %(name)s — %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    redacting_fmt = RedactingFormatter(fmt, datefmt=datefmt)

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(console_level)
    console.setFormatter(redacting_fmt)
    root.addHandler(console)

    # File handlers (only if log_dir is set)
    if log_dir:
        log_path = pathlib.Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # Main log file
        main_handler = RotatingFileHandler(
            str(log_path / "agent.log"),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        main_handler.setLevel(file_level)
        main_handler.setFormatter(redacting_fmt)
        root.addHandler(main_handler)

        # Error log file
        error_handler = RotatingFileHandler(
            str(log_path / "errors.log"),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(error_level)
        error_handler.setFormatter(redacting_fmt)
        root.addHandler(error_handler)

    # Suppress noisy loggers
    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
