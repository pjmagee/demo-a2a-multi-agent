"""Agent card definition for the Tester agent."""



from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def build_agent_card(base_url: str) -> AgentCard:
    """Build the agent card for the Tester agent."""
    capabilities = AgentCapabilities(
        push_notifications=False,
        state_transition_history=True,
        streaming=False,
    )
    skills: list[AgentSkill] = [
        AgentSkill(
            id="run_peer_audit",
            name="Run Peer Audit",
            description="Iterates over each registered peer agent, invoking its skills via A2A to validate readiness.",
            examples=["Run peer audit", "Check all responders"],
            input_modes=["text"],
            output_modes=["text"],
            security=None,
            tags=["testing", "integration", "audit"],
        ),
        AgentSkill(
            id="summarize_last_audit",
            name="Summarize Last Audit",
            description="Summarizes the most recent peer audit run and highlights success or failure details.",
            examples=["Summarize last audit"],
            input_modes=["text"],
            output_modes=["text"],
            security=None,
            tags=["reporting", "audit"],
        ),
    ]
    return AgentCard(
        name="Tester Agent",
        description="Exercises every responder agent to ensure cross-agency readiness.",
        version="0.1.0",
        preferred_transport="JSONRPC",
        capabilities=capabilities,
        default_input_modes=["text"],
        default_output_modes=["text"],
        skills=skills,
        url=base_url,
        supports_authenticated_extended_card=False,
    )
