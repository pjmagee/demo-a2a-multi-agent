"""Weather agent executor using OpenAI Agent SDK."""

import logging
from typing import override

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.utils import new_agent_text_message
from shared.openai_session_helpers import ensure_context_id

from weather_agent.agent import WeatherAgent

logger: logging.Logger = logging.getLogger(name=__name__)

class WeatherAgentExecutor(AgentExecutor):
    """Adapter invoked by the A2A DefaultRequestHandler."""

    def __init__(self) -> None:
        """Initialize the adapter with the underlying agent."""
        self.agent = WeatherAgent()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Ensure context_id exists (A2A protocol: server creates if not provided)
        context_id: str = ensure_context_id(context)

        # Invoke agent with guaranteed context_id
        response_text: str = await self.agent.invoke(
            context=context,
            context_id=context_id,
        )

        logger.info(
            "Executor sending response context_id=%s text=%s",
            context_id,
            response_text,
        )
        await event_queue.enqueue_event(
            event=new_agent_text_message(
                context_id=context_id,
                text=response_text,
                task_id=context.task_id,
            ),
        )

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        msg = "Cancellation is not supported for WeatherAgent"
        raise RuntimeError(msg)
