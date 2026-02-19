"""Reusable tooling for interacting with peer A2A agents."""

import asyncio
import json
import logging
import os
import re
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    DataPart,
    Message,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    SendMessageResponse,
    TextPart,
)
from agents import FunctionTool, Tool, function_tool
from pydantic import BaseModel

logger: logging.Logger = logging.getLogger(name=__name__)

HTTPX_TIMEOUT: httpx.Timeout = httpx.Timeout(timeout=30.0)
REGISTRY_URL: str = os.getenv("A2A_REGISTRY_URL", "http://127.0.0.1:8090")


class HttpGetResult(BaseModel):
    """Result from HTTP GET request."""
    status_code: int
    content_type: str
    body: str  # Always returned as string (JSON or text)


class AgentCardDetails(BaseModel):
    """Details extracted from an AgentCard."""
    name: str
    base_url: str
    input_modes: list[str]
    output_modes: list[str]
    schema_urls: list[str]
    skills: list[str]


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
        logger.debug("No BASE_URL set - returning all %d addresses", len(addresses))
        return addresses

    normalized_base: str = _normalize_url(url=base_url)
    filtered = [
        address
        for address in addresses
        if _normalize_url(url=address) != normalized_base
    ]

    logger.info(
        "Filtered self address: BASE_URL=%s, total=%d, filtered=%d, removed=%d",
        base_url,
        len(addresses),
        len(filtered),
        len(addresses) - len(filtered),
    )

    return filtered


async def load_peer_addresses_from_registry(
    registry_url: str | None = None,
) -> list[str]:
    """Load peer agent addresses from the A2A Registry.

    Args:
        registry_url: Optional registry URL (defaults to A2A_REGISTRY_URL env var)

    Returns:
        List of peer agent addresses (excluding self)

    """
    url = registry_url or REGISTRY_URL
    endpoint = f"{url}/agents"

    logger.info("Attempting to load peer addresses from registry: %s", endpoint)

    try:
        logger.info("Creating httpx.AsyncClient for registry call...")
        async with httpx.AsyncClient(timeout=HTTPX_TIMEOUT, verify=False) as client:
            logger.info("Sending GET request to %s...", endpoint)
            response = await client.get(endpoint)
            logger.info(
                "Received response from registry: status=%d, size=%d bytes",
                response.status_code,
                len(response.content),
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            agents: list[dict[str, Any]] = data.get("agents", [])
            addresses = [agent["address"] for agent in agents]

            logger.info(
                "Registry returned %d agents: %s",
                len(agents),
                [f"{a.get('name', 'unknown')}@{a.get('address', 'unknown')}" for a in agents],
            )

            filtered = _filter_self_address(addresses)
            logger.info(
                "Loaded %d peer addresses from registry (total agents: %d)",
                len(filtered),
                len(agents),
            )
            return filtered
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "Failed to load addresses from registry at %s: %s",
            url,
            exc,
        )
        return []


def load_peer_addresses(env_var: str = "PEER_AGENT_ADDRESSES") -> list[str]:
    """Return the configured peer agent addresses from the environment.

    DEPRECATED: This fallback method uses environment variables and is only
    used when the registry is unavailable. Prefer using
    load_peer_addresses_from_registry() for dynamic discovery.

    Args:
        env_var: Environment variable name containing comma-separated addresses

    Returns:
        List of peer agent addresses (excluding self)

    """
    raw_value: str = os.getenv(key=env_var, default="")
    addresses: list[str] = [
        value.strip()
        for value in raw_value.split(sep=",")
        if value.strip()
    ]
    return _filter_self_address(addresses=addresses)


def _make_list_agents_tool(explicit_addresses: Sequence[str] | None = None) -> Tool:
    """Construct a tool for listing available agents.

    Args:
        explicit_addresses: Optional explicit addresses. If None, loads from
            registry dynamically when tool is invoked.

    """

    @function_tool
    async def list_agents() -> list[AgentCard]:
        """List all available agents from the registry."""
        # Load addresses dynamically from registry or use explicit ones
        if explicit_addresses is not None:
            addresses = list(explicit_addresses)
            logger.info("Using explicit addresses: %s", addresses)
        else:
            logger.info("Loading addresses from registry: %s", REGISTRY_URL)
            addresses = await load_peer_addresses_from_registry()
            logger.info("Loaded %d addresses from registry", len(addresses))
            # Fallback to env var only if registry fails
            if not addresses:
                logger.warning(
                    "Registry unavailable; falling back to PEER_AGENT_ADDRESSES env var",
                )
                addresses = load_peer_addresses()
                logger.info("Loaded %d addresses from env var", len(addresses))

        agent_cards: list[AgentCard] = []
        if not addresses:
            logger.warning("No peer addresses available - registry returned empty and no env var set")
            return agent_cards

        # Disable SSL verification for local development with self-signed certs
        async with httpx.AsyncClient(
            timeout=HTTPX_TIMEOUT,
            verify=False,
        ) as httpx_client:
            async def resolve(address: str) -> AgentCard | None:
                try:
                    resolver = A2ACardResolver(
                        httpx_client=httpx_client,
                        base_url=address,
                    )
                    card = await resolver.get_agent_card()
                    logger.info("Successfully resolved agent card from %s: %s", address, card.name if card else "None")
                    return card
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
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


def _make_session_management_tool() -> FunctionTool:

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

def _build_send_message_request(message: str, context_id: str | None) -> SendMessageRequest:
    return SendMessageRequest(
        id=uuid4().hex,
        jsonrpc="2.0",
        method="message/send",
        params=MessageSendParams(
            message=Message(
                context_id=context_id,
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

def _make_send_message_tool(explicit_addresses: Sequence[str] | None = None) -> FunctionTool:
    """Construct a tool for sending messages to peers.

    Args:
        explicit_addresses: Optional explicit addresses. If None, loads from
            registry dynamically when tool is invoked.

    """

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

        # Load addresses dynamically from registry or use explicit ones
        if explicit_addresses is not None:
            addresses = list(explicit_addresses)
        else:
            addresses = await load_peer_addresses_from_registry()
            # Fallback to env var only if registry fails
            if not addresses:
                logger.warning(
                    "Registry unavailable; falling back to PEER_AGENT_ADDRESSES env var",
                )
                addresses = load_peer_addresses()

        if not addresses:
            logger.warning("No peer addresses available")
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
                    client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
                    try:
                        response: SendMessageResponse = await client.send_message(
                            request=_build_send_message_request(
                                message=message,
                                context_id=context_identifier,
                            ),
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


def _build_peer_communication_tools(
    peer_addresses: Sequence[str] | None = None,
) -> list[Tool]:
    """Construct tools for listing peers and sending messages.

    Args:
        peer_addresses: Optional explicit addresses. If None, tools will
            dynamically load from registry when invoked.

    """
    # Only prepare addresses if explicitly provided; otherwise let tools load dynamically
    explicit_addrs: tuple[str, ...] | None
    if peer_addresses is not None:
        trimmed_addresses: list[str] = [
            address.strip()
            for address in peer_addresses
            if address.strip()
        ]
        filtered_addresses: list[str] = _filter_self_address(
            addresses=trimmed_addresses,
        )
        explicit_addrs = tuple(filtered_addresses)
    else:
        explicit_addrs = None

    list_agents: Tool = _make_list_agents_tool(explicit_addresses=explicit_addrs)
    send_message: Tool = _make_send_message_tool(explicit_addresses=explicit_addrs)
    return [list_agents, send_message]


def _make_http_get_tool() -> FunctionTool:
    """Construct a tool for fetching data via HTTP GET requests."""

    @function_tool
    async def http_get(url: str) -> HttpGetResult:
        """Fetch data from a URL using HTTP GET.

        Args:
            url: The URL to fetch data from.

        Returns:
            HttpGetResult with status_code, content_type, and body fields.
            The body is always a string (JSON will be serialized).

        """
        logger.info("HTTP GET request to %s", url)
        try:
            async with httpx.AsyncClient(timeout=HTTPX_TIMEOUT) as client:
                response = await client.get(url)
                content_type = response.headers.get("content-type", "text/plain")

                # Always return body as string
                if "application/json" in content_type:
                    try:
                        # Parse then re-serialize to ensure valid JSON string
                        body = json.dumps(response.json())
                    except Exception:
                        body = response.text
                else:
                    body = response.text

                return HttpGetResult(
                    status_code=response.status_code,
                    content_type=content_type,
                    body=body,
                )
        except Exception as exc:
            logger.error("HTTP GET failed for %s: %s", url, exc)
            return HttpGetResult(
                status_code=0,
                content_type="text/plain",
                body=f"Error: {exc}",
            )

    return http_get


def _make_get_agent_card_details_tool(
    explicit_addresses: Sequence[str] | None = None,
) -> FunctionTool:
    """Construct a tool for extracting details from an agent's AgentCard."""

    @function_tool
    async def get_agent_card_details(agent_name: str) -> AgentCardDetails | None:
        """Get detailed information from an agent's AgentCard.

        Args:
            agent_name: Display name of the agent.

        Returns:
            AgentCardDetails containing name, base_url, input_modes, output_modes,
            schema_urls, and skills. Returns None if agent not found.

        """
        logger.info("Getting AgentCard details for %s", agent_name)

        # Load addresses dynamically from registry or use explicit ones
        if explicit_addresses is not None:
            addresses = list(explicit_addresses)
        else:
            addresses = await load_peer_addresses_from_registry()
            if not addresses:
                logger.warning(
                    "Registry unavailable; falling back to PEER_AGENT_ADDRESSES env var",
                )
                addresses = load_peer_addresses()

        if not addresses:
            logger.warning("No peer addresses available")
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
                    # Extract schema URLs from skill descriptions
                    schema_urls: list[str] = []
                    skill_names: list[str] = []

                    for skill in agent_card.skills:
                        skill_names.append(skill.name)
                        # Look for URLs in description (common pattern: "Schema: <url>" or "Request Schema: <url>")
                        if skill.description:
                            url_pattern = r'https?://[\w\-\./:#?&=%]+'
                            matches = re.findall(url_pattern, skill.description)
                            schema_urls.extend(matches)

                    # Collect all unique input/output modes from skills
                    all_input_modes: set[str] = set()
                    all_output_modes: set[str] = set()

                    for skill in agent_card.skills:
                        if skill.input_modes:
                            all_input_modes.update(skill.input_modes)
                        if skill.output_modes:
                            all_output_modes.update(skill.output_modes)

                    return AgentCardDetails(
                        name=agent_card.name,
                        base_url=agent_address,
                        input_modes=sorted(all_input_modes),
                        output_modes=sorted(all_output_modes),
                        schema_urls=list(set(schema_urls)),  # Remove duplicates
                        skills=skill_names,
                    )

        logger.warning("Agent %s not found", agent_name)
        return None

    return get_agent_card_details


def _make_send_data_message_tool(
    explicit_addresses: Sequence[str] | None = None,
) -> FunctionTool:
    """Construct a tool for sending structured data messages to peers."""

    @function_tool
    async def send_data_message(
        agent_name: str,
        json_data: str,
    ) -> SendMessageResponse | None:
        """Send a structured data message (DataPart) to a peer agent.

        Args:
            agent_name: Display name of the target agent.
            json_data: JSON string to send as DataPart (will be parsed into dict).

        Returns:
            SendMessageResponse if successful, None otherwise.

        """
        # Parse JSON string to dict
        try:
            data: dict[str, Any] = json.loads(json_data)
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON data: %s", exc)
            return None
        
        logger.info("Sending data message to %s with payload: %s", agent_name, data)

        # Load addresses dynamically from registry or use explicit ones
        if explicit_addresses is not None:
            addresses = list(explicit_addresses)
        else:
            addresses = await load_peer_addresses_from_registry()
            if not addresses:
                logger.warning(
                    "Registry unavailable; falling back to PEER_AGENT_ADDRESSES env var",
                )
                addresses = load_peer_addresses()

        if not addresses:
            logger.warning("No peer addresses available")
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
                        "Sending data message to %s (context_id=%s)",
                        agent_name,
                        context_identifier,
                    )

                    # Build request with DataPart instead of TextPart
                    request = SendMessageRequest(
                        id=uuid4().hex,
                        jsonrpc="2.0",
                        method="message/send",
                        params=MessageSendParams(
                            message=Message(
                                context_id=context_identifier,
                                role=Role.user,
                                message_id=uuid4().hex,
                                parts=[
                                    Part(
                                        root=DataPart(
                                            kind="data",
                                            data=data,
                                        ),
                                    ),
                                ],
                            ),
                        ),
                    )

                    client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
                    try:
                        response: SendMessageResponse = await client.send_message(
                            request=request,
                        )
                    except Exception as exc:
                        logger.debug(
                            "Peer %s failed to handle data message: %s",
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

    return send_data_message


def default_peer_tools() -> list[Tool]:
    """Return peer communication tools using registry-based discovery.

    Tools will dynamically load agent addresses from the A2A Registry when
    invoked. If the registry is unavailable, falls back to PEER_AGENT_ADDRESSES
    environment variable.

    """
    return _build_peer_communication_tools(peer_addresses=None)


def discovery_tools() -> list[Tool]:
    """Return tools for discovering agent capabilities and fetching schemas.

    Includes:
    - http_get: Fetch data from URLs (useful for fetching schemas)
    - get_agent_card_details: Extract MIME types and schema URLs from AgentCards
    - send_data_message: Send structured JSON data as DataPart to agents

    """
    return [
        _make_http_get_tool(),
        _make_get_agent_card_details_tool(explicit_addresses=None),
        _make_send_data_message_tool(explicit_addresses=None),
    ]


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
