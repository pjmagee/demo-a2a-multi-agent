"""Core agent behavior for the Fire Brigade Agent."""

import logging
from secrets import choice
from typing import ClassVar

from a2a.server.agent_execution.context import RequestContext
from agents import (
    Agent,
    ModelSettings,
    Runner,
    RunResult,
    SQLiteSession,
    Tool,
    FunctionTool,
    function_tool,
)
from agents.memory.session import Session
from shared.peer_tools import default_peer_tools, peer_message_context

logger: logging.Logger = logging.getLogger(name=__name__)


class FireBrigadeAgent:
    """Encapsulates Fire Bridage specific reasoning via the OpenAI Agent SDK."""

    status_updates: ClassVar[list[str]] = [
        "Fire contained successfully; ventilation in progress.",
        "Fire fully extinguished; beginning overhaul operations.",
        "Fire under control; monitoring hot spots for rekindle.",
    ]
    risk_levels: ClassVar[list[str]] = ["low", "moderate", "high"]
    sessions: ClassVar[dict[str, Session]] = {}

    def __init__(self) -> None:
        """Initialize the FireFighterAgent with its configuration."""
        self.agent = Agent(
            name="Fire Brigade Agent",
            instructions=(
                "You are a municipal firefighter dispatcher. When a citizen"
                " reports a fire emergency you coordinate a response,"
                " dispatch teams, and provide concise status updates."
                " Keep communication clear and acknowledge receipt of"
                " critical information."
            ),
            handoffs=[],
            tool_use_behavior="run_llm_again",
            tools=self._build_tools(),
            model_settings=ModelSettings(tool_choice="auto"),
        )

    def _build_tools(self) -> list[Tool]:
        """Construct the FireFighterAgent's toolset."""
        peer_tools: list[Tool] = default_peer_tools()

        @function_tool
        async def dispatch_fire_unit(location: str, severity: str | None = None) -> str:
            """Send a fire response team to the specified location.

            Args:
                location: The address or description of the fire location.
                severity: Optional severity level of the fire. (e.g., "low", "moderate", "high")

            """
            logger.info(
                "Tool dispatch_fire_unit invoked with location=%s severity=%s",
                location,
                severity,
            )
            update: str = choice(self.status_updates)
            details: str = f"Dispatching teams to {location}. {update}"
            if severity:
                return f"{details} Reported severity: {severity}."
            return details

        @function_tool
        async def evaluate_fire_risk(location: str) -> str:
            """Produce a qualitative fire risk assessment for the location."""
            logger.info(
                "Tool evaluate_fire_risk invoked with location=%s",
                location,
            )
            risk: str = choice(self.risk_levels)
            return f"The fire risk at {location} is {risk}."

        return [dispatch_fire_unit, evaluate_fire_risk, *peer_tools]


    async def invoke(self, context: RequestContext) -> str:
        """Invoke the FireFighterAgent with the provided context."""
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
            if context.context_id not in FireBrigadeAgent.sessions:
                FireBrigadeAgent.sessions[context.context_id] = SQLiteSession(
                    session_id=context.context_id,
                )
            session = FireBrigadeAgent.sessions[context.context_id]
        return session
