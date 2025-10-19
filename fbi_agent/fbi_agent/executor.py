"""Executor implementation for the FBI agent."""



from typing import override

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.utils import new_agent_text_message
from .agent import FBIAgent


class FBIAgentExecutor(AgentExecutor):
    """Adapter invoked by the A2A DefaultRequestHandler."""

    def __init__(self) -> None:
        self.fbi_agent = FBIAgent()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        response_text = await self.fbi_agent.invoke(context)
        await event_queue.enqueue_event(new_agent_text_message(response_text))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise RuntimeError("Cancellation is not supported for FBIAgent")
