"""Agent card definition for the 911 Operator agent."""

from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def build_agent_card(base_url: str) -> AgentCard:
    """Build the agent card for the 911 Operator agent."""
    return AgentCard(
        name="Operator911Agent",
        description="Routes emergency calls to fire, police, ambulance, or FBI agents and handles weather guidance.",
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
                id="route_emergency",
                name="Route Emergency",
                description="Triage an emergency report and contact the appropriate responder agent.",
                tags=["orchestration"],
                input_modes=["text"],
                output_modes=["text"],
                examples=[
                    "Route a fire reported at 55 State St",
                    "Send police for a robbery in progress",
                ],
                security=None,
            ),
            AgentSkill(
                id="provide_weather_instructions",
                name="Provide Weather Instructions",
                description="Guide callers on how to obtain weather information when not an emergency.",
                tags=["information"],
                input_modes=["text"],
                output_modes=["text"],
                examples=[
                    "Caller wants weather with no emergency",
                    "Non-emergency weather question",
                ],
                security=None,
            ),
        ],
        supports_authenticated_extended_card=False,
    )
