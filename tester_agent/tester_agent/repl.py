"""Interactive REPL utility for the Tester agent."""

import asyncio
import logging

from agents import run_demo_loop

from tester_agent.agent import TesterAgent

# Configure logging to see debug output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def _async_main() -> None:
    tester_agent = TesterAgent()
    await run_demo_loop(
        agent=tester_agent.agent,
        stream=True,
    )


def main() -> None:
    """Run the Tester agent."""
    asyncio.run(main=_async_main())


if __name__ == "__main__":
    main()

