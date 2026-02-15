"""Executor for the Emergency Operator Agent."""

import logging
from datetime import UTC, datetime
from typing import override

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks.task_store import TaskStore
from a2a.types import Message, TaskState, TaskStatus, TaskStatusUpdateEvent
from a2a.utils import new_agent_text_message
from shared.openai_session_helpers import ensure_context_id

from emergency_operator_agent.agent import EmergencyOperatorAgent

logger: logging.Logger = logging.getLogger(name=__name__)


def _new_task_status_update(
    task_id: str,
    context_id: str,
    state: TaskState,
    message: str | None = None,
    final: bool = False,
) -> TaskStatusUpdateEvent:
    """Create a task status update event.

    Args:
        task_id: The task ID
        context_id: The context ID
        state: The new task state
        message: Optional status message
        final: Whether this is the final event

    Returns:
        TaskStatusUpdateEvent ready to be enqueued

    """
    status_message: Message | None = None
    if message:
        status_message = new_agent_text_message(
            context_id=context_id,
            text=message,
            task_id=task_id,
        )

    return TaskStatusUpdateEvent(
        task_id=task_id,
        context_id=context_id,
        status=TaskStatus(
            state=state,
            message=status_message,
            timestamp=datetime.now(UTC).isoformat(),
        ),
        final=final,
    )

class OperatorAgentExecutor(AgentExecutor):
    """Adapter invoked by the A2A DefaultRequestHandler."""

    def __init__(self, task_store: TaskStore) -> None:
        """Initialize the adapter with the Emergency Operator Agent.

        Args:
            task_store: The task store for tracking task state

        """
        self.agent = EmergencyOperatorAgent()
        self.task_store = task_store

    async def _send_status_update(
        self,
        event_queue: EventQueue,
        task_id: str,
        context_id: str,
        state: TaskState,
        message: str | None = None,
        final: bool = False,
    ) -> None:
        """Send a task status update to the event queue.

        Args:
            event_queue: The event queue
            task_id: The task ID
            context_id: The context ID
            state: The new task state
            message: Optional status message
            final: Whether this is the final event

        """
        status_update = _new_task_status_update(
            task_id=task_id,
            context_id=context_id,
            state=state,
            message=message,
            final=final,
        )
        logger.info(
            "Sending task status update task_id=%s state=%s",
            task_id,
            state.value,
        )
        await event_queue.enqueue_event(event=status_update)

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Ensure context_id exists (A2A protocol: server creates if not provided)
        context_id: str = ensure_context_id(context=context)
        task_id: str = context.task_id or context_id

        # Send initial "working" status update
        await self._send_status_update(
            event_queue=event_queue,
            task_id=task_id,
            context_id=context_id,
            state=TaskState.working,
            message="Emergency operator is processing your call...",
        )

        try:
            # Invoke agent with guaranteed context_id and status callback
            response_text: str = await self.agent.invoke(
                context=context,
                context_id=context_id,
                status_callback=lambda msg: self._on_agent_status(
                    event_queue=event_queue,
                    task_id=task_id,
                    context_id=context_id,
                    message=msg,
                ),
            )

            logger.info(
                "Executor sending response context_id=%s text=%s",
                context_id,
                response_text,
            )

            # Send the final text message
            await event_queue.enqueue_event(
                event=new_agent_text_message(
                    context_id=context_id,
                    text=response_text,
                    task_id=task_id,
                ),
            )

            # Send final "completed" status update
            await self._send_status_update(
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id,
                state=TaskState.completed,
                message="Call handled successfully",
                final=True,
            )

        except Exception as e:
            logger.exception("Error executing emergency operator agent")
            # Send "failed" status update
            await self._send_status_update(
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id,
                state=TaskState.failed,
                message=f"Error processing call: {e!s}",
                final=True,
            )
            raise

    async def _on_agent_status(
        self,
        event_queue: EventQueue,
        task_id: str,
        context_id: str,
        message: str,
    ) -> None:
        """Handle status updates from the agent during execution.

        Args:
            event_queue: The event queue
            task_id: The task ID
            context_id: The context ID
            message: Status message from the agent

        """
        await self._send_status_update(
            event_queue=event_queue,
            task_id=task_id,
            context_id=context_id,
            state=TaskState.working,
            message=message,
        )

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        msg = "Cancellation is not supported for Emergency Operator Agent tasks"
        raise RuntimeError(msg)
