"""Mi5 agent executor with tool-call streaming."""

import logging
from typing import override

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.utils import new_agent_text_message
from shared.openai_session_helpers import get_or_create_session
from shared.openai_streaming import stream_openai_agent
from shared.peer_tools import peer_message_context
from shared.traced_executor import a2a_session

from .agent import Mi5Agent

logger: logging.Logger = logging.getLogger(name=__name__)


class Mi5AgentExector(AgentExecutor):
    """Adapter invoked by the A2A DefaultRequestHandler."""

    def __init__(self) -> None:
        """Initialize the executor with the Mi5 Agent."""
        self.mi5_agent = Mi5Agent()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        with a2a_session(context, type(self).__name__) as context_id:
            task_id = context.task_id or context_id
            user_input = context.get_user_input()
            session = get_or_create_session(
                sessions=Mi5Agent.sessions,
                context_id=context_id,
            )

            with peer_message_context(context_id=context_id):
                try:
                    await stream_openai_agent(
                        agent=self.mi5_agent.agent,
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
                            text="I apologize, but I encountered an error processing your request.",
                            task_id=context.task_id,
                        ),
                    )

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        msg = "Cancellation is not supported for Mi5Agent"
        raise RuntimeError(msg)
