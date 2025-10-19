"""Executor logic for the FireFighter agent."""

from typing import override

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.utils import new_agent_text_message

from firefighter_agent.agent import FireFighterAgent


class FireFighterAgentExecutor(AgentExecutor):
    """Adapter used by the A2A DefaultRequestHandler."""

    def __init__(self) -> None:
        """Initialize the FireFighterAgentExecutor."""
        self.agent = FireFighterAgent()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        response_text: str = await self.agent.invoke(context=context)
        await event_queue.enqueue_event(event=new_agent_text_message(text=response_text))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        msg = "Cancellation is not supported for FireFighterAgent"
        raise RuntimeError(msg)
