"""Application entry point for the Mi5 Agent."""

import os

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.events import InMemoryQueueManager
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
import uvicorn
from fastapi import FastAPI

from mi5_agent.agent_card import build_agent_card
from mi5_agent.executor import Mi5AgentExector
from shared import configure_logging

PORT = int(os.getenv(key="PORT", default="8013"))
HOST: str = os.getenv(key="HOST", default="127.0.0.1")
BASE_URL = os.getenv(key="BASE_URL", default=f"http://{HOST}:{PORT}")

configure_logging()


def _create_application() -> FastAPI:
    executor = Mi5AgentExector()
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
        push_sender=None,
        queue_manager=InMemoryQueueManager(),
    )
    server = A2AFastAPIApplication(
        agent_card=build_agent_card(base_url=BASE_URL),
        http_handler=request_handler,
        extended_agent_card=None,
        card_modifier=None,
        context_builder=None,
        extended_card_modifier=None,
    )
    fastapi_app: FastAPI = server.build()
    return fastapi_app


app: FastAPI = _create_application()


def run() -> None:
    """Run the application."""
    uvicorn.run(
        "mi5_agent.app:app",
        host=HOST,
        port=PORT,
        reload=False,
    )


if __name__ == "__main__":
    run()
