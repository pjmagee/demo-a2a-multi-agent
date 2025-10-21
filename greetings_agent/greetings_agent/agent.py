"""Core agent behaviour for the Greetings agent."""


import logging
from secrets import choice
from typing import ClassVar

from a2a.server.agent_execution.context import RequestContext
from agents import Agent, Runner, RunResult, Tool, function_tool
from agents.memory.session import Session
from shared.openai_session_helpers import get_or_create_session

logger: logging.Logger = logging.getLogger(name=__name__)


class GreetingsAgent:
    """Encapsulates Greetings-specific reasoning via the OpenAI Agent SDK."""

    sessions: ClassVar[dict[str, Session]] = {}
    options: ClassVar[list[str]] = ["sunny", "cloudy", "rainy", "snowy"]

    def __init__(self) -> None:
        """Initialise the Greetings agent."""
        self.agent = Agent(
            name="Greetings Agent",
            instructions=(
                "You greet the caller in their language. Offer a friendly tone"
                " and include a weather update if they request one."
            ),
            handoffs=[],
            tool_use_behavior="run_llm_again",
            tools=self._build_tools(),
        )

    # https://openai.github.io/openai-agents-python/tools/
    def _build_tools(self) -> list[Tool]:
        """Return all tools exposed by the Greetings agent."""

        @function_tool
        async def get_weather(location: str) -> str:
            logger.info(
                "Tool get_weather invoked with location=%s",
                location,
            )
            selection: str = choice(self.options)
            return f"The weather in {location} is {selection}."

        return [get_weather]

    async def invoke(self, context: RequestContext, context_id: str) -> str:
        """Execute the agent for the provided request context.

        Args:
            context: Request context containing user input
            context_id: Guaranteed non-null context ID (created by executor)

        Returns:
            Agent response text

        """
        user_input: str = context.get_user_input()
        session: Session = get_or_create_session(
            sessions=GreetingsAgent.sessions,
            context_id=context_id,
        )

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
