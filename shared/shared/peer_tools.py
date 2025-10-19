"""Reusable tooling for interacting with peer A2A agents."""

import asyncio
import logging
import os
from collections.abc import Sequence
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    Message,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    SendMessageResponse,
    TextPart,
)
from agents import Tool, function_tool

logger: logging.Logger = logging.getLogger(name=__name__)
HTTPX_TIMEOUT: httpx.Timeout = httpx.Timeout(timeout=30.0)


def _normalize_url(url: str) -> str:
    """Return a normalized representation of the given URL."""
    return url.strip().rstrip("/")


def _filter_self_address(addresses: list[str]) -> list[str]:
    """Remove the current agent's base URL from the peer address list."""
    base_url: str = os.getenv(key="BASE_URL", default="").strip()
    if not base_url:
        return addresses

    normalized_base: str = _normalize_url(url=base_url)
    return [
        address
        for address in addresses
        if _normalize_url(url=address) != normalized_base
    ]


def load_peer_addresses(env_var: str = "PEER_AGENT_ADDRESSES") -> list[str]:
    """Return the configured peer agent addresses from the environment."""
    raw_value: str = os.getenv(key=env_var, default="")
    addresses: list[str] = [
        value.strip()
        for value in raw_value.split(sep=",")
        if value.strip()
    ]
    return _filter_self_address(addresses=addresses)


def _prepare_addresses(
    peer_addresses: Sequence[str] | None,
) -> tuple[str, ...]:
    if peer_addresses is not None:
        trimmed_addresses: list[str] = [
            address.strip()
            for address in peer_addresses
            if address.strip()
        ]
        filtered_addresses: list[str] = _filter_self_address(
            addresses=trimmed_addresses,
        )
    else:
        filtered_addresses = load_peer_addresses()
    return tuple(filtered_addresses)


def _make_list_agents_tool(addresses: tuple[str, ...]) -> Tool:
    @function_tool
    async def list_agents() -> list[AgentCard]:
        """List all available agents."""
        agent_cards: list[AgentCard] = []
        if not addresses:
            return agent_cards

        async with httpx.AsyncClient(
            timeout=HTTPX_TIMEOUT,
        ) as httpx_client:
            async def resolve(address: str) -> AgentCard | None:
                try:
                    resolver = A2ACardResolver(
                        httpx_client=httpx_client,
                        base_url=address,
                    )
                    return await resolver.get_agent_card()
                except Exception as exc:
                    logger.debug(
                        "Unable to resolve agent card from %s: %s",
                        address,
                        exc,
                    )
                    return None

            results: list[AgentCard | None] = await asyncio.gather(
                *(resolve(address=address) for address in addresses),
            )

        agent_cards.extend(
            agent_card for agent_card in results if agent_card is not None
        )
        return agent_cards

    return list_agents


def _make_send_message_tool(addresses: tuple[str, ...]) -> Tool:
    @function_tool
    async def send_message(
        agent_name: str,
        message: str,
    ) -> SendMessageResponse | None:
        """Send a text message to the peer identified by ``agent_name``.

        Args:
            agent_name: Display name taken from the peer's ``AgentCard``.
            message: Plain-text payload for the target agent.

        Returns:
            ``SendMessageResponse`` when the peer handles the message, or
            ``None`` if the peer cannot be reached or declines the request.

        """
        if not addresses:
            return None

        async with httpx.AsyncClient(timeout=HTTPX_TIMEOUT) as httpx_client:
            for agent_address in addresses:
                try:
                    resolver = A2ACardResolver(
                        httpx_client=httpx_client,
                        base_url=agent_address,
                    )
                    agent_card: AgentCard = await resolver.get_agent_card()
                except Exception as exc:
                    logger.debug(
                        "Skipping %s due to agent card error: %s",
                        agent_address,
                        exc,
                    )
                    continue
                if agent_card.name == agent_name:
                    send_message_request = SendMessageRequest(
                        id=str(object=uuid4()),
                        params=MessageSendParams(
                            message=Message(
                                role=Role.user,
                                message_id=uuid4().hex,
                                parts=[
                                    Part(
                                        root=TextPart(
                                            kind="text",
                                            text=message,
                                        ),
                                    ),
                                ],
                            ),
                        ),
                    )
                    client = A2AClient(
                        httpx_client=httpx_client,
                        agent_card=agent_card,
                    )
                    try:
                        return await client.send_message(
                            request=send_message_request,
                        )
                    except Exception as exc:
                        logger.debug(
                            "Peer %s failed to handle message: %s",
                            agent_name,
                            exc,
                        )
                        return None

        return None

    return send_message


def build_peer_communication_tools(
    peer_addresses: Sequence[str] | None = None,
) -> tuple[Tool, Tool]:
    """Construct tools for listing peers and sending messages."""
    addresses = _prepare_addresses(peer_addresses=peer_addresses)
    return (
        _make_list_agents_tool(addresses=addresses),
        _make_send_message_tool(addresses=addresses),
    )


def default_peer_tools() -> tuple[Tool, Tool]:
    """Return peer communication tools using environment-provided addresses."""
    return build_peer_communication_tools(peer_addresses=None)
