"""Ambulance agent executor leveraging the OpenAI Agent SDK."""

import logging
from typing import override

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.utils import new_agent_text_message

from ambulance_agent.agent import AmbulanceAgent

logger: logging.Logger = logging.getLogger(name=__name__)

class AmbulanceAgentExecutor(AgentExecutor):
    """Adapter invoked by the A2A DefaultRequestHandler."""

    ambulance_agent: AmbulanceAgent

    def __init__(self) -> None:
        """Initialize the AmbulanceAgent."""
        self.ambulance_agent = AmbulanceAgent()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        response_text: str = await self.ambulance_agent.invoke(context=context)
        logger.info("Agent response: %s", response_text)
        await event_queue.enqueue_event(event=new_agent_text_message(text=response_text))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        msg = "Cancellation is not supported for AmbulanceAgent"
        raise RuntimeError(msg)
