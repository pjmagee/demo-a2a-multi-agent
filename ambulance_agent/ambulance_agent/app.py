"""Application entry point for the Ambulance agent."""

import os

import uvicorn
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.events import InMemoryQueueManager
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.types import AgentCard
from fastapi import FastAPI

from ambulance_agent.agent_card import build_agent_card
from ambulance_agent.executor import AmbulanceAgentExecutor

PORT = int(os.getenv(key="PORT", default="8014"))
BASE_URL: str = os.getenv(key="BASE_URL", default=f"http://localhost:{PORT}")


def _create_application() -> FastAPI:
    card: AgentCard = build_agent_card(base_url=BASE_URL)
    executor = AmbulanceAgentExecutor()
    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
        push_sender=None,
        queue_manager=InMemoryQueueManager(),
    )
    app = A2AFastAPIApplication(
        agent_card=card,
        http_handler=handler,
        extended_agent_card=None,
        card_modifier=None,
        context_builder=None,
        extended_card_modifier=None,
    )
    api: FastAPI = app.build()
    return api


app: FastAPI = _create_application()

def run() -> None:    
    """Run the application."""
    uvicorn.run(app="ambulance_agent.app:app", host="0.0.0.0", port=PORT, reload=False)


if __name__ == "__main__":
    run()
