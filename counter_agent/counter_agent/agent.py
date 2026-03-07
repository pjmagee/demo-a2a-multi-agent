"""Counter Agent using Microsoft agent-framework."""

import base64
import logging
import os
from collections.abc import AsyncIterator

from a2a.server.agent_execution.context import RequestContext
from a2a.types import FilePart, FileWithBytes, FileWithUri, TextPart
from agent_framework import Agent, AgentResponseUpdate, Content, Message
from agent_framework.openai import OpenAIChatClient

from counter_agent.in_memory_session_provider import InMemorySessionProvider

logger: logging.Logger = logging.getLogger(name=__name__)


def _a2a_message_to_framework(context: RequestContext) -> Message:
    """Convert the A2A request message into an agent-framework Message.

    Maps A2A TextPart to Content.from_text and A2A FilePart (with bytes)
    to Content.from_data so the LLM sees file attachments.
    """
    contents: list[Content | str] = []
    a2a_msg = context.message
    if a2a_msg and a2a_msg.parts:
        for part in a2a_msg.parts:
            root = part.root
            if isinstance(root, TextPart) and root.text:
                contents.append(Content.from_text(root.text))
            elif isinstance(root, FilePart):
                f = root.file
                if isinstance(f, FileWithBytes) and f.bytes:
                    raw = base64.b64decode(f.bytes)
                    mime = f.mime_type or "application/octet-stream"
                    contents.append(Content.from_data(data=raw, media_type=mime))
                elif isinstance(f, FileWithUri) and f.uri:
                    label = f.name or f.uri
                    contents.append(
                        Content.from_text(f"[Attached file: {label}]"),
                    )
    if not contents:
        contents.append(context.get_user_input() or "")
    return Message("user", contents)


class CounterAgent:
    """Agent that streams count numbers using Microsoft agent-framework."""

    def __init__(self) -> None:
        """Initialize the CounterAgent with Microsoft agent-framework."""
        self.session_provider = InMemorySessionProvider()

        self.agent = Agent(
           client=OpenAIChatClient(
                api_key=os.getenv(key="OPENAI_API_KEY"),
                model_id=os.getenv(key="OPENAI_CHAT_MODEL_ID", default="gpt-4o-mini"),
            ),
            name="CounterAgent",
            instructions="""
                You are a counting assistant. You should count to the number requested.
                Maximum count is 1000 or -1000.
                """,
            context_providers=[self.session_provider],
            tool_choice="auto",
        )
        logger.info("CounterAgent initialized with Microsoft agent-framework")

    async def stream(
        self,
        context: RequestContext,
        context_id: str,
    ) -> AsyncIterator[str]:
        """Stream count numbers based on user request.

        Args:
            context: Request context containing user input
            context_id: Context ID for the request

        Yields:
            String representation of each count number (streamed from agent)

        """
        message: Message = _a2a_message_to_framework(context)
        logger.info(
            "CounterAgent streaming for context_id=%s input=%s",
            context_id,
            message.text,
        )

        chunk: AgentResponseUpdate
        async for chunk in self.agent.run(
            messages=message,
            stream=True,
            context_id=context_id,
        ):
            if chunk.text:
                yield chunk.text
                logger.debug(
                    "Streamed chunk for context_id=%s: %s",
                    context_id,
                    chunk.text,
                )

        logger.info("CounterAgent completed streaming for context_id=%s", context_id)
