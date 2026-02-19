"""A2A executor for the Game News Agent."""

import base64
import json
import logging
from typing import override

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import Artifact, DataPart, FilePart, FileWithBytes, Part, TaskArtifactUpdateEvent
from a2a.utils import new_agent_text_message
from shared.openai_session_helpers import ensure_context_id

from game_news_agent.agent import GameNewsAgent
from game_news_agent.models import GameReportRequest, GameReportResponse

logger = logging.getLogger(__name__)


class GameNewsAgentExecutor(AgentExecutor):
    """Executor that adapts A2A requests to the LangGraph gaming news agent."""

    def __init__(self) -> None:
        """Initialize the executor."""
        self.agent = GameNewsAgent()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute the gaming news agent request.

        Args:
            context: A2A request context
            event_queue: Event queue for sending responses (SSE)
        """

        context_id: str = ensure_context_id(context)
        logger.info(f"GameNewsAgentExecutor executing with context_id={context_id}")

        try:
            # Extract DataPart from context
            data_part = None
            if context.message and context.message.parts:
                for part in context.message.parts:
                    if isinstance(part.root, DataPart):
                        data_part = part.root
                        break

            if not data_part:
                # Fallback to user input as text
                logger.warning("No DataPart found, using text input")
                user_input_raw = context.get_user_input()
            else:
                # Parse DataPart JSON
                user_input_raw = data_part.data.decode("utf-8") if isinstance(data_part.data, bytes) else data_part.data
                preview = str(user_input_raw)[:200] if isinstance(user_input_raw, str) else str(user_input_raw)[:200]
                logger.info("Parsed DataPart: %s", preview)

            # Validate request against Pydantic model
            try:
                if isinstance(user_input_raw, dict):
                    request_data = user_input_raw
                elif isinstance(user_input_raw, str):
                    request_data = json.loads(user_input_raw)
                else:
                    msg = "Invalid input type"
                    raise TypeError(msg)

                request = GameReportRequest(**request_data)
                logger.info(
                    f"Validated request: genres={request.game_genres}, "
                    f"dates={request.date_from} to {request.date_to}, "
                    f"modes={request.game_modes}"
                )
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Invalid request format: {e}")
                await event_queue.enqueue_event(
                    event=new_agent_text_message(
                        context_id=context_id,
                        text=f"Error: Invalid request format. {str(e)}\n\n"
                        "Expected JSON with: game_genres (array), date_from (YYYY-MM-DD), "
                        "date_to (YYYY-MM-DD), game_modes (array)",
                        task_id=context.task_id,
                    )
                )
                return

            # Invoke the LangGraph agent
            logger.info("Invoking LangGraph workflow")
            response: GameReportResponse = await self.agent.invoke(context, context_id)

            # Check for validation errors
            if response.validation_errors:
                logger.warning(f"Validation errors occurred: {response.validation_errors}")
                await event_queue.enqueue_event(
                    event=new_agent_text_message(
                        context_id=context_id,
                        text="Report generation failed:\n\n" + "\n".join(f"- {err}" for err in response.validation_errors),
                        task_id=context.task_id,
                    )
                )
                return

            # Create artifact with markdown report as FilePart
            markdown_bytes = response.report_markdown.encode("utf-8")
            markdown_b64 = base64.b64encode(markdown_bytes).decode("utf-8")

            file_part = FilePart(
                file=FileWithBytes(
                    bytes=markdown_b64,
                    mime_type="text/markdown",
                    name="gaming_report.md",
                ),
                metadata={
                    "fact_checked": response.fact_check_passed,
                    "genre_count": len(request.game_genres),
                }
            )

            artifact = Artifact(
                artifact_id=f"gaming-report-{context_id}",
                name="Gaming Report",
                description=f"Gaming report for {', '.join(g.value for g in request.game_genres)}",
                parts=[Part(root=file_part)],
                metadata={
                    "fact_checked": response.fact_check_passed,
                    "generated_at": response.generated_at.isoformat(),
                    "date_range": {
                        "from": request.date_from.isoformat(),
                        "to": request.date_to.isoformat(),
                    },
                    "genres": [g.value for g in request.game_genres],
                    "game_modes": [m.value for m in request.game_modes],
                },
            )

            logger.info(f"Enqueueing artifact: fact_checked={response.fact_check_passed}")
            await event_queue.enqueue_event(
                event=TaskArtifactUpdateEvent(
                    context_id=context_id,
                    task_id=context.task_id or "",
                    artifact=artifact,
                    last_chunk=True,
                )
            )

        except Exception as e:
            logger.exception(f"Error executing GameNewsAgent: {e}")
            await event_queue.enqueue_event(
                event=new_agent_text_message(
                    context_id=context_id,
                    text=f"An unexpected error occurred: {str(e)}",
                    task_id=context.task_id,
                )
            )

    @override
    async def cancel(self, context: RequestContext) -> None:
        """Cancel the task (not implemented for LangGraph workflow).

        Args:
            context: A2A request context
        """
        logger.info(f"Cancel requested for context_id={context.context_id}, task_id={context.task_id}")
