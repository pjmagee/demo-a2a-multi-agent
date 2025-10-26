"""Logging helpers for the backend service."""

from __future__ import annotations

import logging

_LOGGER = logging.getLogger("webapp_backend")
_HANDLER_NAME = "webapp-backend-stream"


def configure_logging(level: int = logging.INFO) -> None:
    """Configure the root logger with a single stream handler."""
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.name = _HANDLER_NAME

    root = logging.getLogger()
    for existing in root.handlers:
        if getattr(existing, "name", None) == _HANDLER_NAME:
            return
    root.setLevel(level)
    root.addHandler(handler)

    _LOGGER.debug("Logging configured for webapp backend")
