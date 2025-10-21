"""Interactive REPL utility for the Fire Brigade Agent."""

import asyncio

from agents import run_demo_loop

from firebrigade_agent.agent import FireBrigadeAgent


async def _async_main() -> None:
    agent_wrapper = FireBrigadeAgent()
    await run_demo_loop(agent=agent_wrapper.agent)

def main() -> None:
    """Run the main asynchronous function."""
    asyncio.run(main=_async_main())

if __name__ == "__main__":
    main()
