"""Interactive REPL utility for the FireFighter agent."""

import asyncio

from agents import run_demo_loop

from firefighter_agent.agent import FireFighterAgent


async def _async_main() -> None:
    agent_wrapper = FireFighterAgent()
    await run_demo_loop(agent=agent_wrapper.agent)

def main() -> None:
    """Run the main asynchronous function."""
    asyncio.run(main=_async_main())

if __name__ == "__main__":
    main()
