"""Interactive REPL utility for the Emergency Operator Agent."""

import asyncio

from agents import run_demo_loop

from emergency_operator_agent.agent import EmergencyOperatorAgent


async def _async_main() -> None:
    agent_wrapper = EmergencyOperatorAgent()
    await run_demo_loop(agent=agent_wrapper.agent)

def main() -> None:
    """Run the Emergency Operator Agent in an interactive REPL."""
    asyncio.run(main=_async_main())


if __name__ == "__main__":
    main()
