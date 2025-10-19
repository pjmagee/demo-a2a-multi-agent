"""Interactive REPL utility for the Police agent."""

import asyncio

from agents import run_demo_loop

from police_agent.agent import PoliceAgent


async def _async_main() -> None:
    agent_wrapper = PoliceAgent()
    await run_demo_loop(agent=agent_wrapper.agent)

def main() -> None:
    """Run the main function."""
    asyncio.run(main=_async_main())

if __name__ == "__main__":
    main()
