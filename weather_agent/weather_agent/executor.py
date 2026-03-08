"""Weather agent executor using OpenAI Agent SDK with tool-call streaming."""

import logging
from typing import override

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.utils import new_agent_text_message
from agents import InputGuardrailTripwireTriggered
from shared.openai_session_helpers import get_or_create_session
from shared.openai_streaming import stream_openai_agent
from shared.peer_tools import peer_message_context
from shared.traced_executor import a2a_session

from weather_agent.agent import WeatherAgent

logger: logging.Logger = logging.getLogger(name=__name__)

class WeatherAgentExecutor(AgentExecutor):
    """Adapter invoked by the A2A DefaultRequestHandler.

    Uses streaming to emit tool-call and tool-call-result events
    following the a2a-ui metadata convention.
    """

    def __init__(self) -> None:
        """Initialize the adapter with the underlying agent."""
        self.agent = WeatherAgent()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        with a2a_session(context, type(self).__name__) as context_id:
            task_id = context.task_id or context_id
            user_input = context.get_user_input()
            session = get_or_create_session(
                sessions=WeatherAgent.sessions,
                context_id=context_id,
            )

            with peer_message_context(context_id=context_id):
                try:
                    await stream_openai_agent(
                        agent=self.agent.agent,
                        user_input=user_input,
                        session=session,
                        context_id=context_id,
                        task_id=task_id,
                        event_queue=event_queue,
                    )
                except InputGuardrailTripwireTriggered as ex:
                    logger.warning("Guardrail tripwire triggered")
                    response_text = await self.agent._create_tripwire_response(
                        user_input=user_input,
                        ex=ex,
                    )
                    await event_queue.enqueue_event(
                        event=new_agent_text_message(
                            context_id=context_id,
                            text=response_text,
                            task_id=task_id,
                        ),
                    )
                except Exception:
                    logger.exception(
                        "Agent invocation failed context_id=%s",
                        context_id,
                    )
                    await event_queue.enqueue_event(
                        event=new_agent_text_message(
                            context_id=context_id,
                            text="I apologize, but I encountered an error processing your request.",
                            task_id=context.task_id,
                        ),
                    )

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        msg = "Cancellation is not supported for WeatherAgent"
        raise RuntimeError(msg)
