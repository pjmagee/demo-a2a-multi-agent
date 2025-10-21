"""Interactive REPL utility for the Mi5 Agent."""



import asyncio
from agents import run_demo_loop

from mi5_agent.agent import Mi5Agent

async def _async_main() -> None:
    agent_wrapper = Mi5Agent()
    await run_demo_loop(agent_wrapper.agent)

def main() -> None:
    asyncio.run(_async_main())

if __name__ == "__main__":
    main()
