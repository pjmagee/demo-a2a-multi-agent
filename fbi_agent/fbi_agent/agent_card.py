"""Agent card definition for the FBI agent."""

from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def build_agent_card(base_url: str) -> AgentCard:
    """Build the agent card for the FBI agent."""
    skills: list[AgentSkill] = [
        AgentSkill(
            id="investigate_federal_crime",
            name="Investigate Federal Crime",
            description="Coordinate the investigation of a federal crime or interstate case.",
            tags=["crime", "federal"],
            input_modes=["text"],
            output_modes=["text"],
            examples=[
                "Investigate cyber attack impacting multiple states",
                "Follow up on interstate fraud ring",
            ],
            security=None,
        ),
        AgentSkill(
            id="analyze_threat",
            name="Analyze Threat",
            description="Assess national security threats and provide advisories.",
            tags=["threat", "analysis"],
            input_modes=["text"],
            output_modes=["text"],
            examples=[
                "Evaluate potential terrorism threat",
                "Review suspicious package report for federal risk",
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
        name="FBIAgent",
        description="Handles federal crimes, threat assessments, and coordinates with local law enforcement.",
        version="0.1.0",
        preferred_transport="JSONRPC",
        default_input_modes=["text"],
        default_output_modes=["text"],
        url=base_url,
        capabilities=capabilities,
        skills=skills,
        supports_authenticated_extended_card=False,
    )
