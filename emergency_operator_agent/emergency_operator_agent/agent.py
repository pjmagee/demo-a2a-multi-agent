"""Emergency Operator Agent for the OpenAI Agents SDK."""


import asyncio
import logging
import os
from collections.abc import Awaitable, Callable
from typing import ClassVar
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.server.agent_execution.context import RequestContext
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
from agents import Agent, Runner, RunResult, Tool, function_tool
from agents.memory.session import Session
from shared.openai_session_helpers import get_or_create_session_from_context
from shared.peer_tools import (
    HTTPX_TIMEOUT,
    _current_context_id,
    load_peer_addresses_from_registry,
    peer_message_context,
)

logger: logging.Logger = logging.getLogger(name=__name__)


# Type alias for status and message callbacks
StatusCallback = Callable[[str], Awaitable[None]]
MessageCallback = Callable[[str], Awaitable[None]]


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


class EmergencyOperatorAgent:
    """Coordinates emergency routing using the OpenAI Agents SDK."""

    sessions: ClassVar[dict[str, Session]] = {}

    def __init__(self) -> None:
        """Initialize the Emergency Operator Agent."""
        # Store callback references for tool building
        self._status_callback: StatusCallback | None = None
        self._message_callback: MessageCallback | None = None

        self.agent = Agent(
            name="Emergency Operator Agent",
            instructions=(
                "You are a 112 emergency operator. Handle ONLY genuine emergencies.\n\n"
                "For non-emergencies: 'This line is reserved for emergencies only.'\n\n"
                "For emergencies:\n"
                "1. Use list_agents to get exact agent names\n"
                "2. If NO agents are available, inform the caller that all emergency "
                "services are temporarily unavailable and advise them to seek "
                "alternative help\n"
                "3. For each required service, use send_message with EXACT agent name\n"
                "4. Include location, emergency type, and urgency in messages\n"
                "5. After dispatching all services, summarize what was done\n\n"
                "Important: Dispatch services ONE AT A TIME and report responses.\n"
                "Always list agents if unsure of names. Agent names must be exact."
            ),
            handoffs=[],
            tool_use_behavior="run_llm_again",
            tools=self._build_tools(),
        )

    def _build_tools(self) -> list[Tool]:
        """Build tools with status callback support."""
        return [
            self._make_list_agents_tool(),
            self._make_send_message_tool(),
        ]

    def _make_list_agents_tool(self) -> Tool:
        """Create list_agents tool with status callback support."""

        @function_tool
        async def list_agents() -> list[AgentCard]:
            """List all available agents."""
            logger.info("list_agents tool called")
            if self._status_callback:
                logger.info("Calling status_callback: Checking available emergency services...")
                await self._status_callback(
                    "Checking available emergency services...",
                )

            # Fetch peer addresses from registry
            addresses = await load_peer_addresses_from_registry()
            logger.info("Found %d addresses from registry", len(addresses))

            agent_cards: list[AgentCard] = []
            if not addresses:
                if self._status_callback:
                    await self._status_callback(
                        "Warning: No emergency services registered",
                    )
                if self._message_callback:
                    await self._message_callback(
                        "[WARNING] No emergency services are currently "
                        "available in the system.",
                    )
                return agent_cards

            async with httpx.AsyncClient(timeout=HTTPX_TIMEOUT) as httpx_client:

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

    def _make_send_message_tool(self) -> Tool:
        """Create send_message tool with status callback support."""

        @function_tool
        async def send_message(
            agent_name: str,
            message: str,
        ) -> SendMessageResponse | None:
            """Send a text message to the peer identified by agent_name.

            Args:
                agent_name: Display name taken from the peer's AgentCard.
                message: Plain-text payload for the target agent.

            Returns:
                SendMessageResponse when the peer handles the message, or
                None if the peer cannot be reached or declines the request.

            """
            if self._status_callback:
                await self._status_callback(f"Dispatching to {agent_name}...")

            logger.info("Sending message '%s' to %s", message, agent_name)

            # Fetch peer addresses from registry
            addresses = await load_peer_addresses_from_registry()

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
                    except Exception as exc:  # noqa: BLE001
                        logger.debug(
                            "Skipping %s due to agent card error: %s",
                            agent_address,
                            exc,
                        )
                        continue
                    if agent_card.name == agent_name:
                        context_identifier: str | None = _current_context_id()
                        logger.info(
                            "Sending peer message to %s (context_id=%s) "
                            "with payload=%s",
                            agent_name,
                            context_identifier,
                            message,
                        )
                        client = A2AClient(
                            httpx_client=httpx_client, agent_card=agent_card,
                        )
                        try:
                            response: SendMessageResponse = (
                                await client.send_message(
                                    request=SendMessageRequest(
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
                                                        root=TextPart(
                                                            kind="text",
                                                            text=message,
                                                        ),
                                                    ),
                                                ],
                                            ),
                                        ),
                                    ),
                                )
                            )
                        except Exception as exc:  # noqa: BLE001
                            logger.debug(
                                "Peer %s failed to handle message: %s",
                                agent_name,
                                exc,
                            )
                            return None

                        if self._status_callback:
                            await self._status_callback(
                                f"Received response from {agent_name}",
                            )

                        # Send message callback confirming dispatch
                        if self._message_callback:
                            await self._message_callback(
                                f"\u2713 Dispatched: {agent_name} has been "
                                f"notified and is responding",
                            )

                        logger.info(
                            "Peer %s responded to context_id=%s with status=%s",
                            agent_name,
                            context_identifier,
                            getattr(response, "status", "unknown"),
                        )
                        return response

            return None

        return send_message

    async def invoke(
        self,
        context: RequestContext,
        context_id: str,
        status_callback: StatusCallback | None = None,
        message_callback: MessageCallback | None = None,
    ) -> str:
        """Process the caller interaction and return the model response.

        Args:
            context: Request context containing user input
            context_id: Guaranteed non-null context ID (created by executor)
            status_callback: Optional callback for sending status updates
                during execution
            message_callback: Optional callback for sending intermediate
                text messages during execution

        Returns:
            Agent response text

        """
        user_input: str = context.get_user_input()
        session: Session | None = get_or_create_session_from_context(
            sessions=EmergencyOperatorAgent.sessions,
            context=context,
        )

        # Set callbacks for tools to use
        self._status_callback = status_callback
        self._message_callback = message_callback

        # Report initial triage status
        if status_callback:
            await status_callback("Assessing emergency situation...")
        
        if message_callback:
            await message_callback(
                "\ud83d\udea8 Emergency call received. Analyzing situation "
                "and dispatching appropriate services...",
            )

        # Use the context_id provided by the executor for peer messaging
        with peer_message_context(context_id=context_id):
            result: RunResult = await Runner.run(
                starting_agent=self.agent,
                input=user_input,
                session=session,
            )

        # Clear callbacks after execution
        self._status_callback = None
        self._message_callback = None

        response_text: str = result.final_output_as(
            cls=str,
            raise_if_incorrect_type=True,
        )
        return response_text
