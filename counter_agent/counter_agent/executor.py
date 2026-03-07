"""A2A Executor for Counter Agent with SSE streaming."""

import logging
from datetime import UTC, datetime
from typing import override

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import TaskState, TaskStatus, TaskStatusUpdateEvent
from a2a.utils import new_agent_text_message
from shared.traced_executor import a2a_session

from counter_agent.agent import CounterAgent

logger: logging.Logger = logging.getLogger(name=__name__)


def _status_event(
    task_id: str,
    context_id: str,
    text: str,
    state: TaskState,
    *,
    final: bool,
) -> TaskStatusUpdateEvent:
    return TaskStatusUpdateEvent(
        task_id=task_id,
        context_id=context_id,
        status=TaskStatus(
            state=state,
            message=new_agent_text_message(
                text=text,
                context_id=context_id,
                task_id=task_id,
            ),
            timestamp=datetime.now(UTC).isoformat(),
        ),
        final=final,
    )


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
            task_id = context.task_id or context_id

            try:
                last_chunk: str | None = None
                async for chunk in self.agent.stream(
                    context=context,
                    context_id=context_id,
                ):
                    if last_chunk is not None:
                        await event_queue.enqueue_event(
                            _status_event(
                                task_id, context_id, last_chunk,
                                TaskState.working, final=False,
                            ),
                        )
                    last_chunk = chunk

                # Emit the final chunk as completed
                if last_chunk is not None:
                    await event_queue.enqueue_event(
                        _status_event(
                            task_id, context_id, last_chunk,
                            TaskState.completed, final=True,
                        ),
                    )
                else:
                    await event_queue.enqueue_event(
                        _status_event(
                            task_id, context_id, "",
                            TaskState.completed, final=True,
                        ),
                    )
            except Exception:
                logger.exception(
                    "Agent streaming failed context_id=%s",
                    context_id,
                )
                _error_msg = (
                    "I apologize, but I encountered an error "
                    "processing your request."
                )
                await event_queue.enqueue_event(
                    _status_event(
                        task_id, context_id, _error_msg,
                        TaskState.failed, final=True,
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

