"""AgentCard definition for Game News Agent."""

from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def build_agent_card(base_url: str) -> AgentCard:
    """Build the AgentCard for Game News Agent.

    Args:
        base_url: Base URL where the agent is hosted

    Returns:
        AgentCard with skill definitions
    """
    skills: list[AgentSkill] = [
        AgentSkill(
            id="generate_gaming_report",
            name="Generate Gaming Report",
            description=(
                "Creates a comprehensive gaming report with recent releases, upcoming titles, "
                "highly anticipated games, and poorly received titles. Filters by genre, date range "
                "(max 31 days), and game modes. Returns a fact-checked markdown report as an artifact.\n\n"
                "Accepts either:\n"
                "  • Structured JSON matching the request schema (deterministic, no routing ambiguity)\n"
                "  • Plain-text natural language (e.g. 'Generate an action RPG report for the last two weeks')\n\n"
                f"Request Schema:  {base_url}/contracts/v1/game_report_request.schema.json\n"
                f"Response Schema: {base_url}/contracts/v1/game_report_response.schema.json\n\n"
                "The report is delivered as a TaskArtifactUpdateEvent with a text/markdown part."
            ),
            tags=["gaming", "report", "news", "langgraph"],
            input_modes=["application/json", "text/plain"],
            output_modes=["text/markdown"],
            examples=[
                '{"game_genres":["action","rpg"],"date_from":"2026-01-15","date_to":"2026-02-15","game_modes":["single_player"]}',
                "Generate report for RPG and action games released between "
                "2026-01-15 and 2026-02-15, single-player focus",
                "Show me upcoming indie games for the next 2 weeks, both online and offline modes",
                "Create a gaming news report for strategy and simulation genres from last week",
            ],
            security=None,
        ),
        AgentSkill(
            id="analyze_game_reviews",
            name="Analyze Game Reviews",
            description=(
                "Analyses user reviews for a specific game, providing sentiment insights split into "
                "positive and negative feedback. Returns common themes, representative quotes, and "
                "AI-generated summaries as a markdown artifact.\n\n"
                "Accepts either:\n"
                "  • Structured JSON with game_id (RAWG ID) and optional review_count 1–50 (default 20)\n"
                "  • Plain-text natural language — the agent will search for the game first, then analyse\n\n"
                f"Request Schema:  {base_url}/contracts/v1/review_analysis_request.schema.json\n"
                f"Response Schema: {base_url}/contracts/v1/review_analysis_response.schema.json\n\n"
                "The analysis is delivered as a TaskArtifactUpdateEvent with a text/markdown part."
            ),
            tags=["gaming", "reviews", "sentiment", "langgraph"],
            input_modes=["application/json", "text/plain"],
            output_modes=["text/markdown"],
            examples=[
                '{"game_id":3498,"review_count":20}',
                "Analyze reviews for game ID 3498 with top 20 reviews",
                "What do players think about Elden Ring?",
                "Summarise positive and negative reviews for GTA 5",
                "Give me a review analysis for Cyberpunk 2077",
            ],
            security=None,
        ),
    ]

    return AgentCard(
        name="GameNewsAgent",
        description=(
            "Gaming analysis agent with two skills: (1) Generate comprehensive gaming reports "
            "(recent releases, upcoming titles, industry trends) via a LangGraph multi-step workflow "
            "with fact-checking; (2) Analyse game reviews with positive/negative sentiment analysis "
            "via a LangGraph sentiment pipeline. Both skills accept structured JSON or plain-text "
            "natural language. Uses RAWG.io for live game data. Includes input validation, "
            "content-moderation guard rails, and automated fact-checking."
        ),
        version="0.1.0",
        preferred_transport="JSONRPC",
        default_input_modes=["application/json", "text/plain"],
        default_output_modes=["text/markdown"],
        url=base_url,
        capabilities=AgentCapabilities(
            streaming=True,
            push_notifications=False,
            state_transition_history=False,
        ),
        skills=skills,
        supports_authenticated_extended_card=False,
    )

