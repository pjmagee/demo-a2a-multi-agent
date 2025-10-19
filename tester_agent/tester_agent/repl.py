"""Interactive REPL utility for the Tester agent."""

import asyncio

from agents import run_demo_loop

from tester_agent.agent import TesterAgent


async def _async_main() -> None:
    tester_agent = TesterAgent()
    await run_demo_loop(agent=tester_agent.agent)


def main() -> None:
    """Run the Tester agent."""
    asyncio.run(main=_async_main())


if __name__ == "__main__":
    main()
