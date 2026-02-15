"""FastAPI application for the A2A Registry service."""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from a2a_registry.models import (
    AgentsListResponse,
    HealthResponse,
    RegisterRequest,
    RegisterResponse,
    UnregisterResponse,
)
from a2a_registry.store import registry_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger: logging.Logger = logging.getLogger(name=__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown."""
    logger.info("A2A Registry starting up...")
    logger.info("Registry available at http://%s:%s", HOST, PORT)
    yield
    logger.info("A2A Registry shutting down...")
    registry_store.clear()


app = FastAPI(
    title="A2A Agent Registry",
    description="Dynamic agent discovery and registration service",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for web frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_agent(request: RegisterRequest) -> RegisterResponse:
    """Register an agent with the registry.

    Args:
        request: Registration request containing address and agent card

    Returns:
        Registration response with agent details

    """
    logger.info(
        "Registering agent: %s at %s",
        request.agent_card.name,
        request.address,
    )

    entry = registry_store.register(
        address=request.address,
        agent_card=request.agent_card,
    )

    return RegisterResponse(
        agent_name=entry.agent_card.name,
        address=entry.address,
    )


@app.delete("/unregister/{address:path}", response_model=UnregisterResponse)
async def unregister_agent(address: str) -> UnregisterResponse:
    """Unregister an agent from the registry.

    Args:
        address: Base URL of the agent to unregister

    Returns:
        Unregistration response

    Raises:
        HTTPException: If agent not found

    """
    logger.info("Unregistering agent at: %s", address)

    success = registry_store.unregister(address=address)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent at address {address} not found",
        )

    return UnregisterResponse(address=address)


@app.get("/agents", response_model=AgentsListResponse)
async def list_agents() -> AgentsListResponse:
    """List all registered agents.

    Returns:
        List of all registered agents

    """
    agents = registry_store.get_all()
    logger.debug("Listing %d registered agents", len(agents))
    return AgentsListResponse(agents=agents)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health status and agent count

    """
    return HealthResponse(agent_count=registry_store.count())


# Configuration
HOST: str = os.getenv("REGISTRY_HOST", "127.0.0.1")
PORT: int = int(os.getenv("REGISTRY_PORT", "8090"))


def main() -> None:
    """Run the A2A Registry service."""
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
