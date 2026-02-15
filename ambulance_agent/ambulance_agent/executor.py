"""Ambulance agent executor leveraging the OpenAI Agent SDK."""

import logging
from typing import override

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.utils import new_agent_text_message
from shared.openai_session_helpers import ensure_context_id

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
        # Ensure context_id exists (A2A protocol: server creates if not provided)
        context_id: str = ensure_context_id(context)

        try:
            # Invoke agent with guaranteed context_id
            response_text: str = await self.ambulance_agent.invoke(
                context=context,
                context_id=context_id,
            )
        except Exception:
            logger.exception(
                "Agent invocation failed context_id=%s",
                context_id,
            )
            response_text = (
                "I apologize, but I encountered an error processing your request."
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
        msg = "Cancellation is not supported for AmbulanceAgent"
        raise RuntimeError(msg)
