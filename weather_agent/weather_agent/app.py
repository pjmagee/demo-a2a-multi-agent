"""Application entry point for the Weather agent."""

import os

import uvicorn
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.events import InMemoryQueueManager
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from fastapi import FastAPI

from weather_agent.agent_card import build_agent_card
from weather_agent.executor import WeatherAgentExecutor

PORT = int(os.getenv(key="PORT", default="8015"))
HOST: str = os.getenv(key="HOST", default="127.0.0.1")
BASE_URL: str = os.getenv(key="BASE_URL", default=f"http://{HOST}:{PORT}")

def _create_application() -> FastAPI:
    executor = WeatherAgentExecutor()
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
        app="weather_agent.app:app",
        host=HOST,
        port=PORT,
        reload=False,
    )


if __name__ == "__main__":  # pragma: no cover
    run()
