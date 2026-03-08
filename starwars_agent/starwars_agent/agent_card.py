"""Agent card builder for the Star Wars agent."""

from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def build_agent_card(base_url: str) -> AgentCard:
    """Return the agent card describing the Star Wars agent's capabilities."""
    return AgentCard(
        name="Star Wars Agent",
        description=(
            "A Star Wars knowledge expert powered by Wookieepedia articles. "
            "Ask questions about Star Wars movies, characters, planets, and lore. "
            "Answers include source references from Wookieepedia."
        ),
        version="0.1.0",
        url=base_url,
        capabilities=AgentCapabilities(
            push_notifications=False,
            state_transition_history=False,
            streaming=True,
        ),
        preferred_transport="JSONRPC",
        default_input_modes=["text"],
        default_output_modes=["text"],
        supports_authenticated_extended_card=False,
        skills=[
            AgentSkill(
                id="starwars-knowledge",
                name="Star Wars Knowledge",
                description=(
                    "Search and answer questions about the Star Wars universe "
                    "using curated Wookieepedia articles with source citations."
                ),
                examples=[
                    "What is the plot of A New Hope?",
                    "Tell me about the Battle of Yavin",
                    "Who directed The Empire Strikes Back?",
                    "What are the Saga films?",
                    "Summarize Return of the Jedi",
                ],
                input_modes=["text"],
                output_modes=["text"],
                tags=["starwars", "knowledge", "fandom", "wookieepedia"],
            ),
        ],
    )
