"""Interactive REPL utility for the Greetings agent."""

import asyncio

from agents import run_demo_loop

from greetings_agent.agent import GreetingsAgent


async def _async_main() -> None:
    agent_wrapper = GreetingsAgent()
    # https://openai.github.io/openai-agents-python/repl/
    await run_demo_loop(agent=agent_wrapper.agent)


def main() -> None:
    """Run the asynchronous main function."""
    asyncio.run(main=_async_main())


if __name__ == "__main__":
    main()
