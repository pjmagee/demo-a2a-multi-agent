"""FastAPI dependency helpers for constructing shared service objects.

Avoids using function calls in default parameter values (B008) and the global
mutation pattern flagged by linters. Instead we keep a simple module-level
cache keyed by the tuple of addresses.
"""

from __future__ import annotations

import logging
from typing import Annotated

import httpx
from fastapi import Depends

from webapp_backend.clients.a2a_client import A2AAgentClient
from webapp_backend.config import Settings, get_settings

logger = logging.getLogger(__name__)
_client_cache: dict[tuple[str, ...], A2AAgentClient] = {}


async def _fetch_addresses_from_registry(registry_url: str) -> list[str]:
    """Fetch agent addresses from the A2A registry."""
    logger.info("Attempting to fetch agents from registry at: %s", registry_url)
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            response = await client.get(f"{registry_url}/agents")
            response.raise_for_status()
            data = response.json()
            agents = data.get("agents", [])
            addresses = [agent["address"] for agent in agents if "address" in agent]
            logger.info("Fetched %d agent addresses from registry", len(addresses))
            return addresses
    except Exception as exc:
        logger.warning("Failed to fetch from registry at %s: %s", registry_url, exc)
        return []


def _build_client(addresses: list[str]) -> A2AAgentClient:
    return A2AAgentClient(addresses=addresses)


SettingsDep = Annotated[Settings, Depends(get_settings)]


async def get_agent_client(settings: SettingsDep) -> A2AAgentClient:
    """Return a cached A2AAgentClient for the current settings.

    If use_registry is True, fetches addresses from the registry dynamically.
    Otherwise, uses the configured agent_addresses list.
    
    The cache key is the tuple of addresses. This is a lightweight approach to
    reduce object churn while staying side-effect free.
    """
    logger.info("get_agent_client: use_registry=%s, registry_url=%s", 
                settings.use_registry, settings.registry_url)
    
    if settings.use_registry:
        addresses = await _fetch_addresses_from_registry(settings.registry_url)
    else:
        addresses = settings.agent_addresses
        logger.info("Using configured agent_addresses: %s", addresses)
    
    key = tuple(addresses)
    client = _client_cache.get(key)
    if client is not None:
        return client
    client = _build_client(addresses)
    _client_cache[key] = client
    return client
