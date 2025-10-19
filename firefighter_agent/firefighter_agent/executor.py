"""Executor logic for the FireFighter agent."""

import logging
from typing import override

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.utils import new_agent_text_message

from firefighter_agent.agent import FireFighterAgent

logger: logging.Logger = logging.getLogger(name=__name__)


class FireFighterAgentExecutor(AgentExecutor):
    """Adapter used by the A2A DefaultRequestHandler."""

    def __init__(self) -> None:
        """Initialize the FireFighterAgentExecutor."""
        self.agent = FireFighterAgent()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        response_text: str = await self.agent.invoke(context=context)
        context_id: str | None = (
            context.context_id if isinstance(context.context_id, str) else None
        )
        logger.info(
            "Executor sending response context_id=%s text=%s",
            context_id,
            response_text,
        )
        await event_queue.enqueue_event(
            event=new_agent_text_message(text=response_text),
        )

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        msg = "Cancellation is not supported for FireFighterAgent"
        raise RuntimeError(msg)
