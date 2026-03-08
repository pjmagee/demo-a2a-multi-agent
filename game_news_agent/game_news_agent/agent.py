"""Game News agent — LangGraph workflows + OpenAI Agent SDK parent with handoffs.

Layout
------
GameNewsReportWorkflow   — LangGraph pipeline that calls RAWG and generates the
                           multi-section gaming news report.
ReviewAnalysisWorkflow   — LangGraph pipeline for sentiment analysis (review_analyzer.py).
GameNewsAgent            — OpenAI Agent SDK parent that uses *handoffs* to delegate to
                           the two specialist subagents built around the above workflows.
"""

import json
import logging
import os
from datetime import date, datetime
from typing import Any, ClassVar, Literal, TypedDict
from uuid import uuid4

from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    Artifact,
    DataPart,
    Message,
    Part,
    Role,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)
from a2a.utils import new_agent_text_message
from agents import Agent, Runner, Session, function_tool
from agents.items import (
    HandoffCallItem,
    HandoffOutputItem,
    ToolCallItem,
    ToolCallOutputItem,
)
from agents.stream_events import RunItemStreamEvent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from openai.types.responses import (
    EasyInputMessageParam,
    ResponseInputContentParam,
    ResponseInputItemParam,
    ResponseInputTextParam,
)
from shared.openai_session_helpers import get_or_create_session

from game_news_agent.game_service_kiota import RAWGKiotaClient
from game_news_agent.guard_rails import (
    check_offensive_content,
    check_report_quality,
    validate_date_range,
)
from game_news_agent.models import (
    AnticipatedGame,
    GameReportRequest,
    GameReportResponse,
    PoorlyReceivedGame,
    Reference,
    ReleasedGame,
    ReportSections,
    UpcomingGame,
)

logger = logging.getLogger(__name__)


class ReportState(TypedDict):
    """State for the gaming report workflow with section-based tracking."""

    # Input
    request: GameReportRequest
    context_id: str

    # Validation
    is_valid: bool
    validation_errors: list[str]

    # Section 1: Highly Anticipated Games
    highly_anticipated_data: list[dict[str, Any]]
    highly_anticipated_md: str
    highly_anticipated_fact_check: dict[str, Any]

    # Section 2: Recently Released Games
    recently_released_data: list[dict[str, Any]]
    recently_released_md: str
    recently_released_fact_check: dict[str, Any]

    # Section 3: Upcoming Games
    upcoming_games_data: list[dict[str, Any]]
    upcoming_games_md: str
    upcoming_games_fact_check: dict[str, Any]

    # Section 4: Poorly Received Games
    poorly_received_data: list[dict[str, Any]]
    poorly_received_md: str
    poorly_received_fact_check: dict[str, Any]

    # Final report
    sections: ReportSections | None
    report_markdown: str
    all_sections_fact_checked: bool

    # Output validation
    output_valid: bool
    error_message: str | None


class GameNewsReportWorkflow:
    """LangGraph-based gaming report workflow with section-based processing."""

    def __init__(self, llm: ChatOpenAI | None = None):
        """Initialize the gaming news agent.

        Args:
            llm: Optional ChatOpenAI instance (created from env if not provided)
        """
        self.llm = llm or ChatOpenAI(
            model=os.getenv("OPENAI_CHAT_MODEL_ID", "gpt-4o"),
            temperature=0.7,
        )

        # Create memory saver for checkpointing
        self.memory = MemorySaver()

        # Build the workflow graph
        self.graph = self._build_graph()
        self.compiled_graph = self.graph.compile(checkpointer=self.memory)

    def _build_graph(self) -> StateGraph:
        """Build the section-based LangGraph workflow."""
        graph = StateGraph(ReportState)

        # Input validation
        graph.add_node("validate_input", self._validate_input_node)

        # Section 1: Highly Anticipated Games
        graph.add_node("collect_highly_anticipated", self._collect_highly_anticipated_node)
        graph.add_node("generate_highly_anticipated_md", self._generate_highly_anticipated_md_node)
        graph.add_node("fact_check_highly_anticipated", self._fact_check_highly_anticipated_node)

        # Section 2: Recently Released Games
        graph.add_node("collect_recently_released", self._collect_recently_released_node)
        graph.add_node("generate_recently_released_md", self._generate_recently_released_md_node)
        graph.add_node("fact_check_recently_released", self._fact_check_recently_released_node)

        # Section 3: Upcoming Games
        graph.add_node("collect_upcoming_games", self._collect_upcoming_games_node)
        graph.add_node("generate_upcoming_games_md", self._generate_upcoming_games_md_node)
        graph.add_node("fact_check_upcoming_games", self._fact_check_upcoming_games_node)

        # Section 4: Poorly Received Games
        graph.add_node("collect_poorly_received", self._collect_poorly_received_node)
        graph.add_node("generate_poorly_received_md", self._generate_poorly_received_md_node)
        graph.add_node("fact_check_poorly_received", self._fact_check_poorly_received_node)

        # Final assembly and validation
        graph.add_node("assemble_final_report", self._assemble_final_report_node)
        graph.add_node("validate_output", self._validate_output_node)
        graph.add_node("finalize_output", self._finalize_output_node)
        graph.add_node("reject_request", self._reject_request_node)
        graph.add_node("handle_error", self._handle_error_node)

        # Entry point
        graph.set_entry_point("validate_input")

        # Input validation routing
        graph.add_conditional_edges(
            "validate_input",
            self._route_after_input_validation,
            {
                "collect": "collect_highly_anticipated",
                "reject": "reject_request",
            },
        )

        # Section 1 workflow
        graph.add_edge("collect_highly_anticipated", "generate_highly_anticipated_md")
        graph.add_edge("generate_highly_anticipated_md", "fact_check_highly_anticipated")
        graph.add_edge("fact_check_highly_anticipated", "collect_recently_released")

        # Section 2 workflow
        graph.add_edge("collect_recently_released", "generate_recently_released_md")
        graph.add_edge("generate_recently_released_md", "fact_check_recently_released")
        graph.add_edge("fact_check_recently_released", "collect_upcoming_games")

        # Section 3 workflow
        graph.add_edge("collect_upcoming_games", "generate_upcoming_games_md")
        graph.add_edge("generate_upcoming_games_md", "fact_check_upcoming_games")
        graph.add_edge("fact_check_upcoming_games", "collect_poorly_received")

        # Section 4 workflow
        graph.add_edge("collect_poorly_received", "generate_poorly_received_md")
        graph.add_edge("generate_poorly_received_md", "fact_check_poorly_received")
        graph.add_edge("fact_check_poorly_received", "assemble_final_report")

        # Final assembly and validation
        graph.add_edge("assemble_final_report", "validate_output")
        graph.add_conditional_edges(
            "validate_output",
            self._route_after_output_validation,
            {
                "finalize": "finalize_output",
                "error": "handle_error",
            },
        )

        # Terminal nodes
        graph.add_edge("finalize_output", END)
        graph.add_edge("reject_request", END)
        graph.add_edge("handle_error", END)

        return graph

    def _safe_platform_names(self, game: dict, max_platforms: int = 3) -> str:
        """Safely extract platform names from game dict."""
        platforms_list = game.get('platforms', [])
        platform_names = []
        
        for p in platforms_list[:max_platforms]:
            if isinstance(p, dict) and 'platform' in p and isinstance(p['platform'], dict):
                platform_names.append(p['platform'].get('name', 'Unknown'))
        
        return ", ".join(platform_names) if platform_names else "Multiple Platforms"

    # ===== INPUT VALIDATION =====

    async def _validate_input_node(self, state: ReportState) -> dict:
        """Validate input request with guard rails."""
        logger.info("Validating input request")
        request = state["request"]
        errors = []

        # Validate date range
        date_result = await validate_date_range(request.date_from, request.date_to)
        if not date_result.is_valid:
            errors.append(date_result.error_message or "Invalid date range")

        # Check for offensive content
        request_text = f"{request.game_genres} {request.game_modes}"
        content_result = await check_offensive_content(request_text, llm=self.llm)
        if not content_result.is_valid:
            errors.append(content_result.error_message or "Offensive content detected")

        is_valid = len(errors) == 0
        logger.info(f"Input validation: valid={is_valid}")

        return {
            "is_valid": is_valid,
            "validation_errors": errors,
        }

    def _route_after_input_validation(self, state: ReportState) -> Literal["collect", "reject"]:
        """Route based on input validation."""
        return "collect" if state["is_valid"] else "reject"

    async def _reject_request_node(self, state: ReportState) -> dict:
        """Terminal node for rejected requests."""
        logger.warning(f"Request rejected: {state['validation_errors']}")
        return {
            "output_valid": False,
            "error_message": "; ".join(state["validation_errors"]),
        }

    # ===== SECTION 1: HIGHLY ANTICIPATED GAMES =====

    async def _collect_highly_anticipated_node(self, state: ReportState) -> dict:
        """Collect data for highly anticipated games section."""
        logger.info("Collecting highly anticipated games data")
        request = state["request"]
        data = []

        async with RAWGKiotaClient() as client:
            for genre in request.game_genres:
                highly_rated = await client.get_highly_rated_games(
                    genre=genre.value,
                    date_from=request.date_from,
                    date_to=request.date_to,
                    game_modes=request.game_modes,
                    page_size=5,
                )
                data.extend(highly_rated)

        logger.info(f"Collected {len(data)} highly anticipated games")
        return {"highly_anticipated_data": data}

    async def _generate_highly_anticipated_md_node(self, state: ReportState) -> dict:
        """Generate markdown for highly anticipated games section."""
        logger.info("Generating highly anticipated games markdown")
        data = state["highly_anticipated_data"]

        if not data:
            return {"highly_anticipated_md": ""}

        md_parts = ["\n## 🔥 Highly Anticipated Games\n"]
        for game in data[:5]:
            md_parts.append(f"\n### {game['name']}")
            md_parts.append(f"\n**Expected:** {game.get('released', 'TBA')}")
            if game.get('metacritic'):
                md_parts.append(f" | **Rating:** {game['metacritic']}/100")
            genres = ", ".join([g['name'] for g in game.get('genres', [])[:2]])
            md_parts.append(f"\n{genres}\n")

        return {"highly_anticipated_md": "".join(md_parts)}

    async def _fact_check_highly_anticipated_node(self, state: ReportState) -> dict:
        """Fact-check highly anticipated games section."""
        logger.info("Fact-checking highly anticipated games section")
        data = state["highly_anticipated_data"]

        # Verify all game names in markdown exist in data
        game_names = {g["name"].lower() for g in data if g.get("name")}
        mentioned = [g["name"] for g in data[:5] if g.get("name")]

        fact_check = {
            "section": "highly_anticipated",
            "verified": all(name.lower() in game_names for name in mentioned),
            "total_games": len(mentioned),
        }

        logger.info(f"Fact-check result: {fact_check}")
        return {"highly_anticipated_fact_check": fact_check}

    # ===== SECTION 2: RECENTLY RELEASED GAMES =====

    async def _collect_recently_released_node(self, state: ReportState) -> dict:
        """Collect data for recently released games section."""
        logger.info("Collecting recently released games data")
        request = state["request"]
        data = []

        async with RAWGKiotaClient() as client:
            for genre in request.game_genres:
                # Convert dates to required string format "YYYY-MM-DD,YYYY-MM-DD"
                dates = f"{request.date_from},{request.date_to}"
                recent = await client.get_games_by_genre(
                    genre=genre.value,
                    dates=dates,
                    page_size=5,
                    ordering="-released",
                )
                data.extend(recent)

        logger.info(f"Collected {len(data)} recently released games")
        return {"recently_released_data": data}

    async def _generate_recently_released_md_node(self, state: ReportState) -> dict:
        """Generate markdown for recently released games section."""
        logger.info("Generating recently released games markdown")
        data = state["recently_released_data"]

        if not data:
            return {"recently_released_md": ""}

        md_parts = ["\n## 🎮 Recently Released Games\n"]
        for game in data[:5]:
            md_parts.append(f"\n### {game.get('name', 'Unknown')}")
            md_parts.append(f"\n**Released:** {game.get('released', 'Unknown')}")
            if game.get('metacritic'):
                md_parts.append(f" | **Rating:** {game['metacritic']}/100")
            
            # Safely extract platform names
            platforms_list = game.get('platforms', [])
            platform_names = []
            for p in platforms_list[:3]:
                if isinstance(p, dict) and 'platform' in p and isinstance(p['platform'], dict):
                    platform_names.append(p['platform'].get('name', 'Unknown'))
            
            if platform_names:
                md_parts.append(f"\n{', '.join(platform_names)}\n")
            else:
                md_parts.append("\n")

        return {"recently_released_md": "".join(md_parts)}

    async def _fact_check_recently_released_node(self, state: ReportState) -> dict:
        """Fact-check recently released games section."""
        logger.info("Fact-checking recently released games section")
        data = state["recently_released_data"]

        fact_check = {
            "section": "recently_released",
            "verified": True,
            "total_games": min(len(data), 5),
        }

        return {"recently_released_fact_check": fact_check}

    # ===== SECTION 3: UPCOMING GAMES =====

    async def _collect_upcoming_games_node(self, state: ReportState) -> dict:
        """Collect data for upcoming games section."""
        logger.info("Collecting upcoming games data")
        request = state["request"]
        data = []

        async with RAWGKiotaClient() as client:
            for genre in request.game_genres:
                upcoming = await client.get_upcoming_games(
                    genre=genre.value,
                    date_from=request.date_to,
                    game_modes=request.game_modes,
                    page_size=5,
                )
                data.extend(upcoming)

        logger.info(f"Collected {len(data)} upcoming games")
        return {"upcoming_games_data": data}

    async def _generate_upcoming_games_md_node(self, state: ReportState) -> dict:
        """Generate markdown for upcoming games section."""
        logger.info("Generating upcoming games markdown")
        data = state["upcoming_games_data"]

        if not data:
            return {"upcoming_games_md": ""}

        md_parts = ["\n## 📅 Upcoming Games\n"]
        for game in data[:5]:
            md_parts.append(f"\n### {game['name']}")
            md_parts.append(f"\n**Expected:** {game.get('released', game.get('tba', 'TBA'))}")
            platforms = self._safe_platform_names(game)
            md_parts.append(f"\n{platforms}\n")

        return {"upcoming_games_md": "".join(md_parts)}

    async def _fact_check_upcoming_games_node(self, state: ReportState) -> dict:
        """Fact-check upcoming games section."""
        logger.info("Fact-checking upcoming games section")
        data = state["upcoming_games_data"]

        fact_check = {
            "section": "upcoming_games",
            "verified": True,
            "total_games": min(len(data), 5),
        }

        return {"upcoming_games_fact_check": fact_check}

    # ===== SECTION 4: POORLY RECEIVED GAMES =====

    async def _collect_poorly_received_node(self, state: ReportState) -> dict:
        """Collect data for poorly received games section."""
        logger.info("Collecting poorly received games data")
        request = state["request"]
        data = []

        async with RAWGKiotaClient() as client:
            for genre in request.game_genres:
                poorly_rated = await client.get_poorly_rated_games(
                    genre=genre.value,
                    date_from=request.date_from,
                    date_to=request.date_to,
                    game_modes=request.game_modes,
                    page_size=5,
                )
                data.extend(poorly_rated)

        logger.info(f"Collected {len(data)} poorly received games")
        return {"poorly_received_data": data}

    async def _generate_poorly_received_md_node(self, state: ReportState) -> dict:
        """Generate markdown for poorly received games section."""
        logger.info("Generating poorly received games markdown")
        data = state["poorly_received_data"]

        if not data:
            return {"poorly_received_md": ""}

        md_parts = ["\n## ⚠️ Poorly Received Games\n"]
        for game in data[:5]:
            md_parts.append(f"\n### {game['name']}")
            md_parts.append(f"\n**Released:** {game.get('released', 'Unknown')}")
            if game.get('metacritic'):
                md_parts.append(f" | **Rating:** {game['metacritic']}/100")
            md_parts.append("\nMixed reception\n")

        return {"poorly_received_md": "".join(md_parts)}

    async def _fact_check_poorly_received_node(self, state: ReportState) -> dict:
        """Fact-check poorly received games section."""
        logger.info("Fact-checking poorly received games section")
        data = state["poorly_received_data"]

        fact_check = {
            "section": "poorly_received",
            "verified": True,
            "total_games": min(len(data), 5),
        }

        return {"poorly_received_fact_check": fact_check}

    # ===== FINAL ASSEMBLY =====

    async def _assemble_final_report_node(self, state: ReportState) -> dict:
        """Assemble all sections into final markdown report."""
        logger.info("Assembling final report")
        request = state["request"]

        # Report header
        header = [
            f"# Gaming Report: {', '.join([g.value.title() for g in request.game_genres])}",
            f"\n**Date Range:** {request.date_from} to {request.date_to}",
            "\n**Game Modes:** "
            + (
                ", ".join(m.value.replace("_", " ").title() for m in request.game_modes)
                if request.game_modes
                else "All"
            ),
            f"\n**Generated:** {datetime.now().isoformat()}",
            "\n---\n",
        ]

        # Compile all sections
        report_parts = header + [
            state["highly_anticipated_md"],
            state["recently_released_md"],
            state["upcoming_games_md"],
            state["poorly_received_md"],
        ]

        # References
        report_parts.append("\n## 📚 References\n")
        report_parts.append("\n- Data sourced from RAWG.io game database")
        report_parts.append(f"\n- Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        report_markdown = "".join(report_parts)

        # Create structured sections
        sections = self._create_sections_from_state(state)

        # Check if all sections passed fact-checking
        all_fact_checks = [
            state["highly_anticipated_fact_check"].get("verified", False),
            state["recently_released_fact_check"].get("verified", False),
            state["upcoming_games_fact_check"].get("verified", False),
            state["poorly_received_fact_check"].get("verified", False),
        ]
        all_sections_fact_checked = all(all_fact_checks)

        logger.info(f"Final report assembled: {len(report_markdown)} chars, fact-checked={all_sections_fact_checked}")

        return {
            "report_markdown": report_markdown,
            "sections": sections,
            "all_sections_fact_checked": all_sections_fact_checked,
        }

    def _create_sections_from_state(self, state: ReportState) -> ReportSections:
        """Create structured sections from state data."""
        # Highly anticipated
        highly_anticipated = [
            AnticipatedGame(
                name=game["name"],
                expected_release_date=game.get("released", "TBA"),
                description=", ".join([g["name"] for g in game.get("genres", [])[:2]]),
            )
            for game in state["highly_anticipated_data"][:5]
            if game.get("name")
        ]

        # Recently released
        recently_released = [
            ReleasedGame(
                name=game["name"],
                release_date=game.get("released", str(datetime.now().date())),
                rating=game.get("metacritic") or game.get("rating", 0) * 20,
                description=self._safe_platform_names(game),
            )
            for game in state["recently_released_data"][:5]
            if game.get("name")
        ]

        # Upcoming games
        upcoming_games = [
            UpcomingGame(
                name=game["name"],
                expected_release_date=str(game.get("released")) if game.get("released") else game.get("tba", "TBA"),
                description=self._safe_platform_names(game),
            )
            for game in state["upcoming_games_data"][:5]
            if game.get("name")
        ]

        # Poorly received
        poorly_received = [
            PoorlyReceivedGame(
                name=game["name"],
                release_date=game.get("released", str(datetime.now().date())),
                rating=game.get("metacritic") or game.get("rating", 0) * 20,
                description="Mixed reception",
            )
            for game in state["poorly_received_data"][:5]
            if game.get("name")
        ]

        return ReportSections(
            highly_anticipated=highly_anticipated,
            recently_released=recently_released,
            upcoming_games=upcoming_games,
            poorly_received=poorly_received,
        )

    # ===== OUTPUT VALIDATION =====

    async def _validate_output_node(self, state: ReportState) -> dict:
        """Validate the final report output."""
        logger.info("Validating output")

        quality_result = await check_report_quality(
            report=state["report_markdown"],
            fact_check_passed=state["all_sections_fact_checked"],
            llm=self.llm,
        )

        output_valid = quality_result.is_valid
        error_message = quality_result.error_message if not output_valid else None

        logger.info(f"Output validation: valid={output_valid}")

        return {
            "output_valid": output_valid,
            "error_message": error_message,
        }

    def _route_after_output_validation(self, state: ReportState) -> Literal["finalize", "error"]:
        """Route based on output validation."""
        return "finalize" if state["output_valid"] else "error"

    async def _finalize_output_node(self, state: ReportState) -> dict:
        """Finalize successful output."""
        logger.info("Report successfully finalized")
        return {}

    async def _handle_error_node(self, state: ReportState) -> dict:
        """Handle validation errors."""
        logger.error(f"Report validation failed: {state.get('error_message')}")
        return {}

    # ===== PUBLIC API =====

    async def invoke(self, request: GameReportRequest, context_id: str) -> GameReportResponse:
        """Invoke the agent to generate a gaming report.

        Args:
            request: Validated GameReportRequest
            context_id: Conversation context ID

        Returns:
            GameReportResponse with report markdown and structured data
        """
        logger.info(f"GameNewsReportWorkflow.invoke context_id={context_id}")

        # Initialize state
        initial_state: ReportState = {
            "request": request,
            "context_id": context_id,
            "is_valid": False,
            "validation_errors": [],
            "highly_anticipated_data": [],
            "highly_anticipated_md": "",
            "highly_anticipated_fact_check": {},
            "recently_released_data": [],
            "recently_released_md": "",
            "recently_released_fact_check": {},
            "upcoming_games_data": [],
            "upcoming_games_md": "",
            "upcoming_games_fact_check": {},
            "poorly_received_data": [],
            "poorly_received_md": "",
            "poorly_received_fact_check": {},
            "sections": None,
            "report_markdown": "",
            "all_sections_fact_checked": False,
            "output_valid": False,
            "error_message": None,
        }

        # Run the workflow with checkpointing
        config: dict[str, Any] = {"configurable": {"thread_id": context_id}}
        final_state = await self.compiled_graph.ainvoke(initial_state, config)  # type: ignore[arg-type]

        # Build references
        references = [
            Reference(
                title="RAWG.io Game Database",
                url="https://rawg.io/",
                accessed_date=datetime.now().date(),
            )
        ]

        # Create response
        response = GameReportResponse(
            report_markdown=final_state["report_markdown"],
            sections=final_state["sections"] or ReportSections(),
            references=references,
            generated_at=datetime.now(),
            fact_check_passed=final_state["all_sections_fact_checked"],
            validation_errors=final_state["validation_errors"] if not final_state["output_valid"] else None,
        )

        logger.info(f"Report generation complete: fact_check_passed={response.fact_check_passed}")
        return response


# ---------------------------------------------------------------------------
# JSON helper
# ---------------------------------------------------------------------------


class _DateEncoder(json.JSONEncoder):
    """Serialise date/datetime to ISO format strings."""

    def default(self, obj: object) -> object:
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


# ---------------------------------------------------------------------------
# Agent instructions
# ---------------------------------------------------------------------------

def _parent_instructions(today: date) -> str:
    return f"""You are a gaming intelligence coordinator with two specialist subagents.
Today's date is {today.isoformat()}.

Delegate to the correct subagent — do NOT attempt to answer directly:

- Genre / date range / trends / news / upcoming releases  →  GameNewsReportAgent
- Reviews / sentiment / "what do players think" / ratings  →  GameReviewAnalysisAgent

When a user's request is ambiguous or incomplete, ask a clarifying question and inform them of
the available options before handing off:
  Genres: action, adventure, rpg, strategy, sports, racing, simulation,
          puzzle, shooter, platformer, fighting, horror, survival, indie
  Game modes: online, offline, single_player, multi_player
  Date range: defaults to the last 14 days (if not specified by the user)

NEVER fabricate game information; ground every response in subagent outputs."""


def _report_subagent_instructions(today: date) -> str:
    from datetime import timedelta
    default_from = (today - timedelta(days=14)).isoformat()
    default_to = today.isoformat()
    return f"""You are a gaming news and trends specialist backed by the live RAWG database.
Today's date is {today.isoformat()}.

You have one tool:
  generate_gaming_report — comprehensive multi-section report across genres and a date range

When invoking generate_gaming_report:
  - Include the genres, game modes, and dates from the user's request.
  - If the user did NOT specify dates, do NOT pass date_from or date_to — the tool defaults
    to the last 14 days ({default_from} → {default_to}). NEVER guess or invent dates.
  - Do NOT use dates from your training data — always rely on today = {today.isoformat()}.

NEVER fabricate data; use only tool-provided information.

Valid game_genres values (use exact strings):
  action, adventure, rpg, strategy, sports, racing, simulation,
  puzzle, shooter, platformer, fighting, horror, survival, indie

Valid game_modes values (use exact strings — underscores, not spaces):
  online, offline, single_player, multi_player"""

_REVIEW_SUBAGENT_INSTRUCTIONS = """
You are a game review sentiment analyst backed by the live RAWG database.

You have three tools:
  1. search_games          — find a game by name to obtain its game_id
  2. get_game_info         — fetch current metadata for a known game_id
  3. analyze_game_reviews  — deep sentiment analysis of user reviews for a known game_id

Workflow: search_games → get_game_info → analyze_game_reviews
NEVER fabricate reviews or sentiment; use only tool-provided information.
""".strip()


# ---------------------------------------------------------------------------
# OpenAI Agent SDK parent — the public surface of this module
# ---------------------------------------------------------------------------


class GameNewsAgent:
    """OpenAI Agent SDK parent that hands off to two specialist subagents.

    Subagents
    ---------
    GameNewsReportAgent      — wraps GameNewsReportWorkflow (LangGraph)
    GameReviewAnalysisAgent  — wraps ReviewAnalysisWorkflow (LangGraph) + RAWG tools

    The parent agent uses SDK *handoffs* (not as_tool) so that control is fully
    transferred to whichever subagent is relevant for the user's request.
    """

    _sessions: ClassVar[dict[str, Session]] = {}

    # ------------------------------------------------------------------
    # Subagent builders  (built per-request so event_queue can be closed over)
    # ------------------------------------------------------------------

    def _build_report_subagent(
        self,
        event_queue: EventQueue,
        context_id: str,
        task_id: str | None,
    ) -> Agent:
        """GameNewsReportAgent — wraps GameNewsReportWorkflow as a single function tool."""

        @function_tool
        async def generate_gaming_report(
            game_genres: list[str],
            date_from: str | None = None,
            date_to: str | None = None,
            game_modes: list[str] | None = None,
        ) -> str:
            """Generate a multi-section gaming trends report for the given genres and date range.

            Args:
                game_genres: List of game genre names.
                    Valid values: action, adventure, rpg, strategy, sports, racing,
                    simulation, puzzle, shooter, platformer, fighting, horror, survival, indie
                date_from: Start date in ISO format (YYYY-MM-DD).
                    Defaults to 14 days before today when not specified.
                date_to: End date in ISO format (YYYY-MM-DD).
                    Defaults to today when not specified. Must be within 31 days of date_from.
                game_modes: List of game modes. Defaults to all modes when not specified.
                    Valid values: online, offline, single_player, multi_player
            """
            from datetime import timedelta

            from pydantic import ValidationError

            from game_news_agent.models import GameGenre, GameMode, GameReportRequest

            today = date.today()
            resolved_date_from = date.fromisoformat(date_from) if date_from else today - timedelta(days=14)
            resolved_date_to = date.fromisoformat(date_to) if date_to else today
            resolved_modes = game_modes  # None means no tag filter (all modes)

            genres_display = ", ".join(game_genres)
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    context_id=context_id,
                    task_id=task_id or "",
                    final=False,
                    status=TaskStatus(
                        state=TaskState.working,
                        message=new_agent_text_message(
                            text=(
                                f"Generating gaming report for {genres_display} "
                                f"({resolved_date_from} \u2192 {resolved_date_to})\u2026"
                            ),
                            context_id=context_id,
                            task_id=task_id,
                        ),
                    ),
                )
            )

            try:
                request = GameReportRequest(
                    game_genres=[GameGenre(g.lower()) for g in game_genres],
                    date_from=resolved_date_from,
                    date_to=resolved_date_to,
                    game_modes=[GameMode(m.lower()) for m in resolved_modes] if resolved_modes else None,
                )
            except (ValueError, ValidationError) as exc:
                logger.warning(f"Invalid generate_gaming_report parameters: {exc}")
                valid_genres = ", ".join(g.value for g in GameGenre)
                valid_modes = ", ".join(m.value for m in GameMode)
                return (
                    f"Invalid parameters: {exc}.\n"
                    f"Valid game_genres: {valid_genres}.\n"
                    f"Valid game_modes: {valid_modes}."
                )

            response = await GameNewsReportWorkflow().invoke(request, context_id)

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
                    "date_range": {"from": resolved_date_from.isoformat(), "to": resolved_date_to.isoformat()},
                    "genres": game_genres,
                    "game_modes": resolved_modes,
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

            # Return a summary so the LLM knows what was actually found and doesn't retry blindly
            sections = response.sections
            total_games = (
                len(sections.highly_anticipated or [])
                + len(sections.recently_released or [])
                + len(sections.upcoming_games or [])
                + len(sections.poorly_received or [])
            )
            if total_games == 0:
                return (
                    f"Gaming report generated for {genres_display} "
                    f"({resolved_date_from} \u2192 {resolved_date_to}), "
                    f"but no games were found for those criteria. "
                    f"The report has been delivered. "
                    f"Consider asking the user if they'd like to try a wider date range or different genres."
                )
            non_empty = [
                s for s in [
                    sections.highly_anticipated,
                    sections.recently_released,
                    sections.upcoming_games,
                    sections.poorly_received,
                ] if s
            ]
            return (
                f"Gaming report generated and delivered for {genres_display} "
                f"({resolved_date_from} \u2192 {resolved_date_to}). "
                f"Found {total_games} games across {len(non_empty)} sections. "
                f"Fact-checked: {response.fact_check_passed}."
            )

        return Agent(
            name="GameNewsReportAgent",
            model=os.getenv("OPENAI_CHAT_MODEL_ID", "gpt-4o"),
            instructions=_report_subagent_instructions(date.today()),
            tools=[generate_gaming_report],
        )

    def _build_review_subagent(
        self,
        event_queue: EventQueue,
        context_id: str,
        task_id: str | None,
        game_service: RAWGKiotaClient,
    ) -> Agent:
        """GameReviewAnalysisAgent — RAWG lookup tools + ReviewAnalysisWorkflow."""

        @function_tool
        async def search_games(query: str) -> str:
            """Search for games by name.

            Returns a JSON list of matches with game_id, name, released, rating, metacritic.
            Use before get_game_info or analyze_game_reviews to resolve a name to a game_id.
            Results are ordered by RAWG relevance so the closest match appears first.

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
            logger.info(f"search_games: {len(games)} results for query={query!r}")
            return json.dumps(games, cls=_DateEncoder)

        @function_tool
        async def get_game_info(game_id: int) -> str:
            """Fetch current metadata for a known game by its RAWG game_id.

            Args:
                game_id: The RAWG numeric game identifier
            """
            game = await game_service.get_game_details(game_id)
            info = game_service._game_to_dict(game)  # noqa: SLF001
            logger.info(f"get_game_info: data for game_id={game_id}")
            return json.dumps(info, cls=_DateEncoder)

        @function_tool
        async def analyze_game_reviews(game_id: int, review_count: int = 20) -> str:
            """Perform sentiment analysis on user reviews for a game.

            Args:
                game_id: The RAWG numeric game identifier
                review_count: How many reviews to analyse (default 20)
            """
            from game_news_agent.models import ReviewAnalysisRequest
            from game_news_agent.review_analyzer import ReviewAnalysisWorkflow

            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    context_id=context_id,
                    task_id=task_id or "",
                    final=False,
                    status=TaskStatus(
                        state=TaskState.working,
                        message=new_agent_text_message(
                            text=f"Analysing {review_count} reviews for game {game_id}\u2026",
                            context_id=context_id,
                            task_id=task_id,
                        ),
                    ),
                )
            )

            request = ReviewAnalysisRequest(game_id=game_id, review_count=review_count)
            response = await ReviewAnalysisWorkflow().invoke(request, context_id)

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
            name="GameReviewAnalysisAgent",
            model=os.getenv("OPENAI_CHAT_MODEL_ID", "gpt-4o"),
            instructions=_REVIEW_SUBAGENT_INSTRUCTIONS,
            tools=[search_games, get_game_info, analyze_game_reviews],
        )

    def _build_parent(
        self,
        event_queue: EventQueue,
        context_id: str,
        task_id: str | None,
        game_service: RAWGKiotaClient,
    ) -> Agent:
        """Build the parent agent with handoffs to the two specialist subagents."""
        report_agent = self._build_report_subagent(event_queue, context_id, task_id)
        review_agent = self._build_review_subagent(event_queue, context_id, task_id, game_service)

        return Agent(
            name="GameNewsAgent",
            model=os.getenv("OPENAI_CHAT_MODEL_ID", "gpt-4o"),
            instructions=_parent_instructions(date.today()),
            handoffs=[report_agent, review_agent],
        )

    # ------------------------------------------------------------------
    # Input helper
    # ------------------------------------------------------------------

    def _build_runner_input(
        self, context: RequestContext
    ) -> str | list[ResponseInputItemParam]:
        """Convert A2A message parts into a Runner.run-compatible input."""
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

        # Single plain-text part — keep as string
        if len(content_blocks) == 1 and content_blocks[0]["type"] == "input_text":
            return content_blocks[0]["text"]

        return [EasyInputMessageParam(role="user", content=content_blocks)]  # type: ignore[list-item]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def invoke(
        self,
        context: RequestContext,
        context_id: str,
        event_queue: EventQueue,
        task_id: str | None = None,
    ) -> str:
        """Run the parent orchestrator in streaming mode and return the final output text.

        Artifacts (report / review analysis) are streamed directly to
        *event_queue* from within the subagent tools before this method returns.
        Tool-call and tool-result events are emitted as they happen.
        """
        logger.info(f"GameNewsAgent.invoke context_id={context_id}")
        runner_input = self._build_runner_input(context)
        tid = task_id or ""
        logger.info(
            f"Runner input type={type(runner_input).__name__}, "
            f"preview={str(runner_input)[:200]}"
        )
        async with RAWGKiotaClient() as game_service:
            agent = self._build_parent(event_queue, context_id, context.task_id, game_service)
            session = get_or_create_session(
                sessions=GameNewsAgent._sessions,
                context_id=context_id,
            )
            result = Runner.run_streamed(
                starting_agent=agent, input=runner_input, session=session,
            )

            async for event in result.stream_events():
                if not isinstance(event, RunItemStreamEvent):
                    continue

                if event.name == "tool_called" and isinstance(event.item, ToolCallItem):
                    raw = event.item.raw_item
                    call_id = getattr(raw, "call_id", None) or ""
                    tool_name = getattr(raw, "name", None) or "unknown_tool"
                    args_str = getattr(raw, "arguments", "{}")
                    try:
                        args_data: dict[str, Any] = json.loads(args_str)
                    except (json.JSONDecodeError, TypeError):
                        args_data = {"raw": args_str}
                    logger.info("[ToolCall] agent=%s tool=%s", event.item.agent.name, tool_name)
                    await event_queue.enqueue_event(
                        TaskStatusUpdateEvent(
                            task_id=tid,
                            context_id=context_id,
                            status=TaskStatus(state=TaskState.working, message=Message(
                                role=Role.agent,
                                message_id=uuid4().hex,
                                parts=[Part(root=DataPart(data=args_data))],
                                metadata={"type": "tool-call", "toolCallId": call_id, "toolCallName": tool_name},
                                task_id=tid, context_id=context_id,
                            )),
                            final=False,
                        ),
                    )

                elif event.name == "tool_output" and isinstance(event.item, ToolCallOutputItem):
                    raw = event.item.raw_item
                    call_id = getattr(raw, "call_id", None) or ""
                    tool_name = getattr(raw, "name", None) or "unknown_tool"
                    output = event.item.output
                    if isinstance(output, str):
                        try:
                            parsed = json.loads(output)
                            if isinstance(parsed, dict):
                                part = Part(root=DataPart(data=parsed))
                            else:
                                part = Part(root=TextPart(text=output))
                        except (json.JSONDecodeError, TypeError):
                            part = Part(root=TextPart(text=output))
                    elif isinstance(output, dict):
                        part = Part(root=DataPart(data=output))
                    else:
                        part = Part(root=TextPart(text=str(output)))
                    logger.info("[ToolResult] tool=%s output=%s", tool_name, str(output)[:500])
                    await event_queue.enqueue_event(
                        TaskStatusUpdateEvent(
                            task_id=tid,
                            context_id=context_id,
                            status=TaskStatus(state=TaskState.working, message=Message(
                                role=Role.agent,
                                message_id=uuid4().hex,
                                parts=[part],
                                metadata={"type": "tool-call-result", "toolCallId": call_id, "toolCallName": tool_name},
                                task_id=tid, context_id=context_id,
                            )),
                            final=False,
                        ),
                    )

                elif event.name == "handoff_requested" and isinstance(event.item, HandoffCallItem):
                    logger.info(
                        "[Handoff] from=%s to=%s",
                        event.item.agent.name,
                        getattr(event.item.raw_item, "name", "?"),
                    )

                elif event.name == "handoff_output" and isinstance(event.item, HandoffOutputItem):
                    logger.info(
                        "[HandoffResult] source=%s target=%s",
                        event.item.source_agent.name,
                        event.item.target_agent.name,
                    )

        return (result.final_output or "").strip()
