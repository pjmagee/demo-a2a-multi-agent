"""
Apply registry-based agent registration to all agent projects.

This script adds the lifespan registration pattern to all agent app.py files.
Run this after updating the emergency_operator_agent as the reference implementation.
"""

import os
from pathlib import Path

AGENTS = [
    "firebrigade_agent",
    "police_agent",
    "mi5_agent",
    "ambulance_agent",
    "weather_agent",
    "tester_agent",
    "greetings_agent",
    "counter_agent",
]

TEMPLATE = '''"""Application entry point with registry registration."""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from shared.registry_client import register_with_registry, unregister_from_registry

from {package}.agent_card import build_agent_card

logger: logging.Logger = logging.getLogger(name=__name__)

PORT = int(os.getenv(key="PORT", default="{port}"))
HOST: str = os.getenv(key="HOST", default="127.0.0.1")
BASE_URL: str = os.getenv(key="BASE_URL", default=f"http://{{HOST}}:{{PORT}}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage agent registration lifecycle."""
    agent_card = build_agent_card(base_url=BASE_URL)
    logger.info("{agent_name} starting up at %s", BASE_URL)

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
    logger.info("{agent_name} shutting down...")
    unregistered = await unregister_from_registry(agent_address=BASE_URL)
    if unregistered:
        logger.info("Successfully unregistered from A2A Registry")
    else:
        logger.warning("Failed to unregister from A2A Registry")
'''


def main():
    """Generate migration guide for each agent."""
    root = Path(__file__).parent.parent
    
    print("=" * 80)
    print("A2A Registry Migration Guide")
    print("=" * 80)
    print()
    print("The emergency_operator_agent has been updated as a reference.")
    print("Apply similar changes to other agents:")
    print()
    
    for agent in AGENTS:
        agent_path = root / agent / f"{agent}" / "app.py"
        if agent_path.exists():
            print(f"📝 {agent}:")
            print(f"   File: {agent_path}")
            print(f"   1. Add lifespan imports and function")
            print(f"   2. Add 'lifespan=lifespan' or set router.lifespan_context")
            print(f"   3. Remove PEER_AGENT_ADDRESSES from .env if present")
            print()


if __name__ == "__main__":
    main()
