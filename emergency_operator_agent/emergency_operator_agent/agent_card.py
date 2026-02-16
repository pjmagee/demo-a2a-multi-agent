"""Agent card definition for the Emergency Operator Agent."""

from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def build_agent_card(base_url: str) -> AgentCard:
    """Build the agent card for the Emergency Operator Agent."""
    return AgentCard(
        name="Emergency Operator",
        description="Routes emergency calls to fire, police, ambulance, or other Agents.",
        version="0.1.0",
        preferred_transport="JSONRPC",
        default_input_modes=["text"],
        default_output_modes=["text"],
        url=base_url,
        capabilities=AgentCapabilities(
            streaming=True,
            push_notifications=False,
            state_transition_history=True,
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
        ],
        supports_authenticated_extended_card=False,
    )
