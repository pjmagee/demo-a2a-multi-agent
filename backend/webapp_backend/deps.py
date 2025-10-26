"""FastAPI dependencies used across the backend."""

from __future__ import annotations

from fastapi import Depends

from webapp_backend.clients.a2a_client import A2AAgentClient
from webapp_backend.config import Settings, get_settings

_client: A2AAgentClient | None = None


def get_agent_client(settings: Settings = Depends(dependency=get_settings)) -> A2AAgentClient:
    """Return an agent client configured with the latest addresses."""
    global _client
    if _client is None:
        _client = A2AAgentClient(addresses=settings.agent_addresses)
    else:
        _client = _client.with_addresses(settings.agent_addresses)
    return _client
