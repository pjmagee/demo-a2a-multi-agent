"""Reusable tooling for interacting with peer A2A agents."""

import asyncio
import logging
import os
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from contextvars import ContextVar, Token
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

_CURRENT_MESSAGE_CONTEXT_ID: ContextVar[str | None] = ContextVar(
    "shared.peer_tools.context_id",
    default=None,
)
_MANUAL_MESSAGE_CONTEXT_ID: ContextVar[str | None] = ContextVar(
    "shared.peer_tools.manual_context_id",
    default=None,
)

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
    """Construct a tool for listing available agents."""

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
                except Exception as exc:  # noqa: BLE001
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


def _manual_context_id() -> str | None:
    value: str | None = _MANUAL_MESSAGE_CONTEXT_ID.get()
    return value if isinstance(value, str) else None


def _set_manual_context_id(context_id: str | None) -> str | None:
    value: str | None = (
        context_id.strip()
        if isinstance(context_id, str) and context_id.strip()
        else None
    )
    _MANUAL_MESSAGE_CONTEXT_ID.set(value)
    return value


def _current_context_id() -> str | None:
    """Return the message context identifier for the active task."""
    value: str | None = _CURRENT_MESSAGE_CONTEXT_ID.get()
    if isinstance(value, str):
        return value
    return _manual_context_id()


def _make_session_management_tool() -> Tool:
    @function_tool
    async def create_new_session(
        action: str | None = None,
        context_id: str | None = None,
    ) -> str | None:
        """Create, set, or clear the context ID used for peer messaging.

        Args:
            action: ``"new"`` (default) generates a UUID, ``"set"`` uses
                ``context_id`` when provided, and ``"clear"`` removes the
                stored context so future calls behave as fresh sessions.
            context_id: Optional explicit identifier used when ``action`` is
                ``"set"``.

        Returns:
            The active context identifier after the operation, or ``None``
            when cleared.

        """
        normalized_action: str = (action or "new").strip().lower()
        if normalized_action == "clear":
            cleared = _set_manual_context_id(context_id=None)
            logger.info("Manual session cleared")
            return cleared
        if normalized_action == "set" and isinstance(context_id, str):
            set_id = _set_manual_context_id(context_id=context_id)
            logger.info("Manual session set to %s", set_id)
            return set_id
        new_id: str = uuid4().hex
        _set_manual_context_id(context_id=new_id)
        logger.info("Manual session created with id %s", new_id)
        return new_id

    return create_new_session


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
        logger.info("Sending message '%s' to %s", message, agent_name)

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
                    context_identifier: str | None = _current_context_id()
                    logger.info(
                        "Sending peer message to %s (context_id=%s) with payload=%s",
                        agent_name,
                        context_identifier,
                        message,
                    )
                    send_message_request = SendMessageRequest(
                        id=str(object=uuid4()),
                        jsonrpc="2.0",
                        method="message/send",
                        params=MessageSendParams(
                            message=Message(
                                context_id=context_identifier,
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
                        response: SendMessageResponse = await client.send_message(
                            request=send_message_request,
                        )
                    except Exception as exc:
                        logger.debug(
                            "Peer %s failed to handle message: %s",
                            agent_name,
                            exc,
                        )
                        return None
                    logger.info(
                        "Peer %s responded to context_id=%s with status=%s",
                        agent_name,
                        context_identifier,
                        getattr(response, "status", "unknown"),
                    )
                    return response

        return None

    return send_message


def build_peer_communication_tools(
    peer_addresses: Sequence[str] | None = None,
) -> list[Tool]:
    """Construct tools for listing peers and sending messages."""
    addresses = _prepare_addresses(peer_addresses=peer_addresses)
    list_agents: Tool = _make_list_agents_tool(addresses=addresses)
    send_message: Tool = _make_send_message_tool(addresses=addresses)
    return [list_agents, send_message]


def default_peer_tools() -> list[Tool]:
    """Return peer communication tools using environment-provided addresses."""
    return build_peer_communication_tools(peer_addresses=None)


def session_management_tool() -> Tool:
    """Return a tool for managing manual peer messaging sessions."""
    return _make_session_management_tool()


@contextmanager
def peer_message_context(context_id: str | None) -> Iterator[None]:
    """Bind the provided ``context_id`` to outgoing peer messages."""
    token: Token[str | None] = _CURRENT_MESSAGE_CONTEXT_ID.set(
        context_id
        if isinstance(context_id, str)
        else _manual_context_id(),
    )
    try:
        yield
    finally:
        _CURRENT_MESSAGE_CONTEXT_ID.reset(token)
