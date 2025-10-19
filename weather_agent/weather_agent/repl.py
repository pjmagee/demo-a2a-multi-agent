"""Interactive REPL utility for the Weather agent."""



import asyncio

from agents import run_demo_loop

from weather_agent.agent import WeatherAgent


async def _async_main() -> None:
    agent_wrapper = WeatherAgent()
    await run_demo_loop(agent=agent_wrapper.agent)


def main() -> None:
    """Run the interactive REPL utility for the Weather agent."""
    asyncio.run(main=_async_main())


if __name__ == "__main__":
    main()
