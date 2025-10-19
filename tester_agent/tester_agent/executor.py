"""Agent executor for the Tester agent."""

import logging
from typing import override

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.utils import new_agent_text_message

from tester_agent.agent import TesterAgent

logger: logging.Logger = logging.getLogger(name=__name__)


class TesterAgentExecutor(AgentExecutor):
    """Adapter that bridges the Tester agent with the A2A server runtime."""

    tester_agent: TesterAgent

    def __init__(self) -> None:
        """Initialize the TesterAgentExecutor."""
        self.tester_agent = TesterAgent()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        result: str = await self.tester_agent.invoke(context=context)
        context_id: str | None = (
            context.context_id if isinstance(context.context_id, str) else None
        )
        logger.info(
            "Executor sending response context_id=%s text=%s",
            context_id,
            result,
        )
        await event_queue.enqueue_event(
            event=new_agent_text_message(text=result),
        )

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        msg = "Cancellation is not supported for TesterAgent"
        raise RuntimeError(msg)
