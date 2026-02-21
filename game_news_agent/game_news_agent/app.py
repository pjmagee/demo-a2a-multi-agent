"""FastAPI application entrypoint for Game News Agent."""

import json
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.events import InMemoryQueueManager
from a2a.server.request_handlers import DefaultRequestHandler
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from shared.mongodb_task_store import MongoDBTaskStore
from shared.otel_config import configure_telemetry
from shared.registry_client import register_with_registry, unregister_from_registry

from game_news_agent.agent_card import build_agent_card
from game_news_agent.executor import GameNewsAgentExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8021")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8021"))
# Aspire sets ConnectionStrings__<dbname> for MongoDB references
MONGODB_CONNECTION_STRING = os.getenv(
    "ConnectionStrings__game-news-agent-db",
    os.getenv("GAME_NEWS_AGENT_DB_URI", "mongodb://localhost:27017"),
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifespan (startup/shutdown)."""
    logger.info(f"Starting Game News Agent at {BASE_URL}")

    # Register with A2A Registry
    agent_card = build_agent_card(base_url=BASE_URL)
    await register_with_registry(agent_address=BASE_URL, agent_card=agent_card)

    yield

    # Unregister from A2A Registry
    logger.info("Shutting down Game News Agent")
    await unregister_from_registry(agent_address=BASE_URL)


def _create_application() -> FastAPI:
    """Create the FastAPI application with A2A integration."""
    # Initialize executor
    executor = GameNewsAgentExecutor()

    # Create MongoDB task store with pymongo native async client
    task_store = MongoDBTaskStore(
        connection_string=MONGODB_CONNECTION_STRING,
        database_name="game_news_agent",
        collection_name="tasks",
    )

    # Create A2A request handler
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=task_store,
        push_sender=None,
        queue_manager=InMemoryQueueManager(),
    )

    # Build A2A FastAPI application
    server = A2AFastAPIApplication(
        agent_card=build_agent_card(base_url=BASE_URL),
        http_handler=request_handler,
        extended_agent_card=None,
        card_modifier=None,
        context_builder=None,
        extended_card_modifier=None,
    )

    fastapi_app: FastAPI = server.build()

    # Attach lifespan for registry registration
    fastapi_app.router.lifespan_context = lifespan

    # Add schema endpoint for contract discovery
    schema_path = Path(__file__).parent.parent / "contracts" / "v1" / "request.schema.json"

    @fastapi_app.get("/contracts/v1/request.schema.json")
    async def get_request_schema() -> JSONResponse:
        """Serve the JSON schema for the gaming report request."""
        with schema_path.open() as f:
            schema = json.load(f)
        return JSONResponse(content=schema)

    return fastapi_app


# Create the application
app = _create_application()

# Configure OpenTelemetry for Aspire integration
configure_telemetry("game-news-agent")

if __name__ == "__main__":
    import uvicorn

    logger.info(f"Running Game News Agent on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
