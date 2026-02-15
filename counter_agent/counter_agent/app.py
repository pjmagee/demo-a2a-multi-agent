"""Application entry point for the Counter agent."""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.events import InMemoryQueueManager
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from fastapi import FastAPI
from shared.otel_config import configure_telemetry
from shared.registry_client import register_with_registry, unregister_from_registry

from counter_agent.agent_card import build_agent_card
from counter_agent.executor import CounterAgentExecutor

# Initialize OpenTelemetry for Aspire dashboard
configure_telemetry("counter-agent")

logger = logging.getLogger(__name__)

PORT = int(os.getenv(key="PORT", default="8020"))
HOST: str = os.getenv(key="HOST", default="127.0.0.1")
BASE_URL: str = os.getenv(key="BASE_URL", default=f"http://{HOST}:{PORT}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage agent registration lifecycle."""
    agent_card = build_agent_card(base_url=BASE_URL)
    logger.info("Counter Agent starting at %s", BASE_URL)
    await register_with_registry(BASE_URL, agent_card)
    yield
    await unregister_from_registry(BASE_URL)


def _create_application() -> FastAPI:
    executor = CounterAgentExecutor()
    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
        push_sender=None,
        queue_manager=InMemoryQueueManager(),
    )

    app = A2AFastAPIApplication(
        agent_card=build_agent_card(base_url=BASE_URL),
        http_handler=handler,
        extended_agent_card=None,
        card_modifier=None,
        context_builder=None,
        extended_card_modifier=None,
    )
    api: FastAPI = app.build()
    api.router.lifespan_context = lifespan
    return api


app: FastAPI = _create_application()


def run() -> None:
    """Run the application."""
    uvicorn.run(
        app="counter_agent.app:app",
        host=HOST,
        port=PORT,
        reload=False,
    )


if __name__ == "__main__":
    run()
