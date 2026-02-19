"""A2A Agent for testing other A2A agents."""

import logging
from typing import ClassVar

import dotenv
from a2a.server.agent_execution.context import RequestContext
from agents import Agent, Runner, RunResult, Tool
from agents.memory.session import Session
from shared.openai_session_helpers import get_or_create_session
from shared.peer_tools import (
    default_peer_tools,
    discovery_tools,
    peer_message_context,
    session_management_tool,
)

dotenv.load_dotenv()  # Load environment variables from .env file

logger: logging.Logger = logging.getLogger(name=__name__)

class TesterAgent:
    """Audits peer A2A agents by invoking their skills through the A2A client."""

    sessions: ClassVar[dict[str, Session]] = {}

    def __init__(self) -> None:
        """Initialize the Tester agent with the default peer tools."""
        self.agent: Agent[None] = Agent(
            name="Tester Agent",
            instructions=(
                "You are an A2A testing agent. Your goal is to verify that peer agents "
                "respond correctly by exercising their capabilities.\n\n"
                "Testing workflow:\n"
                "1. Use list_agents to discover available agents\n"
                "2. Use get_agent_card_details to inspect an agent's capabilities:\n"
                "   - Check input_modes (text/plain, application/json, etc.)\n"
                "   - Check output_modes\n"
                "   - Extract schema_urls from skill descriptions\n"
                "3. If schema_urls are available, use http_get to fetch the JSON schema\n"
                "4. Send test requests using the appropriate method:\n"
                "   - send_message for text/plain agents (plain text messages)\n"
                "   - send_data_message for application/json agents (structured data)\n"
                "5. Validate responses and report results\n\n"
                "When testing application/json agents, construct valid JSON payloads "
                "matching the schema you fetched. For text/plain agents, send plain text."
            ),
            handoffs=[],
            tool_use_behavior="run_llm_again",
            tools=self._build_tools(),
        )
        self.history: list[str] = []

    def _build_tools(self) -> list[Tool]:
        """Build the Tester agent's toolset."""
        peer_tools: list[Tool] = default_peer_tools()
        discovery: list[Tool] = discovery_tools()
        create_new_session_tool = session_management_tool()
        return [create_new_session_tool, *peer_tools, *discovery]

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
