"""Backend-for-frontend HTTP routes.

SSE Streaming Contract (transparent pass-through):
--------------------------------------------------
We iterate the A2A streaming generator and unwrap envelopes whose ``root`` is a
``SendStreamingMessageSuccessResponse`` or ``JSONRPCErrorResponse``.

For each success response we emit an ``event:stream`` frame with:

    {
        "a2a_type": <underlying result class name>,
        "raw": <model_dump(exclude_none=True) or shallow public attrs>,
        "text": <best-effort text content>,
        "context_id": <context id if present>
    }

If we encounter ``JSONRPCErrorResponse`` we emit a single ``event:error`` frame
with its message and stop.

If a streamed object is not an envelope (or has no ``root``) but is not an error
we still forward it as ``event:stream`` with shallow serialization so callers
see everything (no silent filtering).

When iteration completes we emit ``event:done`` including a count of *stream*
frames and the last observed ``context_id``.
"""
from __future__ import annotations

# Standard library
import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Annotated, TYPE_CHECKING, Any, cast

# Third-party
from a2a.types import (
    AgentCard,
    Artifact,
    FilePart,
    FileWithBytes,
    FileWithUri,
    JSONRPCErrorResponse,
    Message as A2AMessage,
    Part,
    SendStreamingMessageSuccessResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    TextPart,
)
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Local application imports
from webapp_backend.auth import require_auth
from webapp_backend.clients.a2a_client import A2AAgentClient
from webapp_backend.deps import get_agent_client

if TYPE_CHECKING:  # Runtime avoidance for heavier modules
    from collections.abc import AsyncGenerator
    from webapp_backend.schemas.messages import SendMessagePayload

router = APIRouter(prefix="/api")
AgentClientDependency = Annotated[A2AAgentClient, Depends(get_agent_client)]

logger = logging.getLogger(__name__)

def _shallow_dump(obj: object) -> dict[str, Any]:
    if obj is None:
        return {}
    if hasattr(obj, "model_dump"):
        try:
            dumped = obj.model_dump(exclude_none=True)  # type: ignore[call-arg]
            if isinstance(dumped, dict):
                return dumped  # type: ignore[return-value]
        except Exception as exc:  # noqa: BLE001
            logging.getLogger("webapp_backend.api.sse").debug(
                "model_dump failed type=%s exc=%s", type(obj).__name__, exc,
            )
    data: dict[str, Any] = {}
    for name in dir(obj):
        if name.startswith("_"):
            continue
        try:
            value = getattr(obj, name)
        except Exception as exc:  # noqa: BLE001
            logging.getLogger("webapp_backend.api.sse").debug(
                "attr access failed name=%s exc=%s", name, exc,
            )
            continue
        if callable(value):
            continue
        data[name] = value
    return data


async def _sse_stream(
    client: A2AAgentClient,
    agent: str,
    message: str,
    context_id: str | None,
    *,
    raw_envelope: bool,
) -> AsyncGenerator[str]:
    """Stream raw A2A results as SSE frames.

    Emitted frames:
      event:stream -> data: <JSON of underlying result.model_dump(exclude_none=True)>
      event:error  -> data: {"error": <string>}
      event:done   -> data: {"status":"done","count":<int>,"context_id":<str|null>}

    If ``raw_envelope`` is True and the outer envelope has a ``root`` attribute,
    an additional key ``_envelope`` is included with shallow serialized envelope.
    No other transformation is performed.
    """
    count = 0
    last_context_id: str | None = context_id
    log = logging.getLogger("webapp_backend.api.sse")
    log.debug(
        "SSE stream start agent=%s context_id=%s", agent, context_id,
    )
    async for envelope in client.send_message_streaming(
        agent_name=agent,
        message=message,
        context_id=context_id,
    ):
        # Unwrap 'root' if present (pattern used by A2A send_message_streaming)
        root = getattr(envelope, "root", envelope)
        log.debug(
            "Envelope received type=%s root_type=%s count=%s",
            type(envelope).__name__,
            type(root).__name__,
            count,
        )

        # Error envelope
        if isinstance(root, JSONRPCErrorResponse):
            err_msg = getattr(root, "message", None)
            if not isinstance(err_msg, str):
                err_msg = "stream error"
            log.debug(
                "SSE stream error agent=%s context_id=%s msg=%s after_count=%s",
                agent,
                last_context_id,
                err_msg,
                count,
            )
            yield (
                "event:error\n"
                "data:" + json.dumps({"error": err_msg}, ensure_ascii=False) + "\n\n"
            )
            return

        # Success streaming response
        if isinstance(root, SendStreamingMessageSuccessResponse):
            result = root.result
            last_context_id = getattr(result, "context_id", last_context_id)
            payload = _shallow_dump(result)
            if raw_envelope:
                payload["_envelope"] = _shallow_dump(root)
            count += 1
            log.debug(
                "Stream success event agent=%s context_id=%s type=%s count=%s",
                agent,
                last_context_id,
                type(result).__name__,
                count,
            )
            yield (
                "event:stream\n"
                "data:" + json.dumps(payload, ensure_ascii=False) + "\n\n"
            )
            continue

        # Fallback: unknown object (still stream for transparency)
        last_context_id = getattr(root, "context_id", last_context_id)
        payload = _shallow_dump(root)
        if raw_envelope and getattr(envelope, "root", None) is not None:
            payload["_envelope"] = _shallow_dump(envelope)
        count += 1
        log.debug(
            "Fallback stream event agent=%s context_id=%s type=%s count=%s",
            agent,
            last_context_id,
            type(root).__name__,
            count,
        )
        yield (
            "event:stream\n"
            "data:" + json.dumps(payload, ensure_ascii=False) + "\n\n"
        )

    # Completion frame
    done_payload = {"status": "done", "count": count, "context_id": last_context_id}
    log.debug(
        "SSE stream done agent=%s final_context_id=%s total_events=%s",
        agent,
        last_context_id,
        count,
    )
    yield ("event:done\ndata:" + json.dumps(done_payload, ensure_ascii=False) + "\n\n")


def _build_streaming_response(
    *,
    client: A2AAgentClient,
    agent: str,
    message: str,
    context_id: str | None,
    raw_envelope: bool,
) -> StreamingResponse:
    return StreamingResponse(
        content=_sse_stream(
            client=client,
            agent=agent,
            message=message,
            context_id=context_id,
            raw_envelope=raw_envelope,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/agents", response_model=list[AgentCard])
async def list_agents(
    client: AgentClientDependency,
    _authorized: Annotated[None, Depends(require_auth)],
) -> list[AgentCard]:
    """Return metadata for all configured agents."""
    logger.info("GET /api/agents - fetching agent list")
    cards = await client.list_agents()
    logger.info("GET /api/agents - returning %d agents", len(cards))
    return cards



@router.post("/messages/stream")
async def stream_message(
    payload: SendMessagePayload,
    request: Request,
    client: AgentClientDependency,
    _authorized: Annotated[None, Depends(require_auth)],
) -> StreamingResponse:
    """POST streaming endpoint (SSE)."""
    if "text/event-stream" not in request.headers.get("accept", ""):
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Endpoint requires Accept: text/event-stream",
        )
    raw_envelope = request.query_params.get("raw_envelope") == "true"
    return _build_streaming_response(
        client=client,
        agent=payload.agent_name,
        message=payload.message,
        context_id=payload.context_id,
        raw_envelope=raw_envelope,
    )


@router.get("/messages/stream")
async def stream_message_get(
    agent_name: Annotated[str, Query(description="Target agent name")],
    message: Annotated[str, Query(description="User message text")],
    request: Request,
    client: AgentClientDependency,
    _authorized: Annotated[None, Depends(require_auth)],
    context_id: Annotated[
        str | None,
        Query(description="Conversation context id"),
    ] = None,
) -> StreamingResponse:
    """GET streaming endpoint (SSE)."""
    if "text/event-stream" not in request.headers.get("accept", ""):
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Endpoint requires Accept: text/event-stream",
        )
    raw_envelope = request.query_params.get("raw_envelope") == "true"
    return _build_streaming_response(
        client=client,
        agent=agent_name,
        message=message,
        context_id=context_id,
        raw_envelope=raw_envelope,
    )


# ---------------- Assistant-UI Data Stream style endpoint -----------------
# The assistant-ui DataStream protocol expects a POST endpoint that accepts:
#   { messages, tools?, system? }
# We adapt the last user message into our A2A streaming exchange and emit SSE
# frames shaped similarly to the Data Stream protocol so the frontend could
# switch to useDataStreamRuntime if desired.
# For now we keep LocalRuntime in the frontend; this endpoint provides a
# standardized contract for future migration.

class DataStreamChatPayload(BaseModel):
    """Request schema for /api/chat streaming endpoint used by assistant-ui.

    Only the last user message's text content is forwarded to the selected agent.
    The agent must be explicitly provided (no implicit default) so the UI can
    focus the conversation thread.
    """

    messages: list[dict[str, object]]
    agent_name: str  # explicit selection required
    system: str | None = None
    context_id: str | None = None


def _extract_user_text(messages: list[dict[str, object]]) -> str:
    """Return concatenated text of the most recent user message."""
    for item in reversed(messages):
        if item.get("role") != "user":
            continue
        content = item.get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            content_list = cast("list[object]", content)
            parts: list[dict[str, object]] = [
                cast("dict[str, object]", p)
                for p in content_list
                if isinstance(p, dict)
            ]
            texts: list[str] = [
                str(p.get("text"))
                for p in parts
                if p.get("type") == "text" and isinstance(p.get("text"), str)
            ]
            if texts:
                return "".join(texts)
        return ""
    return ""


def _parse_data_uri(data_uri: str) -> tuple[str, str]:
    """Return (mime_type, base64_data) from a data URI string."""
    # Format: data:<mime>;base64,<b64>
    header, _, b64 = data_uri.partition(";base64,")
    mime = header.removeprefix("data:")
    return mime, b64


def _content_item_to_part(p: dict[str, object]) -> Part | None:
    """Convert a single assistant-ui content item to an A2A Part."""
    ptype = p.get("type")
    if ptype == "text" and isinstance(p.get("text"), str):
        return Part(root=TextPart(kind="text", text=str(p["text"])))
    if ptype == "image":
        data_uri = p.get("image", "")
        if isinstance(data_uri, str) and data_uri.startswith("data:"):
            mime, b64 = _parse_data_uri(data_uri)
            return Part(
                root=FilePart(
                    kind="file",
                    file=FileWithBytes(
                        bytes=b64,
                        mime_type=mime or None,
                        name=str(p["filename"]) if p.get("filename") else None,
                    ),
                ),
            )
    if ptype == "file":
        b64 = p.get("data", "")
        mime = p.get("mimeType", "")
        if isinstance(b64, str) and b64:
            if b64.startswith("data:"):
                mime, b64 = _parse_data_uri(b64)
            return Part(
                root=FilePart(
                    kind="file",
                    file=FileWithBytes(
                        bytes=b64,
                        mime_type=str(mime) if mime else None,
                        name=str(p["filename"]) if p.get("filename") else None,
                    ),
                ),
            )
    return None


def _extract_user_parts(messages: list[dict[str, object]]) -> list[Part]:
    """Extract text and file parts from the most recent user message.

    Handles content and attachment content shapes produced by assistant-ui:
      - ``{type: "text", text: "..."}``
      - ``{type: "image", image: "data:image/...;base64,..."}``
      - ``{type: "file", data: "<base64>", mimeType: "...", filename: "..."}``
    """
    for item in reversed(messages):
        if item.get("role") != "user":
            continue
        content = item.get("content", "")
        if isinstance(content, str):
            return [Part(root=TextPart(kind="text", text=content))]
        a2a_parts: list[Part] = []
        if isinstance(content, list):
            for raw in content:
                if isinstance(raw, dict):
                    part = _content_item_to_part(cast("dict[str, object]", raw))
                    if part is not None:
                        a2a_parts.append(part)
        # Also process attachment content (e.g. inlined text from SimpleTextAttachmentAdapter)
        attachments = item.get("attachments")
        if isinstance(attachments, list):
            for att in attachments:
                if not isinstance(att, dict):
                    continue
                att_content = cast("dict[str, object]", att).get("content")
                if isinstance(att_content, list):
                    for raw_att in att_content:
                        if isinstance(raw_att, dict):
                            part = _content_item_to_part(
                                cast("dict[str, object]", raw_att),
                            )
                            if part is not None:
                                a2a_parts.append(part)
        return a2a_parts
    return []

def _chat_accept_error_frames() -> list[str]:
    header_error = {"error": "Endpoint requires Accept: text/event-stream"}
    return [
        "event:error\n" + "data:" + json.dumps(header_error) + "\n\n",
        "event:done\n" + "data:" + json.dumps({"status": "done"}) + "\n\n",
    ]

def _chat_agent_not_found_frames(agent_name: str) -> list[str]:
    not_found_error = {"error": f"Unknown agent '{agent_name}'"}
    return [
        "event:error\n" + "data:" + json.dumps(not_found_error) + "\n\n",
        "event:done\n" + "data:" + json.dumps({"status": "done"}) + "\n\n",
    ]

def _format_message_start(agent_name: str, mid: str, ctx: str | None) -> str:
    return (
        "event:message-start\n"
        "data:" + json.dumps(
            {
                "id": mid,
                "role": "assistant",
                "agent_name": agent_name,
                "context_id": ctx,
            },
            ensure_ascii=False,
        ) + "\n\n"
    )

def _format_message_delta(mid: str, chunk: str) -> str:
    return (
        "event:message-delta\n"
        "data:" + json.dumps(
            {"id": mid, "delta": {"text": chunk}}, ensure_ascii=False,
        ) + "\n\n"
    )

def _format_message_complete(
    agent_name: str,
    mid: str,
    ctx: str | None,
    content_parts: list[dict[str, object]],
) -> str:
    # Consolidate consecutive text parts into a single part so the frontend
    # renders one markdown block instead of many separate lines.
    merged: list[dict[str, object]] = []
    text_buf: list[str] = []
    for part in content_parts:
        if part.get("type") == "text":
            text_buf.append(str(part.get("text", "")))
        else:
            if text_buf:
                merged.append({"type": "text", "text": "".join(text_buf)})
                text_buf.clear()
            merged.append(part)
    if text_buf:
        merged.append({"type": "text", "text": "".join(text_buf)})
    if not merged:
        merged = [{"type": "text", "text": ""}]
    return (
        "event:message-complete\n"
        "data:" + json.dumps(
            {
                "id": mid,
                "role": "assistant",
                "agent_name": agent_name,
                "content": merged,
                "context_id": ctx,
            },
            ensure_ascii=False,
        ) + "\n\n"
    )

def _format_error(err_msg: str) -> str:
    return "event:error\n" + "data:" + json.dumps({"error": err_msg}) + "\n\n"

def _format_done(agent_name: str, ctx: str | None) -> str:
    return (
        "event:done\n"
        "data:" + json.dumps(
            {"status": "done", "agent_name": agent_name, "context_id": ctx},
            ensure_ascii=False,
        ) + "\n\n"
    )


@router.get("/agents/{agent_name}", response_model=AgentCard)
async def get_agent(
    agent_name: str,
    client: AgentClientDependency,
    _authorized: Annotated[None, Depends(require_auth)],
) -> AgentCard:
    """Return a single agent card by name (404 if not found)."""
    agents = await client.list_agents()
    for card in agents:
        if getattr(card, "name", None) == agent_name:
            return card
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")


def _validate_agent_exists(agent_name: str, agents: list[AgentCard]) -> bool:
    return any(getattr(a, "name", None) == agent_name for a in agents)


@dataclass
class _StreamState:
    started: bool
    message_id: str | None
    accumulated_text: list[str]
    content_parts: list[dict[str, object]]
    context_id: str | None


def _format_status_update(event: TaskStatusUpdateEvent) -> str:
    payload: dict[str, object] = {
        "task_id": event.task_id,
        "state": event.status.state.value,
        "final": event.final,
    }
    if event.status.timestamp:
        payload["timestamp"] = event.status.timestamp
    return (
        "event:status-update\n"
        "data:" + json.dumps(payload, ensure_ascii=False) + "\n\n"
    )


def _format_file_part(mid: str, file_part: FilePart) -> str:
    file_obj = file_part.file
    payload: dict[str, object] = {"id": mid}
    if isinstance(file_obj, FileWithBytes):
        payload.update({
            "type": "file",
            "name": file_obj.name,
            "mimeType": file_obj.mime_type or "application/octet-stream",
            "data": file_obj.bytes,
        })
    elif isinstance(file_obj, FileWithUri):
        payload.update({
            "type": "file_uri",
            "name": file_obj.name,
            "mimeType": file_obj.mime_type,
            "uri": file_obj.uri,
        })
    return (
        "event:file-part\n"
        "data:" + json.dumps(payload, ensure_ascii=False) + "\n\n"
    )


def _format_artifact_update(mid: str, artifact: Artifact) -> str:
    payload: dict[str, object] = {
        "id": mid,
        "artifact_id": artifact.artifact_id,
        "name": artifact.name,
        "description": artifact.description,
    }
    return (
        "event:artifact-update\n"
        "data:" + json.dumps(payload, ensure_ascii=False) + "\n\n"
    )


def _process_parts(
    parts: list[Part],
    state: _StreamState,
) -> list[str]:
    """Process A2A Part list into SSE frames, accumulating state."""
    frames: list[str] = []
    mid = state.message_id or "msg"
    for part in parts:
        part_root = getattr(part, "root", None)
        if isinstance(part_root, TextPart) and part_root.text:
            state.accumulated_text.append(part_root.text)
            state.content_parts.append({"type": "text", "text": part_root.text})
            frames.append(_format_message_delta(mid, part_root.text))
        elif isinstance(part_root, FilePart):
            file_obj = part_root.file
            if isinstance(file_obj, FileWithBytes):
                state.content_parts.append({
                    "type": "file",
                    "data": file_obj.bytes,
                    "mimeType": file_obj.mime_type or "application/octet-stream",
                    "filename": file_obj.name,
                })
            elif isinstance(file_obj, FileWithUri):
                state.content_parts.append({
                    "type": "source",
                    "sourceType": "url",
                    "id": file_obj.name or file_obj.uri,
                    "url": file_obj.uri,
                    "title": file_obj.name,
                })
            frames.append(_format_file_part(mid, part_root))
    return frames


async def _stream_agent_reply(
    *,
    client: A2AAgentClient,
    agent_name: str,
    user_text: str,
    context_id: str | None,
    request: Request,
    parts: list[Part] | None = None,
) -> AsyncGenerator[str]:
    """Core streaming logic producing incremental frames.

    Dispatches on A2A result types:
    - Message: text/file parts forwarded as message-delta / file-part
    - TaskStatusUpdateEvent: emitted as status-update, message parts forwarded
    - TaskArtifactUpdateEvent: artifact metadata + parts forwarded
    - Task: logged only
    """
    state = _StreamState(
        started=False,
        message_id=None,
        accumulated_text=[],
        content_parts=[],
        context_id=context_id,
    )
    final_context_id: str | None = context_id
    log = logging.getLogger("webapp_backend.api.sse")

    def _ensure_started() -> list[str]:
        if state.started:
            return []
        state.message_id = state.message_id or "msg"
        state.started = True
        return [_format_message_start(agent_name, state.message_id, state.context_id)]

    try:
        async for envelope in client.send_message_streaming(
            agent_name=agent_name,
            message=user_text,
            context_id=context_id,
            parts=parts,
        ):
            if await request.is_disconnected():
                log.info(
                    "Client disconnected mid-stream agent=%s context=%s",
                    agent_name,
                    final_context_id,
                )
                break
            root = getattr(envelope, "root", envelope)
            if isinstance(root, JSONRPCErrorResponse):
                err_msg = getattr(root, "message", "stream error")
                log.info(
                    "Error from agent early termination agent=%s msg=%s",
                    agent_name,
                    err_msg,
                )
                yield _format_error(err_msg)
                break
            if not isinstance(root, SendStreamingMessageSuccessResponse):
                continue

            result = root.result
            final_context_id = getattr(result, "context_id", final_context_id)
            state.context_id = final_context_id

            if isinstance(result, A2AMessage):
                state.message_id = state.message_id or result.message_id
                for f in _ensure_started():
                    yield f
                for f in _process_parts(result.parts, state):
                    yield f

            elif isinstance(result, TaskStatusUpdateEvent):
                yield _format_status_update(result)
                if result.status.message:
                    state.message_id = (
                        state.message_id or result.status.message.message_id
                    )
                    for f in _ensure_started():
                        yield f
                    for f in _process_parts(result.status.message.parts, state):
                        yield f

            elif isinstance(result, TaskArtifactUpdateEvent):
                for f in _ensure_started():
                    yield f
                mid = state.message_id or "msg"
                yield _format_artifact_update(mid, result.artifact)
                for f in _process_parts(result.artifact.parts, state):
                    yield f

            elif isinstance(result, Task):
                log.debug("Task object received task_id=%s", result.id)

    except asyncio.CancelledError:
        log.info(
            "Streaming coroutine cancelled (likely client abort) agent=%s context=%s",
            agent_name,
            final_context_id,
        )
        raise
    if state.started and state.message_id is not None:
        yield _format_message_complete(
            agent_name,
            state.message_id,
            final_context_id,
            state.content_parts,
        )
    yield _format_done(agent_name, final_context_id)


@router.post("/chat", response_model=None)
async def data_stream_chat(
    payload: DataStreamChatPayload,
    request: Request,
    client: AgentClientDependency,
    _authorized: Annotated[None, Depends(require_auth)],
) -> StreamingResponse:
    """Assistant-UI compatible data stream chat endpoint.

    Emits incremental frames: message-start, message-delta, message-complete,
    error, done.
    """
    if "text/event-stream" not in request.headers.get("accept", ""):
        return StreamingResponse(
            content=iter(_chat_accept_error_frames()),
            media_type="text/event-stream",
        )
    agent_name = payload.agent_name
    agents = await client.list_agents()
    if not _validate_agent_exists(agent_name, agents):
        return StreamingResponse(
            content=iter(_chat_agent_not_found_frames(agent_name)),
            media_type="text/event-stream",
        )
    user_text = _extract_user_text(payload.messages)
    user_parts = _extract_user_parts(payload.messages)
    return StreamingResponse(
        content=_stream_agent_reply(
            client=client,
            agent_name=agent_name,
            user_text=user_text,
            context_id=payload.context_id,
            request=request,
            parts=user_parts or None,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
