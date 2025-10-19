"""A2A Agent for testing other A2A agents."""

import logging
from typing import ClassVar

from a2a.server.agent_execution.context import RequestContext
from agents import Agent, Runner, RunResult, SQLiteSession
from agents.memory.session import Session
from shared.peer_tools import (
    default_peer_tools,
    peer_message_context,
    session_management_tool,
)

logger: logging.Logger = logging.getLogger(name=__name__)


class TesterAgent:
    """Audits peer A2A agents by invoking their skills through the A2A client."""

    sessions: ClassVar[dict[str, Session]] = {}

    def __init__(self) -> None:
        """Initialize the Tester agent with the default peer tools."""
        list_agents_tool, send_message_tool = default_peer_tools()
        create_new_session_tool = session_management_tool()
        self.agent = Agent(
            name="Tester Agent",
            instructions=(
                "You are an A2A testing agent. Verify that every peer agent"
                " responds correctly by exercising their capabilities."
            ),
            handoffs=[],
            tool_use_behavior="run_llm_again",
            tools=[create_new_session_tool, list_agents_tool, send_message_tool],
        )
        self.history: list[str] = []

    async def invoke(self, context: RequestContext) -> str:
        """Invoke the Tester agent with the given context and returns the response."""
        user_input: str = context.get_user_input()
        session: Session | None = self._get_or_create_session(context=context)
        context_id: str | None = (
            context.context_id if isinstance(context.context_id, str) else None
        )
        with peer_message_context(context_id):
            response: RunResult = await Runner.run(
                starting_agent=self.agent,
                input=user_input,
                session=session,
            )
        response_text: str = response.final_output_as(
            cls=str,
            raise_if_incorrect_type=True,
        )
        return response_text

    def _get_or_create_session(self, context: RequestContext) -> Session | None:
        """Get or create a session for the given context."""
        session: Session | None = None
        if isinstance(context.context_id, str):
            if context.context_id not in TesterAgent.sessions:
                TesterAgent.sessions[context.context_id] = SQLiteSession(
                    session_id=context.context_id,
                )
            session = TesterAgent.sessions[context.context_id]
        return session
