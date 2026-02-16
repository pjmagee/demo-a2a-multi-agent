"""Task-orchestrated executor for Emergency Operator Agent."""

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

from emergency_operator_agent.task_orchestrator import EmergencyTaskOrchestrator

logger = logging.getLogger(__name__)


def _new_task_status_update(
    task_id: str,
    context_id: str,
    state: TaskState,
    message: str | None = None,
    final: bool = False,
) -> TaskStatusUpdateEvent:
    """Create a task status update event."""
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


class TaskOrchestratedExecutor(AgentExecutor):
    """Executor that uses task-based orchestration for emergency dispatch."""

    def __init__(self, task_store: TaskStore) -> None:
        """Initialize the executor with task store.

        Args:
            task_store: The task store for persisting task state

        """
        self.task_store = task_store
        self.orchestrator = EmergencyTaskOrchestrator()

    async def _send_status_update(
        self,
        event_queue: EventQueue,
        task_id: str,
        context_id: str,
        state: TaskState,
        message: str | None = None,
        final: bool = False,
    ) -> None:
        """Send a task status update to the event queue."""
        status_update = _new_task_status_update(
            task_id=task_id,
            context_id=context_id,
            state=state,
            message=message,
            final=final,
        )
        logger.info(
            "Task status update: task_id=%s state=%s message=%s",
            task_id,
            state.value,
            message,
        )
        await event_queue.enqueue_event(event=status_update)

    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute emergency dispatch using task orchestration."""
        # Ensure context_id exists
        context_id: str = ensure_context_id(context=context)
        task_id: str = context.task_id or context_id

        logger.info(
            "Starting task orchestration: task_id=%s context_id=%s",
            task_id,
            context_id,
        )

        # Send initial status
        await self._send_status_update(
            event_queue=event_queue,
            task_id=task_id,
            context_id=context_id,
            state=TaskState.working,
            message="Emergency operator analyzing call...",
        )

        try:
            # Phase 1: Create task plan
            user_message = context.get_user_input()
            logger.error("❌ TRACE: Phase 1 starting for task_id=%s", task_id)
            task = await self.orchestrator.create_task_plan(
                task_id=task_id,
                context_id=context_id,
                user_message=user_message,
                event_queue=event_queue,
            )
            logger.error(
                "❌ TRACE: Phase 1 complete - %d steps for task_id=%s",
                len(task.steps),
                task_id,
            )

            # Phase 2: Execute task plan step-by-step
            logger.error("❌ TRACE: Phase 2 starting for task_id=%s", task_id)
            await self.orchestrator.execute_task(
                task=task,
                event_queue=event_queue,
            )
            logger.error("❌ TRACE: Phase 2 complete for task_id=%s", task_id)

            # Send final completion status
            logger.error(
                "❌ TRACE: Sending final status for task_id=%s",
                task_id,
            )
            await self._send_status_update(
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id,
                state=TaskState.completed,
                message="[COMPLETE] Emergency dispatch workflow finished",
                final=True,
            )

        except Exception as e:
            logger.exception(
                "Error during task orchestration: task_id=%s",
                task_id,
            )
            # Send failed status
            await self._send_status_update(
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id,
                state=TaskState.failed,
                message=f"Emergency dispatch failed: {e!s}",
                final=True,
            )
            raise

    @override
    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Cancel an in-progress emergency dispatch task."""
        msg = "Emergency dispatch cancellation not yet implemented"
        raise RuntimeError(msg)
