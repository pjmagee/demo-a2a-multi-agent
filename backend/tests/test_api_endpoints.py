"""Backend API endpoint tests for agent listing and chat streaming.

These tests focus on the new assistant-ui oriented endpoints plus existing
listing routes. They exercise:

1. GET /api/agents returns a list of AgentCard objects.
2. GET /api/agents/{agent_name} returns 404 for unknown agent.
3. POST /api/chat requires Accept: text/event-stream (406 fallback via error frame behavior).
4. POST /api/chat streams at least one message event and a done event when agent exists.
5. POST /api/chat yields an error + done when agent is unknown.

Assertions are intentional (test semantic); ruff rule S101 is suppressed for
this file. Docstring rules are globally ignored by project config. Remaining
style adjustments align with repository conventions.
"""  # ruff: noqa: S101, E501

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from fastapi import FastAPI
from webapp_backend.app import create_app
from webapp_backend.clients.a2a_client import A2AAgentClient
from webapp_backend.deps import get_agent_client  # noqa: F401 (imported for monkeypatch attribute path)
from a2a.types import (
    AgentCard,
    Capabilities,
    AgentCardSkills,
    ToolSummary,
    SendStreamingMessageResponse,
    SendStreamingMessageSuccessResponse,
    Message,
    Role,
    Part,
    TextPart,
)


HTTP_OK = 200
HTTP_NOT_FOUND = 404


class DummyStreamingClient(A2AAgentClient):
    """Dummy client overriding network behavior for tests."""

    def __init__(self) -> None:  # type: ignore[override]
        """Initialize dummy client with a single placeholder address."""
        self._addresses = ("dummy",)

    async def list_agents(self) -> list[AgentCard]:  # type: ignore[override]
        """Return a fixed list containing one streaming-capable agent."""
        return [
            AgentCard(
                name="alpha",
                description="Alpha test agent",
                version="0.0.1",
                capabilities=Capabilities(streaming=True),
                skills=AgentCardSkills(
                    skills=[ToolSummary(name="echo", description="Echo tool")],
                ),
            ),
        ]

    async def send_message_streaming(
        self,
        agent_name: str,
        message: str,
        context_id: str | None = None,
    ) -> AsyncGenerator[SendStreamingMessageResponse]:  # type: ignore[override]
        """Yield a single synthetic streaming message for the alpha agent."""
        if agent_name != "alpha":
            # Simulate no events (unknown agent would be trapped earlier)
            if False:  # pragma: no cover
                yield  # type: ignore[misc]
            return

        # Single synthetic message event then stop
        msg = Message(
            context_id=context_id,
            role=Role.agent,
            message_id="m1",
            parts=[Part(root=TextPart(kind="text", text=f"Echo: {message}"))],
        )
        yield SendStreamingMessageResponse(
            root=SendStreamingMessageSuccessResponse(
                id="id1",
                jsonrpc="2.0",
                result=msg,
            ),
        )


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    """Create test app and monkeypatch agent client dependency."""
    app = create_app()

    # Override dependency injection for A2AAgentClient
    async def _dummy_client() -> A2AAgentClient:
        return DummyStreamingClient()

    monkeypatch.setattr("webapp_backend.deps.get_agent_client", _dummy_client)
    return app


@pytest.fixture
def client(app) -> TestClient:  # noqa: ANN001 - FastAPI TestClient fixture pattern
    return TestClient(app)


def _auth_headers() -> dict[str, str]:
    # Minimal auth header to satisfy require_auth dependency (stubbed logic)
    return {"Authorization": "Bearer test-token"}


def test_list_agents(client: TestClient) -> None:
    resp = client.get("/api/agents", headers=_auth_headers())
    assert resp.status_code == HTTP_OK
    data = resp.json()
    assert isinstance(data, list)
    assert data
    assert data[0]["name"] == "alpha"


def test_get_unknown_agent_404(client: TestClient) -> None:
    resp = client.get("/api/agents/does-not-exist", headers=_auth_headers())
    assert resp.status_code == HTTP_NOT_FOUND
    body = resp.json()
    assert body["detail"] == "Agent not found"


def test_chat_unknown_agent_stream_frames(client: TestClient) -> None:
    # Expect error + done frames via SSE (we collect raw text)
    payload = {
        "messages": [{"role": "user", "content": "Hi"}],
        "agent_name": "does-not-exist",
    }
    resp = client.post(
        "/api/chat",
        json=payload,
        headers={"Accept": "text/event-stream", **_auth_headers()},
    )
    assert resp.status_code == HTTP_OK
    text = resp.text
    assert "event:error" in text
    assert "Unknown agent" in text
    assert "event:done" in text


def test_chat_requires_accept_header(client: TestClient) -> None:
    """Ensure endpoint generates error frames when Accept header missing."""
    payload = {"messages": [{"role": "user", "content": "Hi"}], "agent_name": "alpha"}
    resp = client.post("/api/chat", json=payload, headers=_auth_headers())
    # Endpoint returns SSE with error frames (still HTTP 200) because of custom behavior
    assert resp.status_code == HTTP_OK
    assert "event:error" in resp.text
    assert "Accept: text/event-stream" in resp.text


def test_chat_success_streams_message_and_done(client: TestClient) -> None:
    """Verify successful chat produces message and done SSE frames."""
    payload = {
        "messages": [{"role": "user", "content": "Hello"}],
        "agent_name": "alpha",
    }
    resp = client.post(
        "/api/chat",
        json=payload,
        headers={"Accept": "text/event-stream", **_auth_headers()},
    )
    assert resp.status_code == HTTP_OK
    body = resp.text
    # Should contain at least one message event and a done event.
    assert "event:message" in body
    assert "Echo: Hello" in body
    assert "event:done" in body
