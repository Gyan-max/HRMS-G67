"""
logging_config.py — Centralised logging configuration for the backend.

Replaces ad-hoc `print(...)` statements with a structured `logging` setup
so we get:
  - Consistent timestamps and module names on every line
  - Adjustable log level via the LOG_LEVEL env var (default INFO)
  - A single chokepoint for swapping in JSON / structured output later

Use ``logger = logging.getLogger(__name__)`` in each module after calling
``configure_logging()`` once at process startup.
"""

from __future__ import annotations

import logging
import os
import sys

_CONFIGURED = False

DEFAULT_FORMAT = (
    "%(asctime)s %(levelname)-7s [%(name)s] %(message)s"
)


def configure_logging(level: str | int | None = None) -> None:
    """
    Configure the root logger. Idempotent — safe to call multiple times.

    Args:
        level: Optional explicit log level (e.g. "DEBUG", logging.WARNING).
               Falls back to the LOG_LEVEL env var, then "INFO".
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    resolved_level = level if level is not None else os.environ.get("LOG_LEVEL", "INFO")
    if isinstance(resolved_level, str):
        resolved_level = resolved_level.upper()

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(logging.Formatter(DEFAULT_FORMAT))

    root = logging.getLogger()
    # Replace any existing handlers so uvicorn's defaults don't double-log.
    root.handlers = [handler]
    root.setLevel(resolved_level)

    # Tame chatty third-party libraries.
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    _CONFIGURED = True
