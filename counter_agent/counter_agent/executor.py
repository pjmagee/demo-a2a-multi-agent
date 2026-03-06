"""A2A Executor for Counter Agent with SSE streaming."""

import logging
from typing import override

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from shared.traced_executor import a2a_session
from a2a.server.events.event_queue import EventQueue
from a2a.utils import new_agent_text_message

from counter_agent.agent import CounterAgent

logger: logging.Logger = logging.getLogger(name=__name__)


class CounterAgentExecutor(AgentExecutor):
    """Executor that streams counter messages via SSE."""

    def __init__(self) -> None:
        """Initialize the executor with a CounterAgent instance."""
        self.agent: CounterAgent = CounterAgent()
        logger.info("CounterAgentExecutor initialized")

    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute counter agent and stream results via EventQueue."""
        with a2a_session(context, type(self).__name__) as context_id:
            logger.info(
                "CounterAgentExecutor executing for context_id=%s",
                context_id,
            )

            try:
                async for chunk in self.agent.stream(
                    context=context,
                    context_id=context_id,
                ):
                    await event_queue.enqueue_event(
                        event=new_agent_text_message(
                            context_id=context_id,
                            text=chunk,
                            task_id=context.task_id,
                        ),
                    )
            except Exception:
                logger.exception(
                    "Agent streaming failed context_id=%s",
                    context_id,
                )
                await event_queue.enqueue_event(
                    event=new_agent_text_message(
                        context_id=context_id,
                        text="I apologize, but I encountered an error processing your request.",
                        task_id=context.task_id,
                    ),
                )

            logger.info("CounterAgentExecutor completed streaming")

    @override
    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Raise that cancellation is not supported for CounterAgent."""
        msg = "Cancellation is not supported for CounterAgent"
        raise RuntimeError(msg)

