"""
config/logging_config.py
========================
Centralised logging configuration for the Legislative Intelligence project.

All modules should obtain a logger via ``get_logger(__name__)`` rather than
calling ``logging.getLogger`` directly.  This ensures consistent formatting,
handlers, and log-level control from a single place.

Usage
-----
    from config.logging_config import get_logger

    logger = get_logger(__name__)
    logger.info("Starting data ingestion pipeline")
    logger.warning("Rate-limit approaching; backing off")
    logger.error("Failed to fetch bill PDF: %s", url, exc_info=True)

Log Outputs
-----------
*  **Console handler** – always active; respects LOG_LEVEL.
*  **File handler** – writes to ``logs/<date>.log``; rotates daily,
   keeps 30 days of history.

Design Notes
------------
*  We call ``configure_logging()`` once at import time with the values from
   ``settings``.  Subsequent calls to ``get_logger`` just return a child
   logger under the root ``legislative_intel`` namespace.
*  The root logger is left at WARNING so that noisy third-party libraries
   (requests, urllib3, etc.) do not pollute our logs.
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Internal state — track whether setup has already run
# ---------------------------------------------------------------------------
_configured: bool = False
_ROOT_LOGGER_NAME: str = "legislative_intel"


import re

# ---------------------------------------------------------------------------
# Redacting Filter for Security Hardening (Phase 5 / 8)
# ---------------------------------------------------------------------------


class RedactingFilter(logging.Filter):
    """
    Sanitizes log records to prevent credentials, tokens, connection strings,
    and sensitive customer data from being emitted to stdout or log files.
    """

    PATTERNS: list[tuple[re.Pattern, str]] = [
        # Bearer tokens / JWTs
        (
            re.compile(r"Bearer\s+[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_.+/=]*", re.IGNORECASE),
            "Bearer [REDACTED_TOKEN]",
        ),
        # Raw JWTs
        (
            re.compile(r"eyJ[A-Za-z0-9\-_=]{10,}\.eyJ[A-Za-z0-9\-_=]{10,}\.[A-Za-z0-9\-_.+/=]*"),
            "[REDACTED_JWT]",
        ),
        # Password parameters in URLs/JSON/key-value (quoted or unquoted)
        (
            re.compile(r'((?:password|client_secret|api_key)\s*[:=]\s*["\']?)([^"\'\s&,;]+)(["\']?)', re.IGNORECASE),
            r"\1[REDACTED]\3",
        ),
        # Groq / OpenAI / general API keys
        (
            re.compile(r"gsk_[A-Za-z0-9]{20,}"),
            "[REDACTED_GROQ_KEY]",
        ),
        (
            re.compile(r"sk-[A-Za-z0-9]{20,}"),
            "[REDACTED_API_KEY]",
        ),
        # PostgreSQL / Redis connection strings with passwords
        (
            re.compile(r"(postgres(?:ql)?://[^:]+:)([^@]+)(@)", re.IGNORECASE),
            r"\1[REDACTED_PASSWORD]\3",
        ),
        (
            re.compile(r"(redis://(?::[^@]+)?@)", re.IGNORECASE),
            "redis://:[REDACTED_PASSWORD]@",
        ),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            msg = record.msg
            for pattern, replacement in self.PATTERNS:
                msg = pattern.sub(replacement, msg)
            record.msg = msg
        if record.args:
            if isinstance(record.args, tuple):
                new_args = []
                for a in record.args:
                    if isinstance(a, str):
                        for pattern, replacement in self.PATTERNS:
                            a = pattern.sub(replacement, a)
                    new_args.append(a)
                record.args = tuple(new_args)
            elif isinstance(record.args, dict):
                new_args = {}
                for k, v in record.args.items():
                    if isinstance(v, str):
                        for pattern, replacement in self.PATTERNS:
                            v = pattern.sub(replacement, v)
                    new_args[k] = v
                record.args = new_args
        return True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def configure_logging(
    log_level: str = "INFO",
    log_format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    logs_dir: Path | None = None,
) -> None:
    """
    Configure the root application logger.

    This function is idempotent; calling it multiple times has no effect
    after the first successful call.

    Parameters
    ----------
    log_level : str
        Logging level string (e.g. ``'INFO'``, ``'DEBUG'``).
    log_format : str
        ``logging.Formatter`` format string.
    logs_dir : Path | None
        Directory in which to write rotating log files.  If ``None``,
        file logging is disabled.
    """
    global _configured
    if _configured:
        return

    root_logger = logging.getLogger(_ROOT_LOGGER_NAME)
    root_logger.setLevel(log_level)

    redacting_filter = RedactingFilter()
    root_logger.addFilter(redacting_filter)

    formatter = logging.Formatter(
        fmt=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ------------------------------------------------------------------
    # Console handler
    # ------------------------------------------------------------------
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(redacting_filter)
    root_logger.addHandler(console_handler)

    # ------------------------------------------------------------------
    # Rotating file handler
    # ------------------------------------------------------------------
    if logs_dir is not None:
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_filename = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=log_filename,
            when="midnight",
            backupCount=30,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(redacting_filter)
        root_logger.addHandler(file_handler)

    # Suppress verbose third-party loggers
    for noisy_lib in ("urllib3", "requests", "httpx", "httpcore", "botocore"):
        logging.getLogger(noisy_lib).setLevel(logging.WARNING)

    root_logger.info(
        "Logging configured | level=%s | file_logging=%s",
        log_level,
        logs_dir is not None,
    )
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a child logger under the project namespace.

    Parameters
    ----------
    name : str
        Typically ``__name__`` of the calling module.

    Returns
    -------
    logging.Logger
        A logger named ``legislative_intel.<name>``.

    Examples
    --------
    >>> logger = get_logger(__name__)
    >>> logger.info("Hello from %s", __name__)
    """
    # Lazily initialise with defaults if configure_logging was never called.
    if not _configured:
        try:
            from config.settings import settings  # noqa: PLC0415

            configure_logging(
                log_level=settings.LOG_LEVEL,
                log_format=settings.LOG_FORMAT,
                logs_dir=settings.LOGS_DIR,
            )
        except Exception:  # pragma: no cover
            configure_logging()  # fall back to sane defaults

    # Strip leading package path to avoid double-namespacing
    short_name = name.replace("legislative_intel.", "")
    return logging.getLogger(f"{_ROOT_LOGGER_NAME}.{short_name}")


# ---------------------------------------------------------------------------
# Auto-configure on import
# ---------------------------------------------------------------------------
try:
    from config.settings import settings as _settings  # noqa: PLC0415

    configure_logging(
        log_level=_settings.LOG_LEVEL,
        log_format=_settings.LOG_FORMAT,
        logs_dir=_settings.LOGS_DIR,
    )
except Exception:  # pragma: no cover
    configure_logging()
