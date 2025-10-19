"""Core agent behavior for the FBI agent."""

import logging
from secrets import choice
from typing import ClassVar

from a2a.server.agent_execution.context import RequestContext
from agents import Agent, Runner, RunResult, SQLiteSession, Tool, function_tool
from agents.memory.session import Session
from shared.peer_tools import default_peer_tools, peer_message_context

logger: logging.Logger = logging.getLogger(name=__name__)

class FBIAgent:
    """Encapsulates FBI specific reasoning via the OpenAI Agent SDK."""

    investigation_updates: ClassVar[list[str]] = [
        "Coordinating with cyber division for forensic analysis.",
        "Joint task force notified; assets deploying.",
        "Evidence intake scheduled with federal prosecutors.",
    ]
    threat_updates: ClassVar[list[str]] = [
        "Threat level assessed as elevated; monitoring continues.",
        "Threat mitigated through interagency response.",
        "Additional intelligence requested from homeland partners.",
    ]
    sessions: ClassVar[dict[str, Session]] = {}

    def __init__(self) -> None:
        """Initialize the FBI agent with its tools and behavior."""
        self.agent: Agent = Agent(
            name="FBI Agent",
            instructions=(
                "You are an FBI dispatcher handling federal crimes and"
                " national security threats. Make your own determination"
                " about whether a situation is federal or local. When a"
                " situation is local, rely on your reasoning to direct the"
                " caller to contact their local police department (call"
                " 311 or the local police number). Use your tools to list"
                " peer agents and message them whenever coordination is"
                " helpful."
            ),
            handoffs=[],
            tool_use_behavior="run_llm_again",
            tools=self._build_tools(),
        )

    def _build_tools(self) -> list[Tool]:
        list_agents_tool, send_message_tool = default_peer_tools()

        @function_tool
        async def handle_federal_investigation(
            location: str,
            case: str | None = None,
        ) -> str:
            logger.info(
                "Tool handle_federal_investigation invoked with location=%s case=%s",
                location,
                case,
            )
            update: str = choice(self.investigation_updates)
            case_text: str = f" Case reference: {case}." if case else ""
            return (
                "Initiated federal investigation at "
                f"{location}.{case_text} {update}"
            ).strip()

        @function_tool
        async def assess_threat_level(summary: str) -> str:
            logger.info(
                "Tool assess_threat_level invoked with summary=%s",
                summary,
            )
            update: str = choice(self.threat_updates)
            return f"Analyzed threat summary '{summary}'. {update}"

        return [
            handle_federal_investigation,
            assess_threat_level,
            list_agents_tool,
            send_message_tool,
        ]

    async def invoke(self, context: RequestContext) -> str:
        """Invoke the FBI agent with the provided context."""
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
            if context.context_id not in FBIAgent.sessions:
                FBIAgent.sessions[context.context_id] = SQLiteSession(
                    session_id=context.context_id,
                )
            session = FBIAgent.sessions[context.context_id]
        return session
