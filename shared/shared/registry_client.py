"""Helper utilities for agent registration with the A2A Registry."""

import logging
import os
from typing import Any

import httpx
from a2a.types import AgentCard

logger: logging.Logger = logging.getLogger(name=__name__)

REGISTRY_URL: str = os.getenv("A2A_REGISTRY_URL", "http://127.0.0.1:8090")
HTTPX_TIMEOUT: httpx.Timeout = httpx.Timeout(timeout=10.0)


async def register_with_registry(
    agent_address: str,
    agent_card: AgentCard,
    registry_url: str | None = None,
) -> bool:
    """Register an agent with the A2A Registry.

    Args:
        agent_address: Base URL of the agent (e.g., http://127.0.0.1:8011)
        agent_card: Agent card metadata
        registry_url: Optional registry URL (defaults to A2A_REGISTRY_URL env var)

    Returns:
        True if registration successful, False otherwise

    """
    url = registry_url or REGISTRY_URL
    endpoint = f"{url}/register"

    try:
        async with httpx.AsyncClient(timeout=HTTPX_TIMEOUT) as client:
            response = await client.post(
                endpoint,
                json={
                    "address": agent_address,
                    "agent_card": agent_card.model_dump(),
                },
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            logger.info(
                "Successfully registered %s with registry at %s",
                data.get("agent_name"),
                agent_address,
            )
            return True
    except Exception as exc:
        logger.error(
            "Failed to register agent at %s with registry: %s",
            agent_address,
            exc,
        )
        return False


async def unregister_from_registry(
    agent_address: str,
    registry_url: str | None = None,
) -> bool:
    """Unregister an agent from the A2A Registry.

    Args:
        agent_address: Base URL of the agent to unregister
        registry_url: Optional registry URL (defaults to A2A_REGISTRY_URL env var)

    Returns:
        True if unregistration successful, False otherwise

    """
    url = registry_url or REGISTRY_URL
    # URL encode the address for the path parameter
    encoded_address = httpx.URL(agent_address).raw_path.decode()
    endpoint = f"{url}/unregister/{encoded_address}"

    try:
        async with httpx.AsyncClient(timeout=HTTPX_TIMEOUT) as client:
            response = await client.delete(endpoint)
            response.raise_for_status()
            logger.info(
                "Successfully unregistered agent at %s from registry",
                agent_address,
            )
            return True
    except Exception as exc:
        logger.warning(
            "Failed to unregister agent at %s from registry: %s",
            agent_address,
            exc,
        )
        return False


async def fetch_agents_from_registry(
    registry_url: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch all registered agents from the A2A Registry.

    Args:
        registry_url: Optional registry URL (defaults to A2A_REGISTRY_URL env var)

    Returns:
        List of agent entries (each contains address and agent_card)

    """
    url = registry_url or REGISTRY_URL
    endpoint = f"{url}/agents"

    try:
        async with httpx.AsyncClient(timeout=HTTPX_TIMEOUT) as client:
            response = await client.get(endpoint)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            agents: list[dict[str, Any]] = data.get("agents", [])
            logger.debug("Fetched %d agents from registry", len(agents))
            return agents
    except Exception as exc:
        logger.warning(
            "Failed to fetch agents from registry at %s: %s",
            url,
            exc,
        )
        return []
