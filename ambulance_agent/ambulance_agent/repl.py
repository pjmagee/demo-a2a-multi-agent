"""Interactive REPL utility for the Ambulance agent."""

import asyncio

from agents import run_demo_loop

from ambulance_agent.agent import AmbulanceAgent


async def _async_main() -> None:
    agent = AmbulanceAgent()
    await run_demo_loop(agent=agent.agent)

def main() -> None:
    """Run the main function."""
    asyncio.run(main=_async_main())

if __name__ == "__main__":
    main()
