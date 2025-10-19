"""911 Operator Agent for the OpenAI Agents SDK."""


import logging
from typing import ClassVar

from a2a.server.agent_execution.context import RequestContext
from agents import Agent, Runner, RunResult, SQLiteSession, Tool
from agents.memory.session import Session
from shared.peer_tools import default_peer_tools

logger: logging.Logger = logging.getLogger(name=__name__)


class Operator911Agent:
    """Coordinates emergency routing using the OpenAI Agents SDK."""

    sessions: ClassVar[dict[str, Session]] = {}

    def __init__(self) -> None:
        """Initialize the 911 Operator Agent."""
        self.agent = Agent(
            name="911 Operator Agent",
            instructions=(
                "You are a 911 dispatcher. Always confirm the caller is"
                " reporting an active emergency before taking action."
                " If the caller is not reporting an emergency, terminate"
                " the interaction politely without escalating or handing"
                " off to any responders. For genuine emergencies, decide"
                " which specialized responder to call, using the routing"
                " tool. Only reach for the weather guidance tool when"
                " callers explicitly request weather information."
            ),
            handoffs=[],
            tool_use_behavior="run_llm_again",
            tools=self._build_tools(),
        )

    def _build_tools(self) -> list[Tool]:
        list_agents_tool, send_message_tool = default_peer_tools()
        return [list_agents_tool, send_message_tool]

    async def invoke(self, context: RequestContext) -> str:
        """Process the caller interaction and return the model response."""
        user_input: str = context.get_user_input()
        session: Session | None = self._get_or_create_session(context=context)

        result: RunResult = await Runner.run(
            starting_agent=self.agent,
            input=user_input,
            session=session,
        )
        response_text: str = result.final_output_as(
            cls=str,
            raise_if_incorrect_type=True,
        )
        logger.info("Final response: %s", response_text)
        return response_text

    def _get_or_create_session(self, context: RequestContext) -> Session | None:
        """Get or create a session for the given context."""
        session: Session | None = None
        if isinstance(context.context_id, str):
            if context.context_id not in Operator911Agent.sessions:
                Operator911Agent.sessions[context.context_id] = SQLiteSession(
                    session_id=context.context_id,
                )
            session = Operator911Agent.sessions[context.context_id]
        return session
