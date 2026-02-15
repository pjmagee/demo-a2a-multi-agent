"""Client utilities for interacting with A2A agents.

Performance Notes:
------------------
The original implementation of `list_agents` performed sequential HTTP
requests for each configured agent address, yielding aggregate latency
equal to the sum of all individual response times. This becomes slow
when several agents are cold-starting or one address stalls near the
timeout.

`list_agents` now fetches agent cards concurrently using `asyncio.gather`
to minimize total wait time. An optional `card_timeout` can be supplied
at construction to override the default message timeout for card
resolution only (so the longer timeout can still apply to messaging
exchanges).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    JSONRPCErrorResponse,
    Message,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    SendStreamingMessageRequest,
    SendStreamingMessageResponse,
    SendStreamingMessageSuccessResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    TextPart,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Iterable, Sequence


def _new_str_list() -> list[str]:
    return []


def _new_event_list() -> list[dict[str, object]]:
    return []


@dataclass(slots=True)
class _StreamState:
    """Track incremental details while consuming streaming responses."""

    context_id: str | None
    chunks: list[str] = field(default_factory=_new_str_list)
    raw_events: list[dict[str, object]] = field(default_factory=_new_event_list)
    last_message: Message | None = None
    final_task: Task | None = None
    final_status: TaskStatusUpdateEvent | None = None


@dataclass(slots=True)
class StreamingAccumulator:
    """Accumulate streaming events while exposing incremental metadata."""

    client: A2AAgentClient
    context_id: str | None
    _state: _StreamState = field(init=False)
    _error_response: SendMessageResponse | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        """Initialize the internal stream state container."""
        self._state = _StreamState(context_id=self.context_id)

    def consume(self, event: SendStreamingMessageResponse) -> None:
        """Update internal state with the next streamed event."""
        self._state.raw_events.append(event.model_dump(exclude_none=True))
        root = event.root
        if isinstance(root, JSONRPCErrorResponse):
            self._error_response = SendMessageResponse(root=root)
            return
        self.client.process_stream_result(self._state, root.result)

    def has_events(self) -> bool:
        """Return True when at least one streaming event has been received."""
        return bool(self._state.raw_events)

    def has_error(self) -> bool:
        """Return True if an error response was observed."""
        return self._error_response is not None

    def build_message(self) -> tuple[Message, str, dict[str, object]] | None:
        """Return the synthesized message, aggregated text, and metadata."""
        if self._error_response is not None:
            return None
        if not self._state.raw_events:
            return None

        aggregated_text = "".join(self._state.chunks)
        metadata_payload = self.client.build_stream_metadata(self._state)
        parts = self.client.build_stream_parts(aggregated_text, self._state)
        task_id = self.client.resolve_stream_task_id(self._state)
        message = self.client.construct_stream_message(
            self._state,
            parts=parts,
            metadata=metadata_payload,
            task_id=task_id,
            aggregated_text=aggregated_text,
        )
        return message, aggregated_text, metadata_payload

    def final_response(
        self,
        *,
        payload: SendMessageRequest,
    ) -> SendMessageResponse | None:
        """Return the aggregated response once streaming finishes."""
        if self._error_response is not None:
            return self._error_response
        message_bundle = self.build_message()
        if message_bundle is None:
            return None
        message, _, _ = message_bundle

        return SendMessageResponse(
            root=SendMessageSuccessResponse(
                id=payload.id,
                jsonrpc=payload.jsonrpc,
                result=message,
            ),
        )

    @property
    def raw_events(self) -> list[dict[str, object]]:
        """Return a shallow copy of raw streaming events."""
        return self._state.raw_events.copy()

    @property
    def resolved_context_id(self) -> str | None:
        """Return the latest context identifier tracked for the stream."""
        return self._state.context_id

    @property
    def error_response(self) -> SendMessageResponse | None:
        """Expose any captured JSON-RPC error response."""
        return self._error_response


logger = logging.getLogger(__name__)


class A2AAgentClient:
    """Helper class for resolving and messaging A2A agents."""

    def __init__(
        self,
        addresses: Iterable[str],
        timeout: float = 30.0,
        *,
        card_timeout: float | None = None,
    ) -> None:
        """Initialize the client with a list of agent addresses.

        Parameters
        ----------
        addresses : Iterable[str]
            Base URLs for agent services.
        timeout : float
            General timeout applied to message sending operations.
        card_timeout : float | None
            Optional, shorter timeout applied specifically to agent card
            discovery in ``list_agents``. Falls back to ``timeout`` when not
            provided.
        """
        self._addresses: tuple[str, ...] = tuple(
            address.strip().rstrip("/") for address in addresses if address.strip()
        )
        self._timeout_seconds = timeout
        self._timeout = httpx.Timeout(timeout, read=None)
        self._card_timeout = (
            httpx.Timeout(card_timeout, read=None) if card_timeout else self._timeout
        )

    def with_addresses(self, addresses: Sequence[str]) -> A2AAgentClient:
        """Return a new client instance with an updated address list."""
        return A2AAgentClient(addresses=addresses, timeout=self._timeout_seconds)

    async def list_agents(self) -> list[AgentCard]:
        """Resolve agent cards for all configured addresses concurrently.

        Returns quickly even when one or more agents are slow by launching
        all discovery requests together and waiting for completion. Failed
        or timed-out resolutions are skipped (logged at DEBUG level).
        """
        if not self._addresses:
            return []

        async with httpx.AsyncClient(timeout=self._card_timeout, verify=False) as client:
            async def fetch(address: str) -> AgentCard | None:
                try:
                    resolver = A2ACardResolver(httpx_client=client, base_url=address)
                    return await resolver.get_agent_card()
                except Exception as exc:  # noqa: BLE001
                    logger.debug(
                        "Failed to load agent card from %s: %s",
                        address,
                        exc,
                    )
                    return None

            tasks = [fetch(address) for address in self._addresses]
            results = await asyncio.gather(*tasks, return_exceptions=False)
            cards: list[AgentCard] = [r for r in results if r is not None]
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

        async with httpx.AsyncClient(timeout=self._timeout, verify=False) as client:
            for address in self._addresses:
                try:
                    resolver = A2ACardResolver(httpx_client=client, base_url=address)
                    card: AgentCard = await resolver.get_agent_card()
                except Exception as exc:  # noqa: BLE001
                    logger.debug(
                        "Skipping %s due to resolver failure: %s",
                        address,
                        exc,
                    )
                    continue

                if card.name != agent_name:
                    continue

                payload: SendMessageRequest = self._build_request(
                    message=message,
                    context_id=context_id,
                )
                a2a_client = A2AClient(httpx_client=client, agent_card=card)

                try:
                    if getattr(card.capabilities, "streaming", False):
                        streaming_response = await self._collect_streaming_response(
                            client=a2a_client,
                            payload=payload,
                        )
                        if streaming_response is not None:
                            logger.info(
                                "Received streaming response from %s context_id=%s",
                                agent_name,
                                context_id,
                            )
                            return streaming_response

                    response: SendMessageResponse = await a2a_client.send_message(
                        request=payload,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.debug(
                        "Agent %s failed to handle message: %s",
                        agent_name,
                        exc,
                    )
                    return None
                else:
                    logger.info(
                        "Sent message to %s context_id=%s",
                        agent_name,
                        context_id,
                    )
                    return response
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

    @staticmethod
    def _build_stream_request(
        payload: SendMessageRequest,
    ) -> SendStreamingMessageRequest:
        return SendStreamingMessageRequest(
            id=payload.id,
            params=payload.params,
        )

    @staticmethod
    def _wrap_response_as_streaming(
        response: SendMessageResponse,
    ) -> SendStreamingMessageResponse | None:
        root = getattr(response, "root", None)
        if root is None:
            return None
        if isinstance(root, JSONRPCErrorResponse):
            return SendStreamingMessageResponse(root=root)

        return SendStreamingMessageResponse(
            root=SendStreamingMessageSuccessResponse(
                id=root.id,
                jsonrpc=root.jsonrpc,
                result=root.result,
            ),
        )

    async def _stream_message_events(
        self,
        *,
        client: A2AClient,
        payload: SendMessageRequest,
    ) -> AsyncGenerator[SendStreamingMessageResponse]:
        """Yield streaming events for a message request.

        Converted to an async generator method so callers can iterate directly
        without creating an extra nested coroutine wrapper. This improves
        readability and keeps error stack traces simpler.
        """
        request = self._build_stream_request(payload)
        emitted = 0
        agent_name = getattr(getattr(client, "_agent_card", None), "name", "unknown")
        logger.debug(
            "Begin underlying stream agent=%s context_id=%s payload_id=%s",
            agent_name,
            payload.params.message.context_id,
            payload.id,
        )
        async for event in client.send_message_streaming(
            request=request,
            http_kwargs={"timeout": None},
        ):
            emitted += 1
            logger.debug(
                "Underlying stream event #%s type=%s root_type=%s",
                emitted,
                type(event).__name__,
                type(getattr(event, "root", None)).__name__,
            )
            yield event
        logger.debug(
            "Underlying stream completed emitted=%s agent=%s context_id=%s",
            emitted,
            agent_name,
            payload.params.message.context_id,
        )

    @staticmethod
    def _extract_text_parts(parts: Sequence[Part] | None) -> list[str]:
        if not parts:
            return []
        texts: list[str] = []
        for part in parts:
            root = getattr(part, "root", None)
            if isinstance(root, TextPart) and root.text:
                texts.append(root.text)
        return texts

    @staticmethod
    def _merge_metadata(
        existing: dict[str, object] | None,
        extra: dict[str, object],
    ) -> dict[str, object] | None:
        if not existing:
            return extra or None
        if not extra:
            return existing
        merged = {**existing}
        merged.update(extra)
        return merged

    @staticmethod
    def build_stream_metadata(state: _StreamState) -> dict[str, object]:
        """Construct metadata describing the captured streaming events."""
        streaming: dict[str, object] = {
            "chunk_count": len(state.chunks),
            "event_count": len(state.raw_events),
            "events": state.raw_events,
        }
        if state.chunks:
            streaming["chunks"] = state.chunks.copy()
        if state.final_status is not None:
            streaming["final_state"] = state.final_status.status.state.value
            streaming["final"] = state.final_status.final
        if state.final_task is not None and state.final_task.id:
            streaming["task_id"] = state.final_task.id
        return {"streaming": streaming}

    @staticmethod
    def build_stream_parts(text: str, state: _StreamState) -> list[Part] | None:
        """Return message parts representing the aggregated text payload."""
        if not state.chunks:
            return None
        return [Part(root=TextPart(kind="text", text=text))]

    @staticmethod
    def resolve_stream_task_id(state: _StreamState) -> str | None:
        """Resolve the task identifier associated with the stream, if any."""
        if state.final_task and state.final_task.id:
            return state.final_task.id
        if state.last_message and state.last_message.task_id:
            return state.last_message.task_id
        return None

    def construct_stream_message(
        self,
        state: _StreamState,
        *,
        parts: list[Part] | None,
        metadata: dict[str, object],
        task_id: str | None,
        aggregated_text: str,
    ) -> Message:
        """Build the final Message object representing the stream outcome."""
        if state.last_message is not None:
            message = state.last_message.model_copy(deep=True)
            if parts is not None:
                message.parts = parts
            if state.context_id:
                message.context_id = state.context_id
            if task_id:
                message.task_id = task_id
            merged_metadata = self._merge_metadata(message.metadata, metadata)
            message.metadata = (
                merged_metadata if merged_metadata is not None else metadata
            )
            return message

        return Message(
            context_id=state.context_id,
            role=Role.agent,
            message_id=uuid4().hex,
            parts=parts
            or [Part(root=TextPart(kind="text", text=aggregated_text))],
            metadata=metadata,
            task_id=task_id,
        )

    @classmethod
    def process_stream_result(
        cls,
        state: _StreamState,
        result: object,
    ) -> None:
        """Update the streaming state with the next result payload."""
        if isinstance(result, Message):
            state.last_message = result
            state.context_id = result.context_id or state.context_id
            state.chunks.extend(cls._extract_text_parts(result.parts))
            return

        if isinstance(result, TaskArtifactUpdateEvent):
            state.context_id = result.context_id or state.context_id
            state.chunks.extend(cls._extract_text_parts(result.artifact.parts))
            return

        if isinstance(result, TaskStatusUpdateEvent):
            state.context_id = result.context_id or state.context_id
            state.final_status = result
            if result.status.message:
                state.chunks.extend(
                    cls._extract_text_parts(result.status.message.parts),
                )
            return

        if isinstance(result, Task):
            state.final_task = result
            state.context_id = result.context_id or state.context_id

    async def _collect_streaming_response(
        self,
        *,
        client: A2AClient,
        payload: SendMessageRequest,
    ) -> SendMessageResponse | None:
        stream = self._stream_message_events(client=client, payload=payload)
        accumulator = StreamingAccumulator(
            client=self,
            context_id=payload.params.message.context_id,
        )

        try:
            async for event in stream:
                accumulator.consume(event)
                if accumulator.has_error():
                    return accumulator.final_response(payload=payload)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Streaming exchange failed: %s", exc)
            return None

        if not accumulator.has_events():
            return None

        return accumulator.final_response(payload=payload)

    async def send_message_streaming(
        self,
        agent_name: str,
        message: str,
        context_id: str | None = None,
    ) -> AsyncGenerator[SendStreamingMessageResponse]:
        """Yield streaming responses from the specified agent."""
        if not self._addresses:
            logger.warning("No agent addresses configured")
            return

        logger.info(
            "send_message_streaming called for agent=%s, addresses=%s",
            agent_name,
            self._addresses,
        )

        async with httpx.AsyncClient(timeout=self._timeout, verify=False) as client:
            for address in self._addresses:
                try:
                    logger.debug("Resolving card at %s", address)
                    resolver = A2ACardResolver(httpx_client=client, base_url=address)
                    card: AgentCard = await resolver.get_agent_card()
                    logger.debug(
                        "Resolved card at %s: name=%s streaming=%s",
                        address,
                        card.name,
                        getattr(card.capabilities, "streaming", False),
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.debug(
                        "Skipping %s due to resolver failure: %s",
                        address,
                        exc,
                    )
                    continue

                if card.name != agent_name:
                    logger.debug(
                        "Card name mismatch: looking for %s, found %s at %s",
                        agent_name,
                        card.name,
                        address,
                    )
                    continue

                logger.info(
                    "Matched agent %s at %s, streaming=%s",
                    agent_name,
                    address,
                    getattr(card.capabilities, "streaming", False),
                )

                payload: SendMessageRequest = self._build_request(
                    message=message,
                    context_id=context_id,
                )
                a2a_client = A2AClient(httpx_client=client, agent_card=card)

                if getattr(card.capabilities, "streaming", False):
                    logger.debug(
                        "Streaming capability detected agent=%s context_id=%s",
                        agent_name,
                        context_id,
                    )
                    total = 0
                    try:
                        async for event in self._stream_message_events(
                            client=a2a_client,
                            payload=payload,
                        ):
                            total += 1
                            yield event
                    except Exception as exc:  # noqa: BLE001
                        logger.debug("Streaming exchange failed: %s", exc)
                    logger.debug(
                        (
                            "send_message_streaming completed agent=%s "
                            "context_id=%s total_events=%s"
                        ),
                        agent_name,
                        context_id,
                        total,
                    )
                    return

                try:
                    logger.info(
                        "Calling non-streaming agent=%s context_id=%s",
                        agent_name,
                        context_id,
                    )
                    response: SendMessageResponse = await a2a_client.send_message(
                        request=payload,
                    )
                    logger.info(
                        "Received response from agent=%s context_id=%s",
                        agent_name,
                        context_id,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.exception(
                        "Agent %s failed to handle message",
                        agent_name,
                    )
                    return

                fallback = self._wrap_response_as_streaming(response)
                if fallback is not None:
                    logger.info(
                        "Yielding wrapped response for agent=%s",
                        agent_name,
                    )
                    yield fallback
                else:
                    logger.warning(
                        "Failed to wrap response for agent=%s",
                        agent_name,
                    )
                return
