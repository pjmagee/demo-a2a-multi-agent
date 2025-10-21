"""In-memory session provider for maintaining conversation history."""

import logging
from collections.abc import Sequence
from typing import override

from agent_framework import ContextProvider
from agent_framework._memory import Context
from agent_framework._types import ChatMessage

logger: logging.Logger = logging.getLogger(name=__name__)


class InMemorySessionProvider(ContextProvider):
    """In-memory session provider that maintains conversation history per context_id."""

    def __init__(self) -> None:
        """Initialize the in-memory session store."""
        self._sessions: dict[str, list[ChatMessage]] = {}
        logger.debug("InMemorySessionProvider initialized")

    @override
    async def invoking(
        self,
        messages: ChatMessage | Sequence[ChatMessage],
        **kwargs: object,
    ) -> Context:
        """Provide conversation context before invoking the agent.

        Args:
            messages: New message(s) to add to the conversation
            **kwargs: Additional context including context_id

        Returns:
            Context with full conversation history

        """
        context_id_value = kwargs.get("context_id")
        context_id: str | None = (
            context_id_value if isinstance(context_id_value, str) else None
        )

        new_messages: list[ChatMessage] = (
            [messages] if isinstance(messages, ChatMessage) else list(messages)
        )

        if context_id:
            if context_id not in self._sessions:
                self._sessions[context_id] = []
                logger.debug("Created new session for context_id=%s", context_id)

            full_history: list[ChatMessage] = self._sessions[context_id] + new_messages
            logger.debug(
                "Providing context for context_id=%s with %d messages",
                context_id,
                len(full_history),
            )
            return Context(messages=full_history)

        logger.debug("No context_id provided, returning new messages only")
        return Context(messages=new_messages)

    @override
    async def invoked(
        self,
        request_messages: ChatMessage | Sequence[ChatMessage],
        response_messages: ChatMessage | Sequence[ChatMessage] | None = None,
        invoke_exception: BaseException | None = None,
        **kwargs: object,
    ) -> None:
        """Store conversation history after agent invocation.

        Args:
            request_messages: Messages that were sent to the agent
            response_messages: Response messages from the agent
            invoke_exception: Exception if invocation failed
            **kwargs: Additional context including context_id

        """
        context_id_value = kwargs.get("context_id")
        context_id: str | None = (
            context_id_value if isinstance(context_id_value, str) else None
        )

        if (
            context_id
            and context_id in self._sessions
            and response_messages is not None
        ):
            req_list: list[ChatMessage] = (
                [request_messages]
                if isinstance(request_messages, ChatMessage)
                else list(request_messages)
            )

            resp_list: list[ChatMessage] = (
                [response_messages]
                if isinstance(response_messages, ChatMessage)
                else list(response_messages)
            )

            self._sessions[context_id].extend(req_list)
            self._sessions[context_id].extend(resp_list)

            logger.debug(
                "Stored conversation for context_id=%s, total messages=%d",
                context_id,
                len(self._sessions[context_id]),
            )
