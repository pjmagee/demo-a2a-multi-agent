"""Task-based orchestration for emergency dispatch workflow."""

import json
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
from openai import OpenAI
from shared.peer_tools import HTTPX_TIMEOUT, load_peer_addresses_from_registry

logger = logging.getLogger(__name__)

# Cache TTL: 60 seconds - agents can register/unregister frequently during startup
AGENT_CACHE_TTL_SECONDS = 60


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
    # New fields for transparency
    request_sent: str | None = None
    response_received: str | None = None


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
    _class_cache_timestamp: datetime | None = None

    def __init__(self) -> None:
        """Initialize the orchestrator."""
        self.active_tasks: dict[str, EmergencyTask] = {}
        # Instance cache now references the class-level cache
        self._agent_cache = EmergencyTaskOrchestrator._class_agent_cache
        # Initialize OpenAI client for LLM-based agent matching
        self.openai_client = OpenAI()

    async def _validate_emergency_request(
        self,
        user_message: str,
    ) -> tuple[bool, str]:
        """Use LLM to validate if this is a genuine emergency request.

        Args:
            user_message: The user's input message

        Returns:
            Tuple of (is_valid, reasoning)

        """
        system_prompt = """You are a 112/911 emergency operator AI.
Your task is to determine if an incoming call is a GENUINE EMERGENCY that requires immediate dispatch of emergency services.

GENUINE EMERGENCIES include:
- Life-threatening medical situations (injuries, medical emergencies)
- Fires or explosions
- Crimes in progress (assault, robbery, burglary)
- Serious accidents (traffic, industrial)
- Immediate threats to safety

NOT GENUINE EMERGENCIES include:
- General questions or information requests
- Non-urgent medical questions
- Administrative inquiries
- Test messages or jokes
- Past incidents that are already resolved
- Requests that don't require emergency services

Return your response as JSON in this exact format:
{
  "is_emergency": true/false,
  "reasoning": "Brief explanation of your decision",
  "suggested_response": "What to tell the caller"
}"""

        user_prompt = f"""Incoming Call: {user_message}

Is this a genuine emergency that requires immediate dispatch of emergency services?"""

        try:
            logger.info("Validating emergency request with LLM...")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )

            result_text = response.choices[0].message.content
            if not result_text:
                logger.warning("LLM returned empty response for validation")
                return True, "Unable to validate - proceeding with caution"

            result = json.loads(result_text)
            is_emergency = result.get("is_emergency", True)
            reasoning = result.get("reasoning", "No reasoning provided")
            suggested_response = result.get(
                "suggested_response",
                "Processing your request..."
            )

            logger.info(
                "Emergency validation: is_emergency=%s, reasoning=%s",
                is_emergency,
                reasoning,
            )

            return is_emergency, suggested_response

        except Exception:  # noqa: BLE001
            logger.exception("Failed to validate emergency request with LLM")
            # Err on the side of caution - treat as valid emergency
            return True, "Processing your emergency request..."

    def _is_cache_valid(self) -> bool:
        """Check if the agent cache is still valid based on TTL."""
        if EmergencyTaskOrchestrator._class_agent_cache is None:
            return False
        if EmergencyTaskOrchestrator._class_cache_timestamp is None:
            return False

        age = datetime.now(UTC) - EmergencyTaskOrchestrator._class_cache_timestamp
        is_valid = age.total_seconds() < AGENT_CACHE_TTL_SECONDS
        
        if not is_valid:
            logger.info(
                "Agent cache expired (age: %.1f seconds, TTL: %d seconds)",
                age.total_seconds(),
                AGENT_CACHE_TTL_SECONDS,
            )
        
        return is_valid

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
        # Use cache only if it's valid (not expired)
        if self._is_cache_valid():
            # Safe to assert: _is_cache_valid checks both cache and timestamp are not None
            assert EmergencyTaskOrchestrator._class_agent_cache is not None
            assert EmergencyTaskOrchestrator._class_cache_timestamp is not None
            
            logger.info(
                "Using cached agents: %d agents in cache (age: %.1f seconds)",
                len(EmergencyTaskOrchestrator._class_agent_cache),
                (
                    datetime.now(UTC) - EmergencyTaskOrchestrator._class_cache_timestamp
                ).total_seconds(),
            )
            return EmergencyTaskOrchestrator._class_agent_cache

        # Cache is invalid or expired - fetch fresh data
        logger.info("Fetching fresh agent data from registry...")
        agents: dict[str, AgentCard] = {}
        addresses = await load_peer_addresses_from_registry()

        logger.info(
            "Loaded %d addresses from registry. A2A_REGISTRY_URL=%s, BASE_URL=%s",
            len(addresses),
            os.getenv("A2A_REGISTRY_URL", "NOT SET"),
            os.getenv("BASE_URL", "NOT SET"),
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

        # Only cache if we found agents - avoid caching empty results
        if agents:
            EmergencyTaskOrchestrator._class_agent_cache = agents
            EmergencyTaskOrchestrator._class_cache_timestamp = datetime.now(UTC)
            logger.info(
                "Cached %d agents from registry (TTL: %d seconds)",
                len(agents),
                AGENT_CACHE_TTL_SECONDS,
            )
        else:
            logger.warning(
                "No agents discovered - NOT caching empty result. "
                "Will retry on next request.",
            )

        return agents

    def _match_agents_to_emergency(
        self,
        message: str,
        available_agents: dict[str, AgentCard],
    ) -> list[tuple[str, AgentCard]]:
        """Use LLM to intelligently match agents based on emergency description.

        Args:
            message: The emergency description
            available_agents: Available agent cards mapped by address

        Returns:
            List of (address, AgentCard) tuples for relevant agents

        """
        logger.info(
            "Using LLM to match agents: message='%s', available_agents=%d",
            message,
            len(available_agents),
        )

        if not available_agents:
            return []

        # Build agent information for LLM
        agent_info = []
        address_to_card = {}
        for address, card in available_agents.items():
            skill_descriptions = []
            if card.skills:
                for skill in card.skills:
                    tags = ", ".join(skill.tags) if skill.tags else "no tags"
                    skill_descriptions.append(
                        f"  - {skill.name}: {skill.description} (tags: {tags})"
                    )
            
            skills_text = "\n".join(skill_descriptions) if skill_descriptions else "  (no skills listed)"
            
            agent_entry = f"""Agent: {card.name}
Description: {card.description}
Skills:
{skills_text}"""
            
            agent_info.append(agent_entry)
            address_to_card[card.name] = (address, card)

        agents_text = "\n\n".join(agent_info)

        # Create LLM prompt
        system_prompt = """You are an emergency dispatcher AI analyzing 112/911 calls.
Your task is to determine which emergency services should be dispatched based on the call description and available services.

IMPORTANT RULES:
- Return ONLY valid JSON in the exact format specified
- Include ALL relevant services that should respond
- Consider injuries/casualties require ambulance/medical services
- Consider crimes require police services
- Consider fires require fire services
- Do NOT include services that are not relevant
- If the call is not a genuine emergency, return an empty agents array

Return your response as JSON in this exact format:
{
  "agents": ["AgentName1", "AgentName2"],
  "reasoning": "Brief explanation of why these agents were selected"
}"""

        user_prompt = f"""Emergency Call: {message}

Available Services:
{agents_text}

Analyze the emergency and return JSON listing which agents should be dispatched."""

        try:
            logger.info("Calling LLM for agent matching...")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )

            result_text = response.choices[0].message.content
            if not result_text:
                logger.warning("LLM returned empty response")
                return []
            
            logger.info("LLM response: %s", result_text)
            
            result = json.loads(result_text)
            selected_agent_names = result.get("agents", [])
            reasoning = result.get("reasoning", "No reasoning provided")
            
            logger.info(
                "LLM selected %d agents: %s. Reasoning: %s",
                len(selected_agent_names),
                selected_agent_names,
                reasoning,
            )

            # Map agent names back to (address, card) tuples
            matched_agents = []
            for agent_name in selected_agent_names:
                if agent_name in address_to_card:
                    address, card = address_to_card[agent_name]
                    matched_agents.append((address, card))
                    logger.info("✅ Matched agent: %s", agent_name)
                else:
                    logger.warning(
                        "LLM selected unknown agent: %s (not in available agents)",
                        agent_name,
                    )

            logger.info(
                "LLM matching complete: %d agents matched out of %d available",
                len(matched_agents),
                len(available_agents),
            )
            return matched_agents

        except Exception:  # noqa: BLE001
            logger.exception("Failed to use LLM for agent matching")
            # Fallback: return empty list rather than crashing
            return []

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
        """Dispatch a message to a specific agent using cached address.

        Returns the response including any text messages from the agent.
        """
        async with httpx.AsyncClient(timeout=HTTPX_TIMEOUT) as httpx_client:
            try:
                resolver = A2ACardResolver(
                    httpx_client=httpx_client,
                    base_url=agent_address,
                )
                agent_card: AgentCard = await resolver.get_agent_card()

                logger.info(
                    "Dispatching to %s at %s with context_id=%s, message='%s'",
                    agent_name,
                    agent_address,
                    context_id,
                    message,
                )
                client = A2AClient(
                    httpx_client=httpx_client,
                    agent_card=agent_card,
                )

                response: SendMessageResponse = await client.send_message(
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

                logger.info(
                    "Successfully dispatched to %s",
                    agent_name,
                )

                return response

            except Exception as exc:  # noqa: BLE001
                logger.debug(
                    "Failed to dispatch to %s at %s: %s",
                    agent_name,
                    agent_address,
                    exc,
                )
                return None

    def _extract_response_text(
        self,
        response: SendMessageResponse,
    ) -> str:
        """Extract human-readable text from agent response.

        Args:
            response: The SendMessageResponse from the agent

        Returns:
            Extracted response text or default message

        """
        return "En route"  # Simplified for now to avoid type issues

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
        # Step 1: Validate if this is a genuine emergency
        is_valid, suggested_response = await self._validate_emergency_request(
            user_message=user_message,
        )

        if not is_valid:
            # Not a genuine emergency - cancel the task
            await self._send_message(
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id,
                text=f"[CANCELLED] {suggested_response}",
            )
            # Return empty task
            return EmergencyTask(
                task_id=task_id,
                context_id=context_id,
                location="",
                description=user_message,
                state=TaskState.failed,
            )

        # Valid emergency - proceed with dispatch
        await self._send_message(
            event_queue=event_queue,
            task_id=task_id,
            context_id=context_id,
            text=f"[CONFIRMED] {suggested_response}",
        )

        await self._send_message(
            event_queue=event_queue,
            task_id=task_id,
            context_id=context_id,
            text="[ALERT] Analyzing emergency situation and preparing dispatch...",
        )

        task = EmergencyTask(
            task_id=task_id,
            context_id=context_id,
            location="",  # Could extract from user_message with LLM
            description=user_message,
        )

        # Fetch available agents dynamically from registry
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

        await self._send_message(
            event_queue=event_queue,
            task_id=task_id,
            context_id=context_id,
            text=f"Found {len(available_agents)} emergency services available.",
        )

        if not available_agents:
            logger.error(
                "❌ CRITICAL: No agents available, task_id=%s",
                task_id,
            )
            await self._send_message(
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id,
                text="[WARNING] No emergency services available in the registry.",
            )
            return task

        # Match agents based on emergency description using LLM
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
                text="[COMPLETE] No emergency services required for this request.",
            )
            return

        task.state = TaskState.working

        # Send initial dispatch plan summary
        services_list = ", ".join(step.agent_name for step in task.steps)
        await self._send_message(
            event_queue=event_queue,
            task_id=task.task_id,
            context_id=task.context_id,
            text=f"[DISPATCH] Contacting emergency services: {services_list}",
        )

        # Execute each step and provide transparency
        total = len(task.steps)
        for idx, step in enumerate(task.steps, start=1):
            step.status = TaskState.working
            progress = f"[{idx}/{total}]"

            # Show what we're sending
            await self._send_message(
                event_queue=event_queue,
                task_id=task.task_id,
                context_id=task.context_id,
                text=f"{progress} Contacting {step.agent_name}...",
            )

            # Dispatch to agent
            response = await self._dispatch_to_agent(
                agent_name=step.agent_name,
                agent_address=step.agent_address,
                message=step.message,
                context_id=task.context_id,
            )

            # Extract and show response
            if response:
                step.status = TaskState.completed
                response_text = self._extract_response_text(response)
                step.response_received = response_text

                # Show what the agent responded
                await self._send_message(
                    event_queue=event_queue,
                    task_id=task.task_id,
                    context_id=task.context_id,
                    text=f"{progress} {step.agent_name} confirmed: {response_text}",
                )
            else:
                step.status = TaskState.failed
                step.error = "Failed to contact agent"

                # Show failure
                await self._send_message(
                    event_queue=event_queue,
                    task_id=task.task_id,
                    context_id=task.context_id,
                    text=f"{progress} ⚠️  Failed to reach {step.agent_name}",
                )

            task.advance_step()

        # Task complete - send helpful final summary
        task.state = TaskState.completed

        successful = [s for s in task.steps if s.status == TaskState.completed]
        failed = [s for s in task.steps if s.status == TaskState.failed]

        if not failed:
            # All services responded successfully
            services_str = ", ".join(s.agent_name for s in successful)
            final_msg = (
                f"[COMPLETE] Emergency dispatch successful! "
                f"{services_str} {'is' if len(successful) == 1 else 'are'} "
                f"on the way. Help is coming. Please stay safe and wait for "
                f"emergency services to arrive."
            )
        else:
            # Some services failed
            success_str = (
                ", ".join(s.agent_name for s in successful)
                if successful
                else "none"
            )
            fail_str = ", ".join(s.agent_name for s in failed)
            final_msg = (
                f"[COMPLETE] Dispatch completed with issues. "
                f"Successfully contacted: {success_str}. "
                f"Failed to reach: {fail_str}. "
                f"Please remain on the line for further assistance."
            )

        logger.info(
            "Task execution complete: task_id=%s, successful=%d, failed=%d",
            task.task_id,
            len(successful),
            len(failed),
        )

        await self._send_message(
            event_queue=event_queue,
            task_id=task.task_id,
            context_id=task.context_id,
            text=final_msg,
            final=True,
        )

        # Clean up
        if task.task_id in self.active_tasks:
            del self.active_tasks[task.task_id]

    def get_task(self, task_id: str) -> EmergencyTask | None:
        """Retrieve an active task by ID."""
        return self.active_tasks.get(task_id)

