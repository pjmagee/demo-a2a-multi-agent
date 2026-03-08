"""Agent card builder for the Summarise agent."""

from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def build_agent_card(base_url: str) -> AgentCard:
    """Return the agent card describing the Summarise agent's capabilities."""
    agent_capabilities = AgentCapabilities(
        push_notifications=False,
        state_transition_history=False,
        streaming=True,
    )
    agent_skills: list[AgentSkill] = [
        AgentSkill(
            id="summarise-conversation",
            description=(
                "Generates a short, descriptive title (5-8 words) for a "
                "conversation based on the message history provided."
            ),
            examples=[
                "Summarise this conversation",
                "Give me a title for this chat",
                "What is this conversation about?",
            ],
            name="Conversation Title",
            input_modes=["text"],
            output_modes=["text"],
            security=None,
            tags=["summarise", "title", "conversation"],
        ),
    ]
    return AgentCard(
        name="Summarise Agent",
        capabilities=agent_capabilities,
        description=(
            "Generates concise, descriptive titles for conversations "
            "based on the message history."
        ),
        version="0.1.0",
        preferred_transport="JSONRPC",
        default_input_modes=["text"],
        default_output_modes=["text"],
        skills=agent_skills,
        url=base_url,
        supports_authenticated_extended_card=False,
    )
