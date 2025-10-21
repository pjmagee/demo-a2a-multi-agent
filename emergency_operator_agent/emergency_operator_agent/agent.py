"""Emergency Operator Agent for the OpenAI Agents SDK."""


import logging
from typing import ClassVar

from a2a.server.agent_execution.context import RequestContext
from agents import Agent, Runner, RunResult, SQLiteSession, Tool
from agents.memory.session import Session
from shared.peer_tools import default_peer_tools, peer_message_context

logger: logging.Logger = logging.getLogger(name=__name__)


class Operator911Agent:
    """Coordinates emergency routing using the OpenAI Agents SDK."""

    sessions: ClassVar[dict[str, Session]] = {}

    def __init__(self) -> None:
        """Initialize the Emergency Operator Agent."""
        self.agent = Agent(
            name="Emergency Operator Agent",
            instructions=(
                "You are a 112 emergency operator. Handle ONLY genuine emergencies.\n\n"
                "For non-emergencies: 'This line is reserved for emergencies only.'\n\n"
                "For emergencies:\n"
                "1. Use list_agents to get exact agent names\n"
                "2. Use send_message with EXACT agent name to dispatch services\n"
                "3. Include location, emergency type, and urgency in messages\n\n"
                "Always list agents if unsure of names. Agent names must be exact."
            ),
            handoffs=[],
            tool_use_behavior="run_llm_again",
            tools=self._build_tools(),
        )

    def _build_tools(self) -> list[Tool]:
        return default_peer_tools()

    async def invoke(self, context: RequestContext) -> str:
        """Process the caller interaction and return the model response."""
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
        """Get or create a session for the given context."""
        session: Session | None = None
        if isinstance(context.context_id, str):
            if context.context_id not in Operator911Agent.sessions:
                Operator911Agent.sessions[context.context_id] = SQLiteSession(
                    session_id=context.context_id,
                )
            session = Operator911Agent.sessions[context.context_id]
        return session
