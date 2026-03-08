"""Summarise agent executor with tool-call streaming."""

import logging
from typing import override

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.utils import new_agent_text_message
from shared.openai_session_helpers import get_or_create_session
from shared.openai_streaming import stream_openai_agent
from shared.traced_executor import a2a_session

from summarise_agent.agent import SummariseAgent

logger: logging.Logger = logging.getLogger(name=__name__)


class SummariseAgentExecutor(AgentExecutor):
    """Adapter used by the A2A DefaultRequestHandler."""

    def __init__(self) -> None:
        """Initialise the Summarise agent executor."""
        self.agent = SummariseAgent()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        with a2a_session(context, type(self).__name__) as context_id:
            task_id = context.task_id or context_id
            user_input = context.get_user_input()
            session = get_or_create_session(
                sessions=SummariseAgent.sessions,
                context_id=context_id,
            )

            try:
                await stream_openai_agent(
                    agent=self.agent.agent,
                    user_input=user_input,
                    session=session,
                    context_id=context_id,
                    task_id=task_id,
                    event_queue=event_queue,
                )
            except Exception:
                logger.exception(
                    "Agent invocation failed context_id=%s",
                    context_id,
                )
                await event_queue.enqueue_event(
                    event=new_agent_text_message(
                        context_id=context_id,
                        text="Chat Conversation",
                        task_id=context.task_id,
                    ),
                )

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        msg = "Cancellation is not supported for SummariseAgent"
        raise RuntimeError(msg)
