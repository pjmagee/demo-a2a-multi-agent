"""FastAPI application for the Group Chat AG-UI backend."""

import json
import logging
import os
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from group_chat_backend.chat_manager import ChatManager
from group_chat_backend.models import AgentDefinition, AgentListResponse, RunAgentInput

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger: logging.Logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", "8050"))
HOST = os.getenv("HOST", "127.0.0.1")

chat_manager = ChatManager()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler."""
    logger.info("Group Chat AG-UI backend starting on %s:%s", HOST, PORT)
    yield
    logger.info("Group Chat AG-UI backend shutting down")


app = FastAPI(title="Group Chat AG-UI Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _sse_event(data: dict[str, object]) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


# --- Agent Management REST API ---


@app.get("/api/agents")
async def list_agents() -> AgentListResponse:
    """List all configured group chat agents."""
    return AgentListResponse(
        agents=[
            AgentDefinition(name=s.name, system_prompt=s.system_prompt)
            for s in chat_manager.agent_specs
        ],
    )


@app.post("/api/agents", status_code=201)
async def add_agent(agent: AgentDefinition) -> AgentDefinition:
    """Add a new agent to the group chat."""
    spec = chat_manager.add_agent(name=agent.name, system_prompt=agent.system_prompt)
    return AgentDefinition(name=spec.name, system_prompt=spec.system_prompt)


@app.delete("/api/agents/{name}", status_code=204)
async def remove_agent(name: str) -> None:
    """Remove an agent from the group chat."""
    chat_manager.remove_agent(name)


# --- AG-UI SSE Endpoint ---


@app.post("/")
async def agui_endpoint(request: Request) -> StreamingResponse:
    """AG-UI protocol SSE endpoint for group chat."""
    body = await request.json()
    run_input = RunAgentInput(**body)

    thread_id = run_input.thread_id or str(uuid.uuid4())
    run_id = run_input.run_id or str(uuid.uuid4())

    # Extract last user message
    user_message = ""
    for msg in reversed(run_input.messages):
        if msg.role == "user":
            user_message = msg.content
            break

    if not user_message:
        user_message = "Hello"

    async def event_stream() -> AsyncIterator[str]:
        ts = int(time.time() * 1000)

        # RUN_STARTED
        yield _sse_event({
            "type": "RUN_STARTED",
            "threadId": thread_id,
            "runId": run_id,
            "timestamp": ts,
        })

        current_agent: str | None = None
        current_message_id: str | None = None

        async for chat_event in chat_manager.run_chat(
            thread_id=thread_id,
            user_message=user_message,
        ):
            ts = int(time.time() * 1000)

            # If agent changed, close previous message and start new one
            if chat_event.agent_name != current_agent:
                if current_message_id is not None:
                    yield _sse_event({
                        "type": "TEXT_MESSAGE_END",
                        "messageId": current_message_id,
                        "timestamp": ts,
                    })

                current_agent = chat_event.agent_name
                current_message_id = f"msg_{uuid.uuid4().hex[:12]}"

                yield _sse_event({
                    "type": "TEXT_MESSAGE_START",
                    "messageId": current_message_id,
                    "role": "assistant",
                    "timestamp": ts,
                })

                # Emit agent name prefix
                yield _sse_event({
                    "type": "TEXT_MESSAGE_CONTENT",
                    "messageId": current_message_id,
                    "delta": f"[{chat_event.agent_name}]: ",
                    "timestamp": ts,
                })

            # Emit text content
            yield _sse_event({
                "type": "TEXT_MESSAGE_CONTENT",
                "messageId": current_message_id,
                "delta": chat_event.text,
                "timestamp": ts,
            })

        # Close final message
        ts = int(time.time() * 1000)
        if current_message_id is not None:
            yield _sse_event({
                "type": "TEXT_MESSAGE_END",
                "messageId": current_message_id,
                "timestamp": ts,
            })

        # RUN_FINISHED
        yield _sse_event({
            "type": "RUN_FINISHED",
            "threadId": thread_id,
            "runId": run_id,
            "timestamp": ts,
        })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def run() -> None:
    """Run the application."""
    uvicorn.run(
        app="group_chat_backend.app:app",
        host=HOST,
        port=PORT,
        reload=False,
    )


if __name__ == "__main__":
    run()
