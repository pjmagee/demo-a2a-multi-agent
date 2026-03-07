"""Application entry point for the Star Wars agent."""

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
from shared.phoenix_setup import setup_phoenix_tracing
from shared.registry_client import register_with_registry, unregister_from_registry

# Instrument before importing agent/LLM modules
setup_phoenix_tracing("starwars-agent")

from starwars_agent.agent_card import build_agent_card
from starwars_agent.data_pipeline.loader import run_pipeline
from starwars_agent.executor import StarWarsAgentExecutor

logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", "8022"))
HOST: str = os.getenv("HOST", "127.0.0.1")
BASE_URL: str = os.getenv("BASE_URL", f"http://{HOST}:{PORT}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage agent registration lifecycle and data pipeline."""
    agent_card = build_agent_card(base_url=BASE_URL)
    logger.info("Star Wars Agent starting at %s", BASE_URL)

    # Run data pipeline (ingest articles if collection is empty)
    try:
        await run_pipeline()
        logger.info("Data pipeline check complete")
    except Exception:
        logger.exception("Data pipeline failed — agent will start but may lack data")

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
    logger.info("Star Wars Agent shutting down...")
    unregistered = await unregister_from_registry(agent_address=BASE_URL)
    if unregistered:
        logger.info("Successfully unregistered from A2A Registry")
    else:
        logger.warning("Failed to unregister from A2A Registry")


def _create_application() -> FastAPI:
    agent_card = build_agent_card(base_url=BASE_URL)
    agent_executor = StarWarsAgentExecutor()
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
        push_sender=None,
        queue_manager=InMemoryQueueManager(),
    )
    a2a_app = A2AFastAPIApplication(
        agent_card=agent_card,
        http_handler=request_handler,
        extended_agent_card=None,
        card_modifier=None,
        context_builder=None,
        extended_card_modifier=None,
    )
    api: FastAPI = a2a_app.build()
    api.router.lifespan_context = lifespan
    return api


app: FastAPI = _create_application()


def run() -> None:
    """Run the application."""
    uvicorn.run(
        app="starwars_agent.app:app",
        host=HOST,
        port=PORT,
        reload=False,
    )


if __name__ == "__main__":
    run()
