"""Agent card definition for the Weather agent."""

from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def build_agent_card(base_url: str) -> AgentCard:
    """Build the agent card for the Weather agent."""
    skills: list[AgentSkill] = [
        AgentSkill(
            id="get_weather",
            name="Get Weather",
            description="Provide current weather conditions for a specified location.",
            tags=["weather"],
            input_modes=["text"],
            output_modes=["text"],
            examples=[
                "What's the weather in Seattle?",
                "Current conditions in Tokyo",
            ],
            security=None,
        ),
        AgentSkill(
            id="get_air_quality",
            name="Get Air Quality",
            description="Report the current air quality index for a location.",
            tags=["air_quality"],
            input_modes=["text"],
            output_modes=["text"],
            examples=[
                "Air quality in Denver",
                "AQI for downtown Los Angeles",
            ],
            security=None,
        ),
        AgentSkill(
            id="get_forecast",
            name="Get Weather Forecast",
            description="Provide a multi-day weather forecast (up to 14 days) for a location.",
            tags=["weather", "forecast"],
            input_modes=["text"],
            output_modes=["text"],
            examples=[
                "Give me the 5-day forecast for London",
                "What's the weather like in Paris next week?",
            ],
            security=None,
        ),
    ]

    capabilities = AgentCapabilities(
        streaming=True,
        push_notifications=False,
        state_transition_history=False,
    )

    return AgentCard(
        name="Weather Provider",
        description="Provides weather forecasts and air quality details for any location.",
        version="0.1.0",
        preferred_transport="JSONRPC",
        default_input_modes=["text"],
        default_output_modes=["text"],
        url=base_url,
        capabilities=capabilities,
        skills=skills,
        supports_authenticated_extended_card=False,
    )
