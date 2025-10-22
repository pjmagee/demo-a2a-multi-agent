"""A2A Agent for testing other A2A agents."""

import logging
from typing import ClassVar

from a2a.server.agent_execution.context import RequestContext
from agents import Agent, Runner, RunResult, Tool
from agents.memory.session import Session
from shared.openai_session_helpers import get_or_create_session
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
        self.agent: Agent[None] = Agent(
            name="Tester Agent",
            instructions=(
                "You are an A2A testing agent. Verify that every peer agent"
                " responds correctly by exercising their capabilities."
            ),
            handoffs=[],
            tool_use_behavior="run_llm_again",
            tools=self._build_tools(),
        )
        self.history: list[str] = []

    def _build_tools(self) -> list[Tool]:
        """Build the Tester agent's toolset."""
        peer_tools: list[Tool] = default_peer_tools()
        create_new_session_tool = session_management_tool()
        return [create_new_session_tool, *peer_tools]

    async def invoke(self, context: RequestContext, context_id: str) -> str:
        """Invoke the Tester agent with the given context and returns the response.

        Args:
            context: Request context containing user input
            context_id: Guaranteed non-null context ID (created by executor)

        Returns:
            Agent response text

        """
        user_input: str = context.get_user_input()
        session: Session = get_or_create_session(
            sessions=TesterAgent.sessions,
            context_id=context_id,
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
