"""Agent card definition for the Ambulance agent."""

from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def build_agent_card(base_url: str) -> AgentCard:
    """Build the agent card for the Ambulance agent."""
    return AgentCard(
        name="AmbulanceAgent",
        description="Responds to medical emergencies, triage, and patient transport needs.",
        version="0.1.0",
        preferred_transport="JSONRPC",
        default_input_modes=["text"],
        default_output_modes=["text"],
        url=base_url,
        capabilities= AgentCapabilities(
            streaming=False,
            push_notifications=False,
            state_transition_history=False,
        ),
        skills=[
            AgentSkill(
                id="provide_medical_aid",
                name="Provide Medical Aid",
                description="Dispatch paramedics to deliver on-site medical care.",
                tags=["medical", "emergency"],
                input_modes=["text"],
                output_modes=["text"],
                examples=[
                    "Send ambulance to 22 Pine St",
                    "Provide CPR assistance at the stadium",
                ],
                security=None,
            ),
            AgentSkill(
                id="transport_patient",
                name="Transport Patient",
                description="Safely transport a stabilized patient to an appropriate hospital.",
                tags=["medical", "transport"],
                input_modes=["text"],
                output_modes=["text"],
                examples=[
                    "Transport injured cyclist to county hospital",
                    "Move patient to trauma center",
                ],
                security=None,
            ),
        ],
        supports_authenticated_extended_card=False,
    )
