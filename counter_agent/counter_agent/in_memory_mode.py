"""Interactive DevUI for Counter Agent using Microsoft agent-framework.

This provides a web-based UI alternative to the REPL, serving the CounterAgent
as an OpenAI-compatible API endpoint with in-memory entity registration.
"""

import logging

from agent_framework import Agent
from agent_framework.devui import serve

from counter_agent.agent import CounterAgent


def main() -> None:
    """Demonstrate in-memory entity registration for CounterAgent."""
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger: logging.Logger = logging.getLogger(name=__name__)

    # Create counter agent instance
    counter_agent_instance = CounterAgent()

    # Get the underlying Agent for DevUI
    agent: Agent = counter_agent_instance.agent

    # Collect entities for serving
    entities: list[Agent] = [agent]

    logger.info(msg="Starting DevUI on http://localhost:8090")
    logger.info(msg="Entities available:")
    logger.info(msg="  - Agent: CounterAgent")
    logger.info(msg="  - Test with: 'Count to 10' or 'Count from 1 to 5'")

    # Launch server with auto-generated entity IDs
    serve(entities=entities, port=8090, auto_open=True)


if __name__ == "__main__":
    main()
