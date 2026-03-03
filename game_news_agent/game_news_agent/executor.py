"""A2A executor for the Game News Agent.

Architecture
------------
Thin adapter that delegates to GameNewsAgent (game_news_agent.agent), which owns
the full OpenAI Agent SDK parent + handoff pattern:

  GameNewsAgent (parent -- gpt-4o, handoffs)
  +-- GameNewsReportAgent   -- wraps GameNewsReportWorkflow (LangGraph, RAWG)
  +-- GameReviewAnalysisAgent -- wraps ReviewAnalysisWorkflow (LangGraph) + RAWG lookup tools

Artifacts are streamed to the EventQueue directly from within the subagent tools.
The parent's final text output is emitted here as the completed task message.
"""

import logging
from typing import override

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import TaskState, TaskStatus, TaskStatusUpdateEvent
from a2a.utils import new_agent_text_message
from shared.openai_session_helpers import ensure_context_id

from game_news_agent.agent import GameNewsAgent

logger = logging.getLogger(__name__)


class GameNewsAgentExecutor(AgentExecutor):
    """Thin A2A adapter -- delegates entirely to GameNewsAgent."""

    def __init__(self) -> None:
        self.agent = GameNewsAgent()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        context_id: str = ensure_context_id(context)
        logger.info(f"GameNewsAgentExecutor.execute context_id={context_id}")

        try:
            final_text = await self.agent.invoke(context, context_id, event_queue)
        except Exception as e:
            logger.exception(f"GameNewsAgent invocation failed context_id={context_id}")
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    context_id=context_id,
                    task_id=context.task_id or "",
                    final=True,
                    status=TaskStatus(
                        state=TaskState.failed,
                        message=new_agent_text_message(
                            text=f"An unexpected error occurred: {e}",
                            context_id=context_id,
                            task_id=context.task_id,
                        ),
                    ),
                )
            )
            return

        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                context_id=context_id,
                task_id=context.task_id or "",
                final=True,
                status=TaskStatus(
                    state=TaskState.completed,
                    message=new_agent_text_message(
                        text=final_text or "Done.",
                        context_id=context_id,
                        task_id=context.task_id,
                    ),
                ),
            )
        )

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.info(
            f"Cancel requested context_id={context.context_id}, task_id={context.task_id}"
        )
