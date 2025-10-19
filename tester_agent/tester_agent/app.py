"""FastAPI application for the Tester agent."""

import os

import uvicorn
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.events import InMemoryQueueManager
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.types import AgentCard
from fastapi import FastAPI

from tester_agent.agent_card import build_agent_card
from tester_agent.executor import TesterAgentExecutor

PORT = int(os.getenv(key="PORT", default="8017"))
BASE_URL: str = os.getenv(key="BASE_URL", default=f"http://localhost:{PORT}")


def _create_application() -> FastAPI:

    agent_card: AgentCard = build_agent_card(base_url=BASE_URL)
    request_handler = DefaultRequestHandler(
        agent_executor=TesterAgentExecutor(),
        task_store=InMemoryTaskStore(),
        push_sender=None,
        queue_manager=InMemoryQueueManager(),
    )
    server = A2AFastAPIApplication(
        agent_card=agent_card,
        http_handler=request_handler,
        extended_agent_card=None,
        card_modifier=None,
        context_builder=None,
        extended_card_modifier=None,
    )
    fast_api: FastAPI = server.build()
    return fast_api

app: FastAPI = _create_application()


def run() -> None:
    """Run the FastAPI application."""
    uvicorn.run(app="tester_agent.app:app", host="0.0.0.0", port=PORT, reload=False)


if __name__ == "__main__":
    run()
