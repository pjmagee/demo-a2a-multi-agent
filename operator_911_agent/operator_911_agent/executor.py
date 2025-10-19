"""Executor for the 911 Operator agent."""

import logging
from typing import override

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.utils import new_agent_text_message

from operator_911_agent.agent import Operator911Agent

logger: logging.Logger = logging.getLogger(name=__name__)

class Operator911AgentExecutor(AgentExecutor):
    """Adapter invoked by the A2A DefaultRequestHandler."""

    def __init__(self) -> None:
        """Initialize the adapter with the 911 Operator agent."""
        self.agent = Operator911Agent()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        response_text: str = await self.agent.invoke(context=context)
        logger.info("Agent response: %s", response_text)
        await event_queue.enqueue_event(event=new_agent_text_message(text=response_text))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        msg = "Cancellation is not supported for Operator911Agent"
        raise RuntimeError(msg)
