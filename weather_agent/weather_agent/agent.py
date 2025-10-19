"""Core agent behavior for the Weather agent."""


import logging
from random import SystemRandom
from typing import ClassVar

from a2a.server.agent_execution.context import RequestContext
from agents import Agent, Runner, RunResult, SQLiteSession, Tool, function_tool
from agents.memory.session import Session
from shared.peer_tools import default_peer_tools, peer_message_context

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
        self.agent = Agent(
            name="Weather Agent",
            instructions=(
                "Provide clear, actionable weather and air quality updates"
                " for any requested location."
            ),
            handoffs=[],
            tool_use_behavior="run_llm_again",
            tools=self._build_tools(),
        )

    def _build_tools(self) -> list[Tool]:
        list_agents_tool, send_message_tool = default_peer_tools()

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
            list_agents_tool,
            send_message_tool,
        ]

    async def invoke(self, context: RequestContext) -> str:
        """Invoke the WeatherAgent with the provided context."""
        user_input: str = context.get_user_input()
        session: Session | None = self._get_or_create_session(context=context)
        context_id: str | None = (
            context.context_id if isinstance(context.context_id, str) else None
        )

        with peer_message_context(context_id=context_id):
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

    def _get_or_create_session(self, context: RequestContext) -> Session | None:
        session: Session | None = None
        if isinstance(context.context_id, str):
            if context.context_id not in WeatherAgent.sessions:
                WeatherAgent.sessions[context.context_id] = SQLiteSession(
                    session_id=context.context_id,
                )
            session = WeatherAgent.sessions[context.context_id]
        return session
