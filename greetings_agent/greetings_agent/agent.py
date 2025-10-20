"""Core agent behaviour for the Greetings agent."""


import logging
from secrets import choice
from typing import ClassVar

from a2a.server.agent_execution.context import RequestContext
from agents import Agent, Runner, RunResult, SQLiteSession, Tool, function_tool
from agents.memory.session import Session

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

    async def invoke(self, context: RequestContext) -> str:
        """Execute the agent for the provided request context."""
        user_input: str = context.get_user_input()
        session: Session | None = self._get_or_create_session(context=context)

        result: RunResult = await Runner.run(
            starting_agent=self.agent,
            input=user_input,
            # https://openai.github.io/openai-agents-python/sessions/
            session=session,
        )

        response_text: str = result.final_output_as(
            cls=str,
            raise_if_incorrect_type=True,
        )
        return response_text

    # https://openai.github.io/openai-agents-python/sessions/
    def _get_or_create_session(self, context: RequestContext) -> Session | None:
        session: Session | None = None
        if isinstance(context.context_id, str):
            if context.context_id not in GreetingsAgent.sessions:
                GreetingsAgent.sessions[context.context_id] = SQLiteSession(
                    session_id=context.context_id,
                )
            session = GreetingsAgent.sessions[context.context_id]
        return session
