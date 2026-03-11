"""Group Chat manager using Microsoft Agent Framework orchestrations."""

import logging
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass

from agent_framework import Agent, Message
from agent_framework.openai import OpenAIChatClient
from agent_framework.orchestrations import GroupChatBuilder, GroupChatState

logger: logging.Logger = logging.getLogger(__name__)

_ORCHESTRATOR_NAME = "group_chat_orchestrator"


@dataclass
class AgentSpec:
    """Specification for a group chat participant."""

    name: str
    system_prompt: str


@dataclass
class ChatEvent:
    """An event yielded during group chat execution."""

    agent_name: str
    text: str
    is_streaming: bool = True


class ChatManager:
    """Manages dynamic group chat agents and conversation state."""

    def __init__(self) -> None:
        """Initialize the chat manager."""
        self._agent_specs: dict[str, AgentSpec] = {}
        self._conversations: dict[str, list[Message]] = {}

    @property
    def agent_specs(self) -> list[AgentSpec]:
        """Return all configured agent specifications."""
        return list(self._agent_specs.values())

    def add_agent(self, name: str, system_prompt: str) -> AgentSpec:
        """Add an agent to the group chat."""
        spec = AgentSpec(name=name, system_prompt=system_prompt)
        self._agent_specs[name] = spec
        logger.info("Added agent: %s", name)
        return spec

    def remove_agent(self, name: str) -> bool:
        """Remove an agent from the group chat."""
        if name in self._agent_specs:
            del self._agent_specs[name]
            logger.info("Removed agent: %s", name)
            return True
        return False

    def _build_agents(self) -> list[Agent]:
        client = OpenAIChatClient(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_id=os.getenv("OPENAI_CHAT_MODEL_ID", "gpt-4o-mini"),
        )
        return [
            Agent(
                client=client,
                name=spec.name,
                description=f"Agent: {spec.name}",
                instructions=spec.system_prompt,
            )
            for spec in self._agent_specs.values()
        ]

    async def run_chat(
        self,
        thread_id: str,
        user_message: str,
    ) -> AsyncIterator[ChatEvent]:
        """Run the group chat and yield events for each agent response.

        Args:
            thread_id: Conversation thread identifier.
            user_message: The user's latest message.

        Yields:
            ChatEvent for each piece of agent output.

        """
        agents = self._build_agents()
        if not agents:
            yield ChatEvent(
                agent_name="System",
                text="No agents configured. Add agents using the panel on the right.",
                is_streaming=False,
            )
            return

        # Build full message history: prior turns + new user message
        history = list(self._conversations.get(thread_id, []))
        history.append(Message("user", [user_message]))

        # Termination counts only new messages added in this run
        history_offset = len(history)
        max_rounds = len(agents) * 2

        def round_robin_selector(state: GroupChatState) -> str:
            participant_names = list(state.participants.keys())
            return participant_names[state.current_round % len(participant_names)]

        def termination_condition(conversation: list[Message]) -> bool:
            return len(conversation) - history_offset >= max_rounds

        workflow = GroupChatBuilder(
            participants=agents,
            termination_condition=termination_condition,
            selection_func=round_robin_selector,
        ).build()

        logger.info(
            "Running group chat for thread=%s with %d agents, history_len=%d",
            thread_id,
            len(agents),
            len(history),
        )

        async for event in workflow.run(history, stream=True):
            if event.type != "output" or not isinstance(event.data, list):
                continue
            full_conversation: list[Message] = event.data  # type: ignore[assignment]
            # Persist the full updated conversation for next turn
            self._conversations[thread_id] = full_conversation
            # Yield only the new assistant messages from this run
            for msg in full_conversation[history_offset:]:
                if msg.role == "assistant" and msg.author_name != _ORCHESTRATOR_NAME:
                    text = msg.text or ""
                    if text:
                        yield ChatEvent(
                            agent_name=msg.author_name or "Assistant",
                            text=text,
                        )
