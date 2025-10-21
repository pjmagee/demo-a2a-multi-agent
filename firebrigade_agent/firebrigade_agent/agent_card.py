"""Agent card definition for the Fire Brigade Agent."""

from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def build_agent_card(base_url: str) -> AgentCard:
    """Build the agent card for the Fire Brigade Agent."""
    skills: list[AgentSkill] = [
        AgentSkill(
            id="extinguish_fire",
            name="Extinguish Fire",
            description="Travel to a location and extinguish the reported fire.",
            tags=["fire", "emergency"],
            input_modes=["text"],
            output_modes=["text"],
            examples=[
                "dispatch team to 123 Main St",
                "send firefighters to the industrial park",
            ],
            security=None,
        ),
        AgentSkill(
            id="assess_fire_risk",
            name="Assess Fire Risk",
            description="Assess the fire risk level at the specified location.",
            tags=["fire", "assessment"],
            input_modes=["text"],
            output_modes=["text"],
            examples=[
                "evaluate risk at the docks",
                "how risky is the warehouse",
            ],
            security=None,
        ),
    ]

    capabilities = AgentCapabilities(
        streaming=False,
        push_notifications=False,
        state_transition_history=False,
    )

    return AgentCard(
        name="FireFighterAgent",
        description="Responds to fire emergencies, dispatches crews, and assesses risk levels.",
        version="0.1.0",
        preferred_transport="JSONRPC",
        default_input_modes=["text"],
        default_output_modes=["text"],
        url=base_url,
        capabilities=capabilities,
        skills=skills,
        supports_authenticated_extended_card=False,
    )

