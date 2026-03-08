"""Executor for the Emergency Operator Agent."""

import logging
from typing import override

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks.task_store import TaskStore
from a2a.types import TaskState, TaskStatus, TaskStatusUpdateEvent
from shared.openai_session_helpers import get_or_create_session
from shared.openai_streaming import stream_openai_agent
from shared.peer_tools import peer_message_context
from shared.traced_executor import a2a_session

from emergency_operator_agent.agent import EmergencyOperatorAgent

logger: logging.Logger = logging.getLogger(name=__name__)


class OperatorAgentExecutor(AgentExecutor):
    """Adapter invoked by the A2A DefaultRequestHandler.

    Uses streaming to emit tool-call and tool-call-result events
    following the a2a-ui metadata convention.
    """

    def __init__(self, task_store: TaskStore) -> None:
        """Initialize the adapter with the Emergency Operator Agent."""
        self.agent = EmergencyOperatorAgent()
        self.task_store = task_store

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        with a2a_session(context, type(self).__name__) as context_id:
            task_id: str = context.task_id or context_id
            user_input: str = context.get_user_input()
            session = get_or_create_session(
                sessions=EmergencyOperatorAgent.sessions,
                context_id=context_id,
            )

            try:
                with peer_message_context(context_id=context_id):
                    await stream_openai_agent(
                        agent=self.agent.agent,
                        user_input=user_input,
                        session=session,
                        context_id=context_id,
                        task_id=task_id,
                        event_queue=event_queue,
                    )
            except Exception:
                logger.exception("Error executing emergency operator agent")
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        task_id=task_id,
                        context_id=context_id,
                        status=TaskStatus(state=TaskState.failed),
                        final=True,
                    ),
                )
                raise

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        msg = "Cancellation is not supported for Emergency Operator Agent tasks"
        raise RuntimeError(msg)
