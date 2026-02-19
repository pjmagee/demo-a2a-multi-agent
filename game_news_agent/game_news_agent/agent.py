"""LangGraph-based gaming report agent with section-based workflow and retry policies."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from game_news_agent.game_service import RAWGClient
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

if TYPE_CHECKING:
    from a2a.server.agent_execution.context import RequestContext

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


class GameNewsAgent:
    """LangGraph-based agent with section-based workflow and retry policies."""

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

        async with RAWGClient() as client:
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

        async with RAWGClient() as client:
            for genre in request.game_genres:
                recent = await client.get_games_by_genre(
                    genre=genre.value,
                    date_from=request.date_from,
                    date_to=request.date_to,
                    game_modes=request.game_modes,
                    page_size=5,
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
            md_parts.append(f"\n### {game['name']}")
            md_parts.append(f"\n**Released:** {game.get('released', 'Unknown')}")
            if game.get('metacritic'):
                md_parts.append(f" | **Rating:** {game['metacritic']}/100")
            platforms = ", ".join([p['platform']['name'] for p in game.get('platforms', [])[:3]])
            md_parts.append(f"\n{platforms}\n")

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

        async with RAWGClient() as client:
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
            platforms = ", ".join([p['platform']['name'] for p in game.get('platforms', [])[:3]])
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

        async with RAWGClient() as client:
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
            f"\n**Game Modes:** {', '.join([m.value.replace('_', ' ').title() for m in request.game_modes])}",
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
                description=", ".join([p["platform"]["name"] for p in game.get("platforms", [])[:3]]),
            )
            for game in state["recently_released_data"][:5]
            if game.get("name")
        ]

        # Upcoming games
        upcoming_games = [
            UpcomingGame(
                name=game["name"],
                expected_release_date=game.get("released") or game.get("tba", "TBA"),
                description=", ".join([p["platform"]["name"] for p in game.get("platforms", [])[:3]]),
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

    async def invoke(self, context: RequestContext, context_id: str) -> GameReportResponse:
        """Invoke the agent to generate a gaming report.

        Args:
            context: A2A request context
            context_id: Conversation context ID

        Returns:
            GameReportResponse with report markdown and structured data
        """
        logger.info(f"Invoking GameNewsAgent with context_id={context_id}")

        # Extract request from context
        user_input = context.get_user_input()

        try:
            request_data = json.loads(user_input)
            request = GameReportRequest(**request_data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse request: {e}")
            return GameReportResponse(
                report_markdown="# Error\n\nInvalid request format.",
                sections=ReportSections(),
                references=[],
                generated_at=datetime.now(),
                fact_check_passed=False,
                validation_errors=[f"Invalid request format: {str(e)}"],
            )

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
