"""Executor logic for the Star Wars agent."""

import logging
from typing import override

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.utils import new_agent_text_message
from shared.traced_executor import a2a_session

from starwars_agent.agent import StarWarsAgent

logger = logging.getLogger(__name__)


class StarWarsAgentExecutor(AgentExecutor):
    """Adapter used by the A2A DefaultRequestHandler."""

    def __init__(self) -> None:
        """Initialise the Star Wars agent executor."""
        self.agent = StarWarsAgent()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute the agent for an incoming A2A request."""
        with a2a_session(context, type(self).__name__) as context_id:
            try:
                user_input = context.get_user_input()
                response_text = await self.agent.invoke(user_input)
            except Exception:
                logger.exception("Agent invocation failed context_id=%s", context_id)
                response_text = "I apologize, but I encountered an error processing your request."

            logger.info("Executor sending response context_id=%s", context_id)
            await event_queue.enqueue_event(
                event=new_agent_text_message(
                    context_id=context_id,
                    text=response_text,
                    task_id=context.task_id,
                ),
            )

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel is not supported."""
        msg = "Cancellation is not supported for StarWarsAgent"
        raise RuntimeError(msg)
