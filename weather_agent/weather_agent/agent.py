"""Core agent behavior for the Weather agent."""


import logging
from typing import ClassVar

from a2a.server.agent_execution.context import RequestContext
from agents import (
    Agent,
    InputGuardrailTripwireTriggered,
    ModelSettings,
    Runner,
    RunResult,
    Tool,
)
from agents.memory.session import Session
from shared.openai_session_helpers import get_or_create_session
from shared.peer_tools import peer_message_context

from weather_agent.guard_rails import weather_only_guardrail
from weather_agent.tools import get_air_quality_report, get_weather_report

logger: logging.Logger = logging.getLogger(name=__name__)

class WeatherAgent:
    """Produces weather and air quality responses."""

    sessions: ClassVar[dict[str, Session]] = {}

    def __init__(self) -> None:
        """Initialize the WeatherAgent."""
        self.agent: Agent[None] = Agent(
            name="Weather Agent",
            instructions="""
            Provide clear, actionable weather and air quality updates by using the provided tools.
            """,
            handoffs=[],
            input_guardrails=[weather_only_guardrail],
            tool_use_behavior="run_llm_again",
            tools=self._build_tools(),
            model_settings=ModelSettings(tool_choice="required"),
        )

    def _build_tools(self) -> list[Tool]:

        # peer_tools: list[Tool] = default_peer_tools()  # noqa: ERA001

        return [
            get_weather_report,
            get_air_quality_report,
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
                return await self._create_tripwire_response(user_input=user_input, ex=ex)

    async def _create_tripwire_response(
            self,
            user_input: str,
            ex: InputGuardrailTripwireTriggered) -> str:

        result: RunResult = await Runner.run(
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
            input="Generate a user friendly response based on the instructions.",
        )
        return result.final_output_as(
            cls=str,
            raise_if_incorrect_type=True,
        )
