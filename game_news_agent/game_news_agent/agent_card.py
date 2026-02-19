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
                "(max 31 days), and game modes. Returns a fact-checked markdown report.\n\n"
                f"Request Schema: {base_url}/contracts/v1/request.schema.json"
            ),
            tags=["gaming", "report", "news", "analysis"],
            input_modes=["application/json"],  # Expects JSON DataPart
            output_modes=["text/markdown"],  # Returns markdown Artifact
            examples=[
                "Generate report for RPG and action games released between 2026-01-15 and 2026-02-15, single-player focus",
                "Show me upcoming indie games for the next 2 weeks, both online and offline modes",
                "Create a gaming news report for strategy and simulation genres from last week",
            ],
            security=None,
        ),
    ]

    return AgentCard(
        name="GameNewsAgent",
        description=(
            "LangGraph-based gaming report generator that creates comprehensive gaming reports "
            "with recent releases, upcoming titles, industry trends, and game ratings. "
            "Uses RAWG.io database for real game data. Includes input/output validation, "
            "content moderation guard rails, and automated fact-checking."
        ),
        version="0.1.0",
        preferred_transport="JSONRPC",
        default_input_modes=["application/json"],
        default_output_modes=["text/markdown"],
        url=base_url,
        capabilities=AgentCapabilities(
            streaming=False,
            push_notifications=False,
            state_transition_history=False,
        ),
        skills=skills,
        supports_authenticated_extended_card=False,
    )
