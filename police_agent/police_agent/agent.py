"""Core agent behaviour for the Police agent."""


import logging
from secrets import choice
from typing import ClassVar

from a2a.server.agent_execution.context import RequestContext
from agents import Agent, Runner, RunResult, SQLiteSession, Tool, function_tool
from agents.memory.session import Session
from shared.peer_tools import default_peer_tools, peer_message_context

logger: logging.Logger = logging.getLogger(name=__name__)

class PoliceAgent:
    """Encapsulates local policing behaviour using the OpenAI Agent SDK."""

    traffic_messages: ClassVar[list[str]] = [
        "Officers are managing traffic and setting up cones.",
        "Traffic rerouted to adjacent streets.",
        "Tow trucks dispatched; expect delays for 20 minutes.",
    ]
    crime_messages: ClassVar[list[str]] = [
        "Officers on scene collecting witness statements.",
        "Crime scene secured; forensics en route.",
        "Patrol units canvassing neighbouring blocks for leads.",
    ]
    sessions: ClassVar[dict[str, Session]] = {}

    def __init__(self) -> None:
        """Initialise the PoliceAgent with the required tools and instructions."""
        self.agent: Agent = Agent(
            name="Police Agent",
            instructions=(
                "You are a local police dispatcher supporting the 911 operator."
                " Handle local crimes and traffic incidents. When a caller"
                " faces a life-threatening emergency, identify the most"
                " appropriate responder agent and coordinate with them,"
                " while reminding the caller to contact the 911 operator"
                " immediately for emergency services. When a request"
                " involves federal matters, direct the caller to contact"
                " the FBI by providing the Agents name and address from the list agents tool."
            ),
            handoffs=[],
            tool_use_behavior="run_llm_again",
            tools=self._build_tools(),
        )

    def _build_tools(self) -> list[Tool]:
        peer_tools: list[Tool] = default_peer_tools()

        @function_tool
        async def deploy_crime_response(location: str) -> str:
            logger.info(
                "Tool deploy_crime_response invoked with location=%s",
                location,
            )
            outcome: str = choice(self.crime_messages)
            return f"Dispatched officers to {location}. {outcome}"

        @function_tool
        async def manage_traffic_flow(location: str) -> str:
            logger.info(
                "Tool manage_traffic_flow invoked with location=%s",
                location,
            )
            outcome: str = choice(self.traffic_messages)
            return f"Traffic response initiated at {location}. {outcome}"

        return [
            deploy_crime_response,
            manage_traffic_flow,
            *peer_tools,
        ]

    async def invoke(self, context: RequestContext) -> str:
        """Invoke the PoliceAgent with the provided context."""

        user_input: str = context.get_user_input()
        session: Session | None = self._get_or_create_session(context=context)
        context_id: str | None = (
            context.context_id if isinstance(context.context_id, str) else None
        )

        with peer_message_context(context_id):
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
            if context.context_id not in PoliceAgent.sessions:
                PoliceAgent.sessions[context.context_id] = SQLiteSession(
                    session_id=context.context_id,
                )
            session = PoliceAgent.sessions[context.context_id]
        return session
