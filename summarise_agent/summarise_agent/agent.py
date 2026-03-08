"""Core agent behaviour for the Summarise agent."""

import logging
from typing import ClassVar

from a2a.server.agent_execution.context import RequestContext
from agents import Agent, Runner, RunResult
from agents.memory.session import Session
from shared.openai_session_helpers import get_or_create_session

logger: logging.Logger = logging.getLogger(name=__name__)


class SummariseAgent:
    """Generates short descriptive titles for conversations."""

    sessions: ClassVar[dict[str, Session]] = {}

    def __init__(self) -> None:
        """Initialise the Summarise agent."""
        self.agent = Agent(
            name="Summarise Agent",
            instructions=(
                "You are a conversation title generator. Given a conversation "
                "between a user and an assistant, produce a short, descriptive "
                "title that captures the main topic. Rules:\n"
                "- Output ONLY the title text, nothing else\n"
                "- Keep it between 3 and 8 words\n"
                "- Do not include quotes or punctuation at the end\n"
                "- Use title case\n"
                "- Be specific rather than generic"
            ),
            handoffs=[],
            tool_use_behavior="run_llm_again",
            tools=[],
        )

    async def invoke(self, context: RequestContext, context_id: str) -> str:
        """Execute the agent for the provided request context.

        Args:
            context: Request context containing conversation history
            context_id: Guaranteed non-null context ID

        Returns:
            A short descriptive title for the conversation

        """
        user_input: str = context.get_user_input()
        session: Session = get_or_create_session(
            sessions=SummariseAgent.sessions,
            context_id=context_id,
        )

        result: RunResult = await Runner.run(
            starting_agent=self.agent,
            input=user_input,
            session=session,
        )

        response_text: str = result.final_output_as(
            cls=str,
            raise_if_incorrect_type=True,
        )
        return response_text.strip().strip('"').strip("'")
