"""Interactive REPL utility for the 911 Operator agent."""

import asyncio

from agents import run_demo_loop

from operator_911_agent.agent import Operator911Agent


async def _async_main() -> None:
    agent_wrapper = Operator911Agent()
    await run_demo_loop(agent=agent_wrapper.agent)

def main() -> None:
    """Run the 911 Operator agent in an interactive REPL."""
    asyncio.run(main=_async_main())


if __name__ == "__main__":
    main()
