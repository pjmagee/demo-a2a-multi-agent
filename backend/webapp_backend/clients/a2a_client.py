"""Client utilities for interacting with A2A agents."""

import logging
from collections.abc import Iterable, Sequence
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

logger = logging.getLogger(__name__)


class A2AAgentClient:
    """Helper class for resolving and messaging A2A agents."""

    def __init__(self, addresses: Iterable[str], timeout: float = 30.0) -> None:
        """Initialize the client with a list of agent addresses."""
        self._addresses: tuple[str, ...] = tuple(
            address.strip().rstrip("/") for address in addresses if address.strip()
        )
        self._timeout_seconds = timeout
        self._timeout = httpx.Timeout(timeout)

    def with_addresses(self, addresses: Sequence[str]) -> "A2AAgentClient":
        """Return a new client instance with an updated address list."""
        return A2AAgentClient(addresses=addresses, timeout=self._timeout_seconds)

    async def list_agents(self) -> list[AgentCard]:
        """Resolve agent cards for all configured addresses."""

        if not self._addresses:
            return []

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            cards: list[AgentCard] = []
            for address in self._addresses:
                try:
                    resolver = A2ACardResolver(httpx_client=client, base_url=address)
                    card = await resolver.get_agent_card()
                    cards.append(card)
                except Exception as exc:  # noqa: BLE001
                    logger.debug("Failed to load agent card from %s: %s", address, exc)
            return cards

    async def send_message(
        self,
        agent_name: str,
        message: str,
        context_id: str | None = None,
    ) -> SendMessageResponse | None:
        """Send a text message to the agent with the given display name."""

        if not self._addresses:
            return None

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for address in self._addresses:
                try:
                    resolver = A2ACardResolver(httpx_client=client, base_url=address)
                    card: AgentCard = await resolver.get_agent_card()
                except Exception as exc:  # noqa: BLE001
                    logger.debug("Skipping %s due to resolver failure: %s", address, exc)
                    continue

                if card.name != agent_name:
                    continue

                payload: SendMessageRequest = self._build_request(
                    message=message,
                    context_id=context_id,
                )
                a2a_client = A2AClient(httpx_client=client, agent_card=card)
                try:
                    response: SendMessageResponse = await a2a_client.send_message(
                        request=payload,
                    )
                    logger.info(
                        "Sent message to %s context_id=%s", agent_name, context_id,
                    )
                    return response
                except Exception as exc:  # noqa: BLE001
                    logger.debug("Agent %s failed to handle message: %s", agent_name, exc)
                    return None
        return None

    @staticmethod
    def _build_request(message: str, context_id: str | None) -> SendMessageRequest:
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
