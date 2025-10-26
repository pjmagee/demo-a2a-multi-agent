"""Helpers for proxying CopilotKit requests to A2A agents."""

from __future__ import annotations

from collections import deque
from typing import Annotated, Protocol, TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from webapp_backend.config import Settings, get_settings
from webapp_backend.deps import get_agent_client

if TYPE_CHECKING:
    from collections.abc import Iterator


type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | dict[str, JsonValue] | list[JsonValue]


class SupportsModelDump(Protocol):
    """Protocol describing pydantic models used in responses."""

    def model_dump(self, *, mode: str) -> JsonValue:
        """Serialize the model to JSON-compatible data."""
        ...


class AgentLike(Protocol):
    """Minimal surface needed from agent metadata."""

    name: str | None


class AgentClientLike(Protocol):
    """Client capable of listing agents and sending messages."""

    async def list_agents(self) -> list[AgentLike]:
        """Return available agents."""
        ...

    async def send_message(
        self,
        *,
        agent_name: str,
        message: str,
        context_id: str | None,
    ) -> SupportsModelDump | None:
        """Relay a message to the given agent and return the response."""
        ...

copilot_router = APIRouter(prefix="/copilotkit_remote")

_ACTION_NAME = "send_message_to_agent"


class InfoRequest(BaseModel):
    """Request payload for the remote /info endpoint."""

    properties: dict[str, JsonValue] | None = None
    frontend_url: str | None = Field(default=None, alias="frontendUrl")


class ActionExecutionRequest(BaseModel):
    """Request payload for the remote /actions/execute endpoint."""

    name: str
    arguments: dict[str, JsonValue] = Field(default_factory=dict)
    properties: dict[str, JsonValue] | None = None


def _verify_authorization(request: Request, settings: Settings) -> None:
    """Validate optional bearer token configured for remote access."""
    expected_token: str | None = settings.copilotkit_remote_token
    if not expected_token:
        return

    auth_header = request.headers.get("Authorization", "").strip()
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )

    supplied = auth_header.removeprefix("Bearer ").strip()
    if supplied != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token.",
        )


def _build_action_catalog(agents: list[AgentLike]) -> list[dict[str, object]]:
    """Return the remote action definitions exposed to CopilotKit."""
    agent_names = sorted({card.name for card in agents if card.name})
    if not agent_names:
        return []

    return [
        {
            "name": _ACTION_NAME,
            "description": "Send a text message to one of the available A2A agents.",
            "parameters": [
                {
                    "name": "agent",
                    "type": "string",
                    "description": (
                        "Display name of the target agent as reported in its AgentCard."
                    ),
                    "enum": agent_names,
                },
                {
                    "name": "message",
                    "type": "string",
                    "description": "Plain-text message for the selected agent.",
                },
                {
                    "name": "contextId",
                    "type": "string",
                    "description": (
                        "Optional conversation context to reuse for follow-up "
                        "exchanges."
                    ),
                    "required": False,
                },
            ],
        },
    ]


def _serialize_send_message_response(response: SupportsModelDump | None) -> JsonValue:
    if response is None:
        return None

    try:
        data = response.model_dump(mode="json")
    except AttributeError:  # pragma: no cover - defensive fallback
        return None

    if isinstance(data, dict) and "root" in data:
        root_value = data.get("root")
        return root_value if root_value is not None else data
    return data


def _extract_text_candidates(node: JsonValue) -> Iterator[str]:
    queue: deque[JsonValue] = deque([node])
    while queue:
        current = queue.popleft()
        if isinstance(current, str):
            stripped = current.strip()
            if stripped:
                yield stripped
            continue

        if isinstance(current, dict):
            text_value = current.get("text")
            if isinstance(text_value, str):
                stripped = text_value.strip()
                if stripped:
                    yield stripped

            parts = current.get("parts")
            if isinstance(parts, list):
                queue.extend(part for part in parts if part is not None)

            queue.extend(
                value
                for key in ("result", "message")
                if (value := current.get(key)) is not None
            )
            continue

        if isinstance(current, list):
            queue.extend(item for item in current if item is not None)


def _extract_text_from_payload(payload: JsonValue) -> str | None:
    for text in _extract_text_candidates(payload):
        return text
    return None


def _resolve_context_id(
    *, arguments: dict[str, JsonValue], properties: dict[str, JsonValue] | None,
) -> str | None:
    candidate = arguments.get("contextId")
    if isinstance(candidate, str) and candidate.strip():
        return candidate.strip()

    properties = properties or {}
    for key in ("threadId", "copilotkitThreadId", "copilotkitSessionId"):
        value = properties.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _require_agent(agent_name: str, agents: list[AgentLike]) -> AgentLike:
    for card in agents:
        if card.name == agent_name:
            return card
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Agent '{agent_name}' is not available.",
    )


@copilot_router.post("/info")
async def copilot_info(
    request: Request,
    _payload: InfoRequest,
    client: Annotated[AgentClientLike, Depends(get_agent_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, object]:
    """Return action metadata for the Copilot runtime."""
    _verify_authorization(request, settings)

    agents = await client.list_agents()
    return {
        "version": "1.0",
        "actions": _build_action_catalog(agents),
        "agents": [],
    }


@copilot_router.post("/actions/execute")
async def execute_action(
    request: Request,
    payload: ActionExecutionRequest,
    client: Annotated[AgentClientLike, Depends(get_agent_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, object]:
    """Execute a remote Copilot action against an A2A agent."""
    _verify_authorization(request, settings)

    if payload.name != _ACTION_NAME:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action '{payload.name}' is not registered.",
        )

    agent_name = payload.arguments.get("agent")
    message = payload.arguments.get("message")

    if not isinstance(agent_name, str) or not agent_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Argument 'agent' must be a non-empty string.",
        )

    if not isinstance(message, str) or not message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Argument 'message' must be a non-empty string.",
        )

    agent_name = agent_name.strip()
    message = message.strip()

    agents = await client.list_agents()
    _require_agent(agent_name, agents)

    context_id = _resolve_context_id(
        arguments=payload.arguments,
        properties=payload.properties,
    )
    response = await client.send_message(
        agent_name=agent_name,
        message=message,
        context_id=context_id,
    )

    if response is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Agent '{agent_name}' did not return a response.",
        )

    serialized = _serialize_send_message_response(response)
    text_result = _extract_text_from_payload(serialized)

    return {
        "result": {
            "agent": agent_name,
            "contextId": context_id,
            "text": text_result,
            "raw": serialized,
        },
    }
