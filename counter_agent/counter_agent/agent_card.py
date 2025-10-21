"""Agent card definition for the Counter agent."""

from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def build_agent_card(base_url: str) -> AgentCard:
    """Build the agent card for the Counter agent."""
    return AgentCard(
        name="CounterAgent",
        description=(
            "Streams count numbers using SSE (Server-Sent Events). "
            "Demonstrates async streaming with Microsoft agent-framework."
        ),
        version="0.1.0",
        preferred_transport="JSONRPC",
        default_input_modes=["text"],
        default_output_modes=["text"],
        url=base_url,
        capabilities=AgentCapabilities(
            streaming=True,
            push_notifications=False,
            state_transition_history=False,
        ),
        skills=[
            AgentSkill(
                id="stream_count",
                name="Stream Count",
                description=(
                    "Stream count numbers from 1 to the specified target. "
                    "Each number is sent as a separate SSE message."
                ),
                tags=["streaming", "demo", "counter"],
                input_modes=["text"],
                output_modes=["text"],
                examples=[
                    "count to 10",
                    "count to 100",
                    "count to 5",
                ],
                security=None,
            ),
        ],
        supports_authenticated_extended_card=False,
    )
