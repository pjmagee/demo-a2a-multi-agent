"""Application entry point for the Emergency Operator Agent."""

import logging
import os

import uvicorn
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.events import InMemoryQueueManager
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from fastapi import FastAPI
from shared.otel_config import configure_telemetry
from shared.registry_client import register_with_registry, unregister_from_registry

from emergency_operator_agent.agent_card import build_agent_card
from emergency_operator_agent.task_executor import TaskOrchestratedExecutor

# Initialize OpenTelemetry for Aspire dashboard
configure_telemetry("emergency-operator-agent")

logger: logging.Logger = logging.getLogger(name=__name__)

PORT = int(os.getenv(key="PORT", default="8016"))
HOST: str = os.getenv(key="HOST", default="127.0.0.1")
BASE_URL: str = os.getenv(key="BASE_URL", default=f"http://{HOST}:{PORT}")


def _create_application() -> FastAPI:
    # Create task store to be shared between executor and request handler
    task_store = InMemoryTaskStore()

    request_handler = DefaultRequestHandler(
        agent_executor=TaskOrchestratedExecutor(task_store=task_store),
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

    # Add startup handler for pre-caching and registry registration
    @fastapi_app.on_event("startup")
    async def startup_event() -> None:
        """Handle startup tasks."""
        agent_card = build_agent_card(base_url=BASE_URL)
        logger.info("Emergency Operator Agent starting up at %s", BASE_URL)

        # Pre-cache agents to avoid delays during first emergency call
        from emergency_operator_agent.task_orchestrator import EmergencyTaskOrchestrator
        orchestrator = EmergencyTaskOrchestrator()
        logger.info("Pre-fetching available agents from registry...")
        try:
            agents = await orchestrator._fetch_available_agents()  # noqa: SLF001
            logger.info("Successfully pre-cached %d agents", len(agents))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to pre-cache agents: %s", exc)

        # Register with the A2A Registry on startup
        registered = await register_with_registry(
            agent_address=BASE_URL,
            agent_card=agent_card,
        )
        if registered:
            logger.info("Successfully registered with A2A Registry")
        else:
            logger.warning("Failed to register with A2A Registry")

    # Add shutdown handler for registry unregistration
    @fastapi_app.on_event("shutdown")
    async def shutdown_event() -> None:
        """Handle shutdown tasks."""
        logger.info("Emergency Operator Agent shutting down...")
        unregistered = await unregister_from_registry(agent_address=BASE_URL)
        if unregistered:
            logger.info("Successfully unregistered from A2A Registry")
        else:
            logger.warning("Failed to unregister from A2A Registry")

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
