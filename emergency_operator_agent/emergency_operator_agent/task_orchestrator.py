"""Task-based orchestration for emergency dispatch workflow."""

import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    AgentCard,
    Message,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    SendMessageResponse,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)
from a2a.utils import new_agent_text_message
from shared.peer_tools import HTTPX_TIMEOUT, load_peer_addresses_from_registry

logger = logging.getLogger(__name__)


@dataclass
class DispatchStep:
    """A single step in the emergency dispatch plan."""

    step_id: str
    agent_name: str
    agent_address: str
    agent_description: str
    message: str
    status: TaskState = TaskState.submitted
    response: str | None = None
    error: str | None = None


@dataclass
class EmergencyTask:
    """Represents an emergency dispatch task with multiple steps."""

    task_id: str
    context_id: str
    location: str
    description: str
    steps: list[DispatchStep] = field(default_factory=list)
    current_step: int = 0
    state: TaskState = TaskState.submitted

    def add_step(
        self,
        agent_name: str,
        agent_address: str,
        agent_description: str,
        message: str,
    ) -> None:
        """Add a dispatch step to the task plan."""
        step = DispatchStep(
            step_id=f"{self.task_id}-step-{len(self.steps)}",
            agent_name=agent_name,
            agent_address=agent_address,
            agent_description=agent_description,
            message=message,
        )
        self.steps.append(step)

    def get_current_step(self) -> DispatchStep | None:
        """Get the current step being executed."""
        if 0 <= self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None

    def advance_step(self) -> bool:
        """Move to the next step. Returns False if no more steps."""
        self.current_step += 1
        return self.current_step < len(self.steps)

    def is_complete(self) -> bool:
        """Check if all steps are completed."""
        return self.current_step >= len(self.steps)

    def get_progress(self) -> tuple[int, int]:
        """Get progress as (completed, total)."""
        return (self.current_step, len(self.steps))


class EmergencyTaskOrchestrator:
    """Orchestrates emergency dispatch tasks with step-by-step execution."""

    # Class-level cache shared across all instances
    _class_agent_cache: dict[str, AgentCard] | None = None

    def __init__(self) -> None:
        """Initialize the orchestrator."""
        self.active_tasks: dict[str, EmergencyTask] = {}
        # Instance cache now references the class-level cache
        self._agent_cache = EmergencyTaskOrchestrator._class_agent_cache

    async def _fetch_available_agents(
        self,
        event_queue: EventQueue | None = None,
        task_id: str | None = None,
        context_id: str | None = None,
    ) -> dict[str, AgentCard]:
        """Fetch all available agents from the registry with their cards.
        
        Args:
            event_queue: Optional event queue to send progress updates (keeps queue alive)
            task_id: Optional task ID for progress messages
            context_id: Optional context ID for progress messages
        
        Returns:
            Dictionary mapping agent addresses to their AgentCards
            
        """
        if EmergencyTaskOrchestrator._class_agent_cache is not None:
            return EmergencyTaskOrchestrator._class_agent_cache

        agents: dict[str, AgentCard] = {}
        addresses = await load_peer_addresses_from_registry()

        logger.info(
            "Loaded %d addresses from registry. A2A_REGISTRY_URL=%s",
            len(addresses),
            os.getenv("A2A_REGISTRY_URL", "NOT SET"),
        )

        if not addresses:
            logger.warning("No agents available in registry")
            return agents

        # Send initial discovery message to keep EventQueue alive
        if event_queue and task_id and context_id:
            await self._send_message(
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id,
                text=f"Discovering {len(addresses)} emergency services...",
            )

        async with httpx.AsyncClient(timeout=HTTPX_TIMEOUT) as httpx_client:
            for idx, agent_address in enumerate(addresses, 1):
                # Send progress update to keep EventQueue alive
                if event_queue and task_id and context_id and idx % 2 == 1:  # Every other card
                    await self._send_message(
                        event_queue=event_queue,
                        task_id=task_id,
                        context_id=context_id,
                        text=f"Checking service {idx}/{len(addresses)}...",
                    )

                try:
                    resolver = A2ACardResolver(
                        httpx_client=httpx_client,
                        base_url=agent_address,
                    )
                    agent_card: AgentCard = await resolver.get_agent_card()
                    agents[agent_address] = agent_card
                    logger.debug(
                        "Discovered agent: %s at %s",
                        agent_card.name,
                        agent_address,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.debug(
                        "Failed to fetch card from %s: %s",
                        agent_address,
                        exc,
                    )

        EmergencyTaskOrchestrator._class_agent_cache = agents
        logger.info("Cached %d agents from registry", len(agents))
        return agents

    def _has_emergency_keywords(
        self,
        message: str,
        keywords: list[str],
    ) -> bool:
        """Check if message contains any of the keywords."""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in keywords)

    def _has_agent_capabilities(
        self,
        combined_text: str,
        capabilities: list[str],
    ) -> bool:
        """Check if agent has any of the capabilities."""
        return any(term in combined_text for term in capabilities)

    def _match_agents_to_emergency(
        self,
        message: str,
        available_agents: dict[str, AgentCard],
    ) -> list[tuple[str, AgentCard]]:
        """Match relevant agents based on emergency message.

        Args:
            message: The emergency description
            available_agents: Available agent cards mapped by address

        Returns:
            List of (address, AgentCard) tuples for relevant agents

        """
        matched_agents: list[tuple[str, AgentCard]] = []

        for address, card in available_agents.items():
            # Check agent name and description
            agent_text = f"{card.name} {card.description}".lower()

            # Check skill tags
            skill_tags = []
            for skill in card.skills or []:
                skill_tags.extend(skill.tags or [])
            skill_text = " ".join(skill_tags).lower()

            # Simple keyword matching (in production, use LLM)
            combined_text = f"{agent_text} {skill_text}"

            # Check for fire emergency match
            if self._has_emergency_keywords(
                message,
                ["fire", "burning", "smoke", "flame"],
            ) and self._has_agent_capabilities(
                combined_text,
                ["fire", "firefighter", "extinguish"],
            ):
                matched_agents.append((address, card))
                continue

            # Check for police emergency match
            if self._has_emergency_keywords(
                message,
                ["police", "arrest", "criminal", "theft", "crime"],
            ) and self._has_agent_capabilities(
                combined_text,
                ["police", "crime", "investigation"],
            ):
                matched_agents.append((address, card))
                continue

            # Check for medical emergency match
            if self._has_emergency_keywords(
                message,
                ["ambulance", "injury", "injured", "medical", "hurt"],
            ) and self._has_agent_capabilities(
                combined_text,
                ["ambulance", "medical", "paramedic", "emergency medical"],
            ):
                matched_agents.append((address, card))
                continue

            # Check for weather service match
            if self._has_emergency_keywords(
                message,
                ["weather", "forecast", "rain", "storm"],
            ) and self._has_agent_capabilities(
                combined_text,
                ["weather", "forecast", "meteorology"],
            ):
                matched_agents.append((address, card))
                continue

        return matched_agents

    async def _send_message(
        self,
        event_queue: EventQueue,
        task_id: str,
        context_id: str,
        text: str,
        final: bool = False,
    ) -> None:
        """Send a task status update with a text message.
        
        Uses TaskStatusUpdateEvent instead of bare Message to prevent
        the A2A SDK from treating intermediate messages as final events.
        """
        status_message = new_agent_text_message(
            context_id=context_id,
            text=text,
            task_id=task_id,
        )

        status_update = TaskStatusUpdateEvent(
            task_id=task_id,
            context_id=context_id,
            status=TaskStatus(
                state=TaskState.working,
                message=status_message,
                timestamp=datetime.now(UTC).isoformat(),
            ),
            final=final,
        )

        await event_queue.enqueue_event(event=status_update)

    async def _dispatch_to_agent(
        self,
        agent_name: str,
        agent_address: str,
        message: str,
        context_id: str,
    ) -> SendMessageResponse | None:
        """Dispatch a message to a specific agent using cached address."""
        async with httpx.AsyncClient(timeout=HTTPX_TIMEOUT) as httpx_client:
            try:
                resolver = A2ACardResolver(
                    httpx_client=httpx_client,
                    base_url=agent_address,
                )
                agent_card: AgentCard = await resolver.get_agent_card()

                logger.info(
                    "Dispatching to %s at %s with context_id=%s",
                    agent_name,
                    agent_address,
                    context_id,
                )
                client = A2AClient(
                    httpx_client=httpx_client,
                    agent_card=agent_card,
                )
                try:
                    response: SendMessageResponse = (
                        await client.send_message(
                            request=SendMessageRequest(
                                id=uuid4().hex,
                                jsonrpc="2.0",
                                method="message/send",
                                params=MessageSendParams(
                                    message=Message(
                                        context_id=context_id,
                                        role=Role.user,
                                        message_id=uuid4().hex,
                                        parts=[
                                            Part(
                                                root=TextPart(
                                                    kind="text",
                                                    text=message,
                                                ),
                                            ),
                                        ],
                                    ),
                                ),
                            ),
                        )
                    )
                    return response
                except Exception:
                    logger.exception(
                        "Failed to dispatch to %s",
                        agent_name,
                    )
                    return None
            except Exception as exc:  # noqa: BLE001
                logger.debug(
                    "Failed to get agent card for %s at %s: %s",
                    agent_name,
                    agent_address,
                    exc,
                )
                return None

    async def create_task_plan(
        self,
        task_id: str,
        context_id: str,
        user_message: str,
        event_queue: EventQueue,
    ) -> EmergencyTask:
        """Analyze the emergency and create a task plan.

        Args:
            task_id: Unique task identifier
            context_id: Context identifier for the conversation
            user_message: The emergency description from the user
            event_queue: Queue for sending SSE updates

        Returns:
            EmergencyTask with dispatch plan

        """
        await self._send_message(
            event_queue=event_queue,
            task_id=task_id,
            context_id=context_id,
            text="[ALERT] Emergency call received. Analyzing situation...",
        )

        task = EmergencyTask(
            task_id=task_id,
            context_id=context_id,
            location="",  # Extract from user_message
            description=user_message,
        )

        # Fetch available agents dynamically from registry
        # Send progress message BEFORE fetch to keep queue alive
        await self._send_message(
            event_queue=event_queue,
            task_id=task_id,
            context_id=context_id,
            text="Checking emergency services registry...",
        )

        available_agents = await self._fetch_available_agents(
            event_queue=event_queue,
            task_id=task_id,
            context_id=context_id,
        )

        # Send message AFTER fetch completes
        await self._send_message(
            event_queue=event_queue,
            task_id=task_id,
            context_id=context_id,
            text=f"Found {len(available_agents)} emergency services available.",
        )

        if not available_agents:
            logger.error(
                "❌ CRITICAL: No agents available, task_id=%s - about to send warning",
                task_id,
            )
            await self._send_message(
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id,
                text="[WARNING] No emergency services available in the registry.",
            )
            logger.error("❌ Warning message enqueue completed for task_id=%s", task_id)
            return task

        # Match agents based on emergency description
        matched_agents = self._match_agents_to_emergency(
            message=user_message,
            available_agents=available_agents,
        )

        # Create dispatch steps for matched agents
        for address, agent_card in matched_agents:
            task.add_step(
                agent_name=agent_card.name,
                agent_address=address,
                agent_description=agent_card.description,
                message=f"Emergency dispatch: {user_message}",
            )
            logger.info(
                "Added dispatch step for %s (%s) at %s",
                agent_card.name,
                agent_card.description,
                address,
            )

        # Store task
        self.active_tasks[task_id] = task

        # Notify user of the plan
        if task.steps:
            services = ", ".join(step.agent_name for step in task.steps)
            await self._send_message(
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id,
                text=f"[PLAN] Dispatch plan created: {services}",
            )
        else:
            await self._send_message(
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id,
                text="[WARNING] No emergency services matched for this request.",
            )

        return task

    async def execute_task(
        self,
        task: EmergencyTask,
        event_queue: EventQueue,
    ) -> None:
        """Execute all steps of an emergency task.

        Args:
            task: The emergency task to execute
            event_queue: Queue for sending SSE updates

        """
        if not task.steps:
            logger.info(
                "No steps to execute for task_id=%s, sending completion message",
                task.task_id,
            )
            await self._send_message(
                event_queue=event_queue,
                task_id=task.task_id,
                context_id=task.context_id,
                text="[COMPLETE] No emergency services required. Call handled.",
            )
            return

        task.state = TaskState.working

        # WORKAROUND: Send ALL dispatch announcements BEFORE making any HTTP calls
        # This prevents A2A SDK's EventQueue from closing during HTTP operations
        total = len(task.steps)
        for idx, step in enumerate(task.steps, start=1):
            progress_text = f"[{idx}/{total}]"
            await self._send_message(
                event_queue=event_queue,
                task_id=task.task_id,
                context_id=task.context_id,
                text=f"[PLAN] {progress_text} Will dispatch {step.agent_name}",
            )

        # Now execute each step sequentially (HTTP calls happen here)
        while not task.is_complete():
            step = task.get_current_step()
            if not step:
                break

            # Update step status (no event sent here)
            step.status = TaskState.working

            # Dispatch to the agent (HTTP call)
            response = await self._dispatch_to_agent(
                agent_name=step.agent_name,
                agent_address=step.agent_address,
                message=step.message,
                context_id=task.context_id,
            )

            # Update step result based on response
            if response:
                step.status = TaskState.completed
                step.response = "Acknowledged"
            else:
                step.status = TaskState.failed
                step.error = "Failed to contact agent"

            # Move to next step
            task.advance_step()

        # Task complete
        task.state = TaskState.completed

        # Send summary
        successful = sum(
            1 for step in task.steps if step.status == TaskState.completed
        )
        failed = sum(
            1 for step in task.steps if step.status == TaskState.failed
        )

        if failed == 0:
            summary = (
                f"[COMPLETE] All emergency services dispatched successfully "
                f"({successful}/{len(task.steps)})"
            )
        else:
            summary = (
                f"[COMPLETE] Dispatch finished with issues: "
                f"{successful} successful, {failed} failed"
            )

        logger.info(
            "Task execution complete, sending summary: task_id=%s summary=%s",
            task.task_id,
            summary,
        )
        await self._send_message(
            event_queue=event_queue,
            task_id=task.task_id,
            context_id=task.context_id,
            text=summary,
            final=True,
        )

        # Clean up
        if task.task_id in self.active_tasks:
            del self.active_tasks[task.task_id]

    def get_task(self, task_id: str) -> EmergencyTask | None:
        """Retrieve an active task by ID."""
        return self.active_tasks.get(task_id)

