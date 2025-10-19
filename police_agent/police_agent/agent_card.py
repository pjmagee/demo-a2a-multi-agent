"""Agent card definition for the Police agent."""

from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def build_agent_card(base_url: str) -> AgentCard:
    """build_agent_card."""
    return AgentCard(
        name="PoliceAgent",
        description="Handles local policing tasks, crime investigations, and traffic incidents.",
        version="0.1.0",
        preferred_transport="JSONRPC",
        default_input_modes=["text"],
        default_output_modes=["text"],
        url=base_url,
        capabilities=AgentCapabilities(
            streaming=False,
            push_notifications=False,
            state_transition_history=False,
        ),
        skills=[
            AgentSkill(
                id="investigate_crime",
                name="Investigate Local Crime",
                description="Deploy officers to investigate a local crime scene and gather statements.",
                tags=["crime", "local"],
                input_modes=["text"],
                output_modes=["text"],
                examples=[
                    "Investigate burglary at 42 Elm St",
                    "Respond to robbery near the market",
                ],
                security=None,
            ),
            AgentSkill(
                id="manage_traffic",
                name="Manage Traffic Incident",
                description="Coordinate officers and resources for a traffic collision or congestion.",
                tags=["traffic", "local"],
                input_modes=["text"],
                output_modes=["text"],
                examples=[
                    "Clear minor accident on 5th Ave",
                    "Handle road blockage downtown",
                ],
                security=None,
            ),
        ],
        supports_authenticated_extended_card=False,
    )
