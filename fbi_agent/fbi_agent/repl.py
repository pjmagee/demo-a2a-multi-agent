"""Interactive REPL utility for the FBI agent."""



import asyncio
from agents import run_demo_loop

from fbi_agent.agent import FBIAgent

async def _async_main() -> None:
    agent_wrapper = FBIAgent()
    await run_demo_loop(agent_wrapper.agent)

def main() -> None:
    asyncio.run(_async_main())

if __name__ == "__main__":
    main()
