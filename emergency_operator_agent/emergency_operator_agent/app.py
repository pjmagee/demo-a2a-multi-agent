"""Application entry point for the Emergency Operator Agent."""

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

from emergency_operator_agent.agent_card import build_agent_card
from emergency_operator_agent.executor import OperatorAgentExecutor

# Initialize OpenTelemetry for Aspire dashboard
configure_telemetry("emergency-operator-agent")

logger: logging.Logger = logging.getLogger(name=__name__)

PORT = int(os.getenv(key="PORT", default="8016"))
HOST: str = os.getenv(key="HOST", default="127.0.0.1")
BASE_URL: str = os.getenv(key="BASE_URL", default=f"http://{HOST}:{PORT}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage agent registration lifecycle."""
    agent_card = build_agent_card(base_url=BASE_URL)
    logger.info("Emergency Operator Agent starting up at %s", BASE_URL)

    # Register with the A2A Registry on startup
    registered = await register_with_registry(
        agent_address=BASE_URL,
        agent_card=agent_card,
    )
    if registered:
        logger.info("Successfully registered with A2A Registry")
    else:
        logger.warning("Failed to register with A2A Registry")

    yield

    # Unregister from the A2A Registry on shutdown
    logger.info("Emergency Operator Agent shutting down...")
    unregistered = await unregister_from_registry(agent_address=BASE_URL)
    if unregistered:
        logger.info("Successfully unregistered from A2A Registry")
    else:
        logger.warning("Failed to unregister from A2A Registry")


def _create_application() -> FastAPI:
    # Create task store to be shared between executor and request handler
    task_store = InMemoryTaskStore()

    request_handler = DefaultRequestHandler(
        agent_executor=OperatorAgentExecutor(task_store=task_store),
        task_store=task_store,
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

    # Add lifespan for registry registration/unregistration
    fastapi_app.router.lifespan_context = lifespan

    return fastapi_app


app: FastAPI = _create_application()


def run() -> None:
    """Run the application."""
    uvicorn.run(
        app="emergency_operator_agent.app:app",
        host=HOST,
        port=PORT,
        reload=False,
    )


if __name__ == "__main__":
    run()
