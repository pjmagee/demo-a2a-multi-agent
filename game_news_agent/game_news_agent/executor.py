"""A2A executor for the Game News Agent."""

import json
import logging
from datetime import date, datetime
from typing import override

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    Artifact,
    DataPart,
    Part,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)
from a2a.utils import new_agent_text_message
from agents import Agent, Runner, Session, function_tool
from openai.types.responses import (
    EasyInputMessageParam,
    ResponseInputContentParam,
    ResponseInputItemParam,
    ResponseInputTextParam,
)
from shared.openai_session_helpers import ensure_context_id, get_or_create_session

from game_news_agent.game_service_kiota import RAWGKiotaClient

logger = logging.getLogger(__name__)


class _DateEncoder(json.JSONEncoder):
    """JSON encoder that serialises date/datetime to ISO format strings."""

    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

_AGENT_INSTRUCTIONS = """
You are a gaming news assistant backed by the live RAWG database.
You have four tools:
1. generate_gaming_report  — broad multi-section report across genres and a date range
2. search_games            — find a game by name or description to obtain its game_id
3. get_game_info           — fetch current metadata for a known game_id
4. analyze_game_reviews    — sentiment analysis of user reviews for a known game_id

Routing rules:
- Genres / dates / trends / news  →  generate_gaming_report
- Review / sentiment / "what do players think"  →  search_games → get_game_info → analyze_game_reviews
- If ambiguous or missing details, ask a short follow-up question.

NEVER fabricate game information. ALWAYS ground every response in tool outputs.
Tool calls that return "generated and delivered" mean the result was sent as an artifact;
summarise briefly, don't repeat content.
""".strip()


class GameNewsAgentExecutor(AgentExecutor):
    """Executor that drives an OpenAI Agent SDK agent whose tools emit A2A SSE events."""

    _sessions: dict[str, Session] = {}

    def _build_agent(
        self,
        event_queue: EventQueue,
        context_id: str,
        task_id: str | None,
        game_service: RAWGKiotaClient,
    ) -> Agent:
        """Build a per-request Agent with tools closed over the SSE event queue."""

        @function_tool
        async def generate_gaming_report(
            game_genres: list[str],
            date_from: str,
            date_to: str,
            game_modes: list[str],
        ) -> str:
            """Generate a multi-section gaming trends report for the given genres and date range.

            Args:
                game_genres: List of game genre names (e.g. ["action", "rpg"])
                date_from: Start date in ISO format (YYYY-MM-DD)
                date_to: End date in ISO format (YYYY-MM-DD)
                game_modes: List of game mode names (e.g. ["singleplayer", "multiplayer"])
            """
            from game_news_agent.agent import GameNewsAgent
            from game_news_agent.models import GameGenre, GameMode, GameReportRequest

            genres_display = ", ".join(game_genres)
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    context_id=context_id,
                    task_id=task_id or "",
                    final=False,
                    status=TaskStatus(
                        state=TaskState.working,
                        message=new_agent_text_message(
                            text=f"Generating gaming report for {genres_display} ({date_from} → {date_to})…",
                            context_id=context_id,
                            task_id=task_id,
                        ),
                    ),
                )
            )

            request = GameReportRequest(
                game_genres=[GameGenre(g.lower()) for g in game_genres],
                date_from=date.fromisoformat(date_from),
                date_to=date.fromisoformat(date_to),
                game_modes=[GameMode(m.lower()) for m in game_modes],
            )
            response = await GameNewsAgent().invoke(request, context_id)

            if response.validation_errors:
                return "Report generation failed: " + "; ".join(response.validation_errors)

            text_part = TextPart(
                text=response.report_markdown,
                metadata={"mime_type": "text/markdown", "fact_checked": response.fact_check_passed},
            )
            artifact = Artifact(
                artifact_id=f"gaming-report-{context_id}",
                name="Gaming Report",
                description=f"Gaming report for {genres_display}",
                parts=[Part(root=text_part)],
                metadata={
                    "fact_checked": response.fact_check_passed,
                    "generated_at": response.generated_at.isoformat(),
                    "date_range": {"from": date_from, "to": date_to},
                    "genres": game_genres,
                    "game_modes": game_modes,
                },
            )
            await event_queue.enqueue_event(
                TaskArtifactUpdateEvent(
                    context_id=context_id,
                    task_id=task_id or "",
                    artifact=artifact,
                    last_chunk=True,
                )
            )
            logger.info(f"Gaming report artifact enqueued: fact_checked={response.fact_check_passed}")
            return "Gaming report generated and delivered."

        @function_tool
        async def search_games(query: str) -> str:
            """Search for games by name.

            Returns a JSON list of matches with game_id, name, released, rating, metacritic.

            Use this to resolve a game name to a game_id before calling get_game_info or analyze_game_reviews.
            Results are ordered by RAWG relevance so the closest name match appears first.

            Args:
                query: Game name or partial name to search for (e.g. "Elden Ring", "Cyberpunk")
            """
            results = await game_service.search_games(
                query,
                page_size=5,
                search_precise=True,
                search_exact=False,
            )
            games = [
                {
                    "game_id": g.get("id"),
                    "name": g.get("name"),
                    "released": g.get("released"),
                    "rating": g.get("rating"),
                    "metacritic": g.get("metacritic"),
                }
                for g in (results or [])
            ]
            logger.info(f"search_games returned {len(games)} results for query={query!r}")
            return json.dumps(games, cls=_DateEncoder)

        @function_tool
        async def get_game_info(game_id: int) -> str:
            """Fetch current metadata for a known game by its RAWG game_id.

            Args:
                game_id: The RAWG numeric game identifier
            """
            game = await game_service.get_game_details(game_id)
            info = game_service._game_to_dict(game)  # noqa: SLF001
            logger.info(f"get_game_info returned data for game_id={game_id}")
            return json.dumps(info, cls=_DateEncoder)

        @function_tool
        async def analyze_game_reviews(game_id: int, review_count: int = 20) -> str:
            """Perform sentiment analysis on user reviews for a game.

            Args:
                game_id: The RAWG numeric game identifier
                review_count: How many reviews to analyse (default 20)
            """
            from game_news_agent.models import ReviewAnalysisRequest
            from game_news_agent.review_analyzer import ReviewAnalyzer

            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    context_id=context_id,
                    task_id=task_id or "",
                    final=False,
                    status=TaskStatus(
                        state=TaskState.working,
                        message=new_agent_text_message(
                            text=f"Analysing {review_count} reviews for game {game_id}…",
                            context_id=context_id,
                            task_id=task_id,
                        ),
                    ),
                )
            )

            request = ReviewAnalysisRequest(game_id=game_id, review_count=review_count)
            response = await ReviewAnalyzer().invoke(request, context_id)

            if response.validation_errors:
                return "Review analysis failed: " + "; ".join(response.validation_errors)

            text_part = TextPart(
                text=response.analysis_markdown,
                metadata={
                    "mime_type": "text/markdown",
                    "game_id": response.game.id,
                    "game_name": response.game.name,
                },
            )
            artifact = Artifact(
                artifact_id=f"review-analysis-{context_id}",
                name=f"Review Analysis: {response.game.name}",
                description=(
                    f"Sentiment analysis of {response.positive_reviews.review_count} positive and "
                    f"{response.negative_reviews.review_count} negative reviews"
                ),
                parts=[Part(root=text_part)],
                metadata={
                    "game_id": response.game.id,
                    "game_name": response.game.name,
                    "game_rating": response.game.rating,
                    "generated_at": response.generated_at.isoformat(),
                    "positive_themes": response.positive_reviews.common_themes,
                    "negative_themes": response.negative_reviews.common_themes,
                },
            )
            await event_queue.enqueue_event(
                TaskArtifactUpdateEvent(
                    context_id=context_id,
                    task_id=task_id or "",
                    artifact=artifact,
                    last_chunk=True,
                )
            )
            logger.info(f"Review analysis artifact enqueued for game_id={game_id}")
            return f"Review analysis for '{response.game.name}' generated and delivered."

        return Agent(
            name="GameNewsAgent",
            model="gpt-4o",
            instructions=_AGENT_INSTRUCTIONS,
            tools=[generate_gaming_report, search_games, get_game_info, analyze_game_reviews],
        )

    def _build_runner_input(self, context: RequestContext) -> str | list[ResponseInputItemParam]:
        """Convert A2A message parts into a Runner.run-compatible input.

        Produces a plain string when there is exactly one text part (simple case),
        or an OpenAI Responses API message list when the message carries a DataPart
        or multiple parts, so structured content isn't silently flattened to text.
        """
        if not context.message or not context.message.parts:
            return context.get_user_input()

        content_blocks: list[ResponseInputContentParam] = []
        for part in context.message.parts:
            if isinstance(part.root, TextPart):
                content_blocks.append(ResponseInputTextParam(type="input_text", text=part.root.text))
            elif isinstance(part.root, DataPart):
                raw = part.root.data
                if isinstance(raw, (dict, list)):
                    text = json.dumps(raw)
                elif isinstance(raw, bytes):
                    text = raw.decode("utf-8")
                else:
                    text = str(raw)
                content_blocks.append(ResponseInputTextParam(type="input_text", text=text))

        if not content_blocks:
            return context.get_user_input()

        # Single plain-text part — keep as string (no wrapping overhead)
        if len(content_blocks) == 1 and content_blocks[0]["type"] == "input_text":
            return content_blocks[0]["text"]

        # Mixed / multi-part — send as a proper Responses API user message
        return [EasyInputMessageParam(role="user", content=content_blocks)]  # type: ignore[list-item]

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Run the agent, letting it decide which tools to call based on the user's message."""
        context_id: str = ensure_context_id(context)
        logger.info(f"GameNewsAgentExecutor executing context_id={context_id}")

        try:
            runner_input = self._build_runner_input(context)
            logger.info(f"Runner input type={type(runner_input).__name__}, preview={str(runner_input)[:200]}")

            game_service = RAWGKiotaClient()
            agent = self._build_agent(event_queue, context_id, context.task_id, game_service)
            session = get_or_create_session(
                sessions=GameNewsAgentExecutor._sessions,
                context_id=context_id,
            )

            result = await Runner.run(starting_agent=agent, input=runner_input, session=session)

            final = (result.final_output or "").strip()
            if final:
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        context_id=context_id,
                        task_id=context.task_id or "",
                        final=True,
                        status=TaskStatus(
                            state=TaskState.completed,
                            message=new_agent_text_message(
                                text=final,
                                context_id=context_id,
                                task_id=context.task_id,
                            ),
                        ),
                    )
                )

        except Exception as e:
            logger.exception(f"Error executing GameNewsAgent: {e}")
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

    @override
    async def cancel(self, context: RequestContext) -> None:
        """Cancel the task."""
        logger.info(f"Cancel requested context_id={context.context_id}, task_id={context.task_id}")
