"""Core agent behavior for the Weather agent."""


import logging
from random import SystemRandom
from typing import ClassVar

from a2a.server.agent_execution.context import RequestContext
from agents import (
    Agent,
    InputGuardrailTripwireTriggered,
    Runner,
    RunResult,
    Tool,
    function_tool,
)
from agents.memory.session import Session
from shared.openai_session_helpers import get_or_create_session
from shared.peer_tools import default_peer_tools, peer_message_context

from weather_agent.guard_rails import weather_only_guardrail

logger: logging.Logger = logging.getLogger(name=__name__)
_rng = SystemRandom()


class WeatherAgent:
    """Produces weather and air quality responses."""

    weather_conditions: ClassVar[tuple[str, ...]] = (
        "sunny",
        "cloudy",
        "rainy",
        "stormy",
        "snowy",
    )

    air_quality_descriptions: ClassVar[tuple[str, ...]] = (
        "Good",
        "Moderate",
        "Unhealthy for Sensitive Groups",
        "Unhealthy",
    )

    sessions: ClassVar[dict[str, Session]] = {}

    def __init__(self) -> None:
        """Initialize the WeatherAgent."""
        self.agent: Agent[None] = Agent(
            name="Weather Agent",
            instructions="""
            Provide clear, actionable weather and air quality updates
            for any requested location.
            """,
            handoffs=[],
            input_guardrails=[weather_only_guardrail],
            tool_use_behavior="run_llm_again",
            tools=self._build_tools(),
        )

    def _build_tools(self) -> list[Tool]:
        peer_tools: list[Tool] = default_peer_tools()

        @function_tool
        async def get_weather_report(location: str) -> str:
            """Report weather for the given location."""
            logger.info(
                "Tool get_weather_report invoked with location=%s",
                location,
            )
            temperature: int = _rng.randint(-10, 40)
            condition: str = _rng.choice(self.weather_conditions)
            return f"Weather in {location}: {condition} with {temperature}°C."

        @function_tool
        async def get_air_quality_report(location: str) -> str:
            """Report air quality for the given location."""
            logger.info(
                "Tool get_air_quality_report invoked with location=%s",
                location,
            )
            aqi: int = _rng.randint(10, 150)
            descriptor: str = _rng.choice(self.air_quality_descriptions)
            return f"Air quality in {location}: AQI {aqi} ({descriptor})."

        return [
            get_weather_report,
            get_air_quality_report,
            *peer_tools,
        ]

    async def invoke(self, context: RequestContext, context_id: str) -> str:
        """Invoke the WeatherAgent with the provided context.

        Args:
            context: Request context containing user input
            context_id: Guaranteed non-null context ID (created by executor)

        Returns:
            Agent response text

        """
        user_input: str = context.get_user_input()
        session: Session = get_or_create_session(
            sessions=WeatherAgent.sessions,
            context_id=context_id,
        )

        with peer_message_context(context_id=context_id):
            try:
                result: RunResult = await Runner.run(
                    starting_agent=self.agent,
                    input=user_input,
                    session=session,
                )
                response_text: str = result.final_output_as(
                    cls=str,
                    raise_if_incorrect_type=True,
                )
                return response_text

            except InputGuardrailTripwireTriggered as ex:
                logger.warning("Guardrail tripwire triggered")
                result = await Runner.run(
                        starting_agent=Agent(
                            name="Guard",
                            instructions=f"""
                                The guard rails agent tripwire triggered.
                                Notify the user you cannot continue with their original request:

                                User Input:
                                ----------
                                {user_input}

                                Guard rails exception:
                                ---------------------
                                {ex!s}


                                """,
                        ),
                        input="Generate a user friendly response based on the instructions",
                    )
                return result.final_output_as(
                    cls=str,
                    raise_if_incorrect_type=True)