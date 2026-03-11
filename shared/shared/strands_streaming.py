"""Streaming adapter for Strands Agent SDK → A2A protocol events.

Converts ``Agent.stream_async()`` events into A2A protocol events
(``TaskStatusUpdateEvent``, ``Message``) that flow through the A2A event
queue.  Tool calls and tool results are emitted using the a2a-ui metadata
convention.

Usage::

    from shared.strands_streaming import stream_strands_agent

    async def execute(self, context, event_queue):
        with a2a_session(context, ...) as context_id:
            task_id = context.task_id or context_id
            result_text = await stream_strands_agent(
                agent=self.agent,
                user_input=context.get_user_input(),
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

if TYPE_CHECKING:
    from strands import Agent

logger: logging.Logger = logging.getLogger(name=__name__)


def _new_message_id() -> str:
    return str(uuid.uuid4())


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _make_tool_use_message(
    tool_use: dict[str, Any],
    *,
    context_id: str,
    task_id: str,
) -> Message:
    """Create an A2A Message for a Strands tool_use event."""
    call_id = tool_use.get("toolUseId", _new_message_id())
    tool_name = tool_use.get("name", "unknown_tool")
    args_data = tool_use.get("input", {})

    if not isinstance(args_data, dict):
        args_data = {"raw": str(args_data)}

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
    tool_result: dict[str, Any],
    *,
    context_id: str,
    task_id: str,
    tool_names: dict[str, str] | None = None,
) -> Message:
    """Create an A2A Message for a Strands tool_result event."""
    call_id = tool_result.get("toolUseId", _new_message_id())
    content_list = tool_result.get("content", [])

    # Strands ToolResult.content is a list of ToolResultContent dicts
    text_parts: list[str] = [
        str(item["text"])
        for item in content_list
        if isinstance(item, dict) and "text" in item
    ]

    output = "\n".join(text_parts) if text_parts else str(content_list)

    # Try to parse as JSON dict for DataPart
    try:
        parsed = json.loads(output)
        if isinstance(parsed, dict):
            part = Part(root=DataPart(data=parsed))
        else:
            part = Part(root=TextPart(text=output))
    except (json.JSONDecodeError, TypeError):
        part = Part(root=TextPart(text=output))

    return Message(
        role=Role.agent,
        message_id=_new_message_id(),
        parts=[part],
        metadata={
            "type": "tool-call-result",
            "toolCallId": call_id,
            "toolCallName": (tool_names or {}).get(call_id, "tool_result"),
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


async def stream_strands_agent(
    *,
    agent: Agent,
    user_input: str,
    context_id: str,
    task_id: str,
    event_queue: EventQueue,
) -> str:
    """Run a Strands agent in streaming mode and emit A2A events.

    Emits tool-call and tool-call-result messages as ``TaskStatusUpdateEvent``
    with the a2a-ui metadata convention.  Returns the final text output.
    """
    accumulated_text = ""
    emitted_tool_uses: set[str] = set()
    tool_names: dict[str, str] = {}

    async for event in agent.stream_async(user_input):
        # Strands events are dicts with various keys
        if not isinstance(event, dict):
            continue

        # Text chunk
        if "data" in event:
            accumulated_text += str(event["data"])

        # Tool use started
        current_tool = event.get("current_tool_use")
        if isinstance(current_tool, dict) and "toolUseId" in current_tool:
            tool_id = current_tool["toolUseId"]
            if tool_id not in emitted_tool_uses:
                emitted_tool_uses.add(tool_id)
                tool_name = current_tool.get("name", "")
                if tool_name:
                    tool_names[tool_id] = tool_name
                tool_msg = _make_tool_use_message(
                    current_tool,
                    context_id=context_id,
                    task_id=task_id,
                )
                logger.info(
                    "Strands tool call: %s (call_id=%s)",
                    current_tool.get("name", "?"),
                    tool_id,
                )
                await event_queue.enqueue_event(
                    _status_update(
                        task_id=task_id,
                        context_id=context_id,
                        state=TaskState.working,
                        message=tool_msg,
                    ),
                )

        # Tool results — ToolResultMessageEvent carries message.content
        # with [{"toolResult": {"toolUseId": ..., "content": [...], "status": ...}}, ...]
        tool_result_msg = event.get("message")
        if (
            isinstance(tool_result_msg, dict)
            and tool_result_msg.get("role") == "user"
        ):
            for item in tool_result_msg.get("content", []):
                if not isinstance(item, dict):
                    continue
                tr = item.get("toolResult")
                if not isinstance(tr, dict):
                    continue
                result_msg = _make_tool_result_message(
                    tr,
                    context_id=context_id,
                    task_id=task_id,
                    tool_names=tool_names,
                )
                logger.info(
                    "Strands tool result: %s (call_id=%s)",
                    tool_names.get(tr.get("toolUseId", ""), "?"),
                    tr.get("toolUseId", "?"),
                )
                await event_queue.enqueue_event(
                    _status_update(
                        task_id=task_id,
                        context_id=context_id,
                        state=TaskState.working,
                        message=result_msg,
                    ),
                )

    # Emit final text message — the A2A EventConsumer treats Message as
    # a terminal event, so nothing after this will be consumed.
    final_text = accumulated_text.strip() or "[no response]"
    await event_queue.enqueue_event(
        new_agent_text_message(
            context_id=context_id,
            text=final_text,
            task_id=task_id,
        ),
    )

    return final_text
