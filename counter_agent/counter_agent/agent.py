"""Counter Agent using Microsoft agent-framework."""

import logging
import os
from collections.abc import AsyncIterator

from a2a.server.agent_execution.context import RequestContext
from agent_framework import Agent, AgentResponseUpdate
from agent_framework.openai import OpenAIChatClient

from counter_agent.in_memory_session_provider import InMemorySessionProvider

logger: logging.Logger = logging.getLogger(name=__name__)


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
                Maximum count is 1000.
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
        user_input: str = context.get_user_input()
        logger.info(
            "CounterAgent streaming for context_id=%s input=%s",
            context_id,
            user_input,
        )

        chunk: AgentResponseUpdate
        async for chunk in self.agent.run(
            messages=user_input,
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
