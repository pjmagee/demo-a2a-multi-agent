"""Streaming adapter for OpenAI Agent SDK → A2A protocol events.

Converts ``Runner.run_streamed()`` events (``RunItemStreamEvent``) into A2A
protocol events (``TaskStatusUpdateEvent``, ``Message``) that flow through
the A2A event queue.  Tool calls and tool results are emitted using the
a2a-ui metadata convention so the frontend can render collapsible tool-call
accordions.

Metadata convention (from https://github.com/a2anet/a2a-ui):

Tool call::

    Message(
        metadata={"type": "tool-call", "toolCallId": ..., "toolCallName": ...},
        parts=[DataPart(data=<args dict>)],
    )

Tool result::

    Message(
        metadata={"type": "tool-call-result", "toolCallId": ..., "toolCallName": ...},
        parts=[TextPart(text=<result>) | DataPart(data=<result>)],
    )

Usage::

    from shared.openai_streaming import stream_openai_agent

    async def execute(self, context, event_queue):
        with a2a_session(context, ...) as context_id:
            task_id = context.task_id or context_id
            session = get_or_create_session(...)
            result_text = await stream_openai_agent(
                agent=self.agent,
                user_input=context.get_user_input(),
                session=session,
                context_id=context_id,
                task_id=task_id,
                event_queue=event_queue,
            )
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from a2a.server.events.event_queue import EventQueue  # noqa: TC002
from a2a.types import (
    DataPart,
    Message,
    Part,
    Role,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)
from a2a.utils import new_agent_text_message
from agents import Agent, Runner
from agents.items import ToolCallItem, ToolCallOutputItem
from agents.stream_events import RunItemStreamEvent

if TYPE_CHECKING:
    from agents.memory.session import Session

logger: logging.Logger = logging.getLogger(name=__name__)


def _new_message_id() -> str:
    return str(uuid.uuid4())


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _make_tool_call_message(
    tool_call_item: ToolCallItem,
    *,
    context_id: str,
    task_id: str,
) -> Message:
    """Create an A2A Message for a tool call event."""
    raw_item = tool_call_item.raw_item  # ResponseFunctionToolCall or similar
    call_id = getattr(raw_item, "call_id", None) or _new_message_id()
    tool_name = getattr(raw_item, "name", None) or "unknown_tool"
    arguments_str = getattr(raw_item, "arguments", "{}")

    try:
        args_data: dict[str, Any] = json.loads(arguments_str)
    except (json.JSONDecodeError, TypeError):
        args_data = {"raw": arguments_str}

    return Message(
        role=Role.agent,
        message_id=_new_message_id(),
        parts=[Part(root=DataPart(data=args_data))],
        metadata={
            "type": "tool-call",
            "toolCallId": call_id,
            "toolCallName": tool_name,
            "timestamp": _timestamp(),
        },
        task_id=task_id,
        context_id=context_id,
    )


def _make_tool_result_message(
    tool_output_item: ToolCallOutputItem,
    *,
    context_id: str,
    task_id: str,
    tool_names: dict[str, str] | None = None,
) -> Message:
    """Create an A2A Message for a tool call result event."""
    raw_item = tool_output_item.raw_item  # FunctionCallOutput (TypedDict)
    # FunctionCallOutput is a TypedDict so use dict access, not getattr
    if isinstance(raw_item, dict):
        call_id = raw_item.get("call_id") or _new_message_id()
    else:
        call_id = getattr(raw_item, "call_id", None) or _new_message_id()
    # ToolCallOutputItem doesn't carry the function name on raw_item;
    # look it up from the mapping built during tool_called events.
    tool_name = (tool_names or {}).get(call_id, "unknown_tool")
    output = tool_output_item.output

    # Route to TextPart or DataPart based on output type
    if isinstance(output, str):
        try:
            parsed = json.loads(output)
            if isinstance(parsed, dict):
                part = Part(root=DataPart(data=parsed))
            else:
                part = Part(root=TextPart(text=output))
        except (json.JSONDecodeError, TypeError):
            part = Part(root=TextPart(text=output))
    elif isinstance(output, dict):
        part = Part(root=DataPart(data=output))
    else:
        part = Part(root=TextPart(text=str(output)))

    return Message(
        role=Role.agent,
        message_id=_new_message_id(),
        parts=[part],
        metadata={
            "type": "tool-call-result",
            "toolCallId": call_id,
            "toolCallName": tool_name,
            "timestamp": _timestamp(),
        },
        task_id=task_id,
        context_id=context_id,
    )


def _status_update(
    *,
    task_id: str,
    context_id: str,
    state: TaskState,
    message: Message | None = None,
    final: bool = False,
) -> TaskStatusUpdateEvent:
    return TaskStatusUpdateEvent(
        task_id=task_id,
        context_id=context_id,
        status=TaskStatus(
            state=state,
            message=message,
            timestamp=_timestamp(),
        ),
        final=final,
    )


async def stream_openai_agent(  # noqa: PLR0913
    *,
    agent: Agent[None],
    user_input: str,
    session: Session,
    context_id: str,
    task_id: str,
    event_queue: EventQueue,
) -> str:
    """Run an OpenAI Agent SDK agent in streaming mode and emit A2A events.

    Emits tool-call and tool-call-result messages as ``TaskStatusUpdateEvent``
    with the a2a-ui metadata convention.  Returns the final text output.

    Args:
        agent: The OpenAI Agent SDK Agent instance.
        user_input: User's message text.
        session: The session for conversation history.
        context_id: A2A context ID.
        task_id: A2A task ID.
        event_queue: Queue for emitting A2A events.

    Returns:
        The agent's final text output.

    """
    result = Runner.run_streamed(
        starting_agent=agent,
        input=user_input,
        session=session,
    )

    # Track call_id → tool_name so we can label tool results correctly
    # (ToolCallOutputItem.raw_item doesn't carry the function name).
    tool_names: dict[str, str] = {}

    async for event in result.stream_events():
        if not isinstance(event, RunItemStreamEvent):
            continue

        if event.name == "tool_called" and isinstance(
            event.item, ToolCallItem
        ):
            tool_msg = _make_tool_call_message(
                event.item,
                context_id=context_id,
                task_id=task_id,
            )
            # Remember the name for the result event
            meta = tool_msg.metadata or {}
            cid = str(meta.get("toolCallId", ""))
            if cid:
                tool_names[cid] = str(meta.get("toolCallName", ""))

            await event_queue.enqueue_event(
                _status_update(
                    task_id=task_id,
                    context_id=context_id,
                    state=TaskState.working,
                    message=tool_msg,
                ),
            )

        elif event.name == "tool_output" and isinstance(
            event.item, ToolCallOutputItem
        ):
            result_msg = _make_tool_result_message(
                event.item,
                context_id=context_id,
                task_id=task_id,
                tool_names=tool_names,
            )
            await event_queue.enqueue_event(
                _status_update(
                    task_id=task_id,
                    context_id=context_id,
                    state=TaskState.working,
                    message=result_msg,
                ),
            )

    # Extract final output
    final_output: str = result.final_output_as(
        cls=str, raise_if_incorrect_type=True,
    )

    # Emit final text message — the A2A EventConsumer treats Message as
    # a terminal event, so nothing after this will be consumed.
    await event_queue.enqueue_event(
        new_agent_text_message(
            context_id=context_id,
            text=final_output,
            task_id=task_id,
        ),
    )

    return final_output
