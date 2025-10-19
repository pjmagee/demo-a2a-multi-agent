"""Core agent behaviour for the Ambulance agent."""

import logging
from secrets import choice
from typing import ClassVar

from a2a.server.agent_execution.context import RequestContext
from a2a.types import Message
from agents import Agent, Runner, RunResult, SQLiteSession, Tool, function_tool
from agents.memory.session import Session
from shared.peer_tools import default_peer_tools, peer_message_context

logger: logging.Logger = logging.getLogger(name=__name__)


class AmbulanceAgent:
    """Encapsulates ambulance dispatch behaviour."""

    care_updates: ClassVar[list[str]] = [
        "Patient stabilized and ready for transport.",
        "Administered first aid and monitoring vitals.",
        "Coordinating with ER for arrival in 8 minutes.",
    ]
    transport_updates: ClassVar[list[str]] = [
        "Route cleared with priority sirens.",
        "Transporting with paramedic support in transit.",
        "Arriving at trauma center shortly.",
    ]
    sessions: ClassVar[dict[str, Session]] = {}

    def __init__(self) -> None:
        """Initialize the AmbulanceAgent."""
        self.agent = Agent(
            name="Ambulance Agent",
            instructions=(
                "You dispatch ambulances and provide medical status"
                " updates. If a caller asks about weather, direct them"
                " to the WeatherAgent."
            ),
            handoffs=[],
            tool_use_behavior="run_llm_again",
            tools=self._build_tools(),
        )

    def _build_tools(self) -> list[Tool]:
        list_agents_tool, send_message_tool = default_peer_tools()

        @function_tool
        async def provide_field_care(location: str) -> str:
            """Provide field care to a patient at a given location."""
            logger.info(
                "Tool provide_field_care invoked with location=%s",
                location,
            )
            update: str = choice(self.care_updates)
            return f"Ambulance dispatched to {location}. {update}"

        @function_tool
        async def transport_patient(destination: str) -> str:
            """Transport a patient to a given destination."""
            logger.info(
                "Tool transport_patient invoked with destination=%s",
                destination,
            )
            update: str = choice(self.transport_updates)
            return f"Patient en route to {destination}. {update}"

        return [
            provide_field_care,
            transport_patient,
            list_agents_tool,
            send_message_tool,
        ]

    async def invoke(self, context: RequestContext) -> str:
        """Invoke the AmbulanceAgent."""
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
        if isinstance(context.message, Message) and context.message.context_id:
            if context.message.context_id not in AmbulanceAgent.sessions:
                AmbulanceAgent.sessions[context.message.context_id] = SQLiteSession(
                    session_id=context.message.context_id,
                )
            session = AmbulanceAgent.sessions[context.message.context_id]
        return session
