"""Shared utilities for the multi-agent workspace."""

import logging

from shared.peer_tools import (
    build_peer_communication_tools,
    default_peer_tools,
    load_peer_addresses,
)


def configure_logging(level: int = logging.INFO) -> None:
    """Initialise application logging once with a shared format."""
    root_logger: logging.Logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.setLevel(level)
        return
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(name)s [%(levelname)s] %(message)s",
    )


__all__: list[str] = [
    "build_peer_communication_tools",
    "configure_logging",
    "default_peer_tools",
    "load_peer_addresses",
]
