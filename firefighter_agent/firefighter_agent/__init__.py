"""FireFighter Agent package."""

from agents import enable_verbose_stdout_logging, set_tracing_disabled

from firefighter_agent.agent import FireFighterAgent
from firefighter_agent.executor import FireFighterAgentExecutor

enable_verbose_stdout_logging()
set_tracing_disabled(disabled=True)

__all__: list[str] = ["FireFighterAgent", "FireFighterAgentExecutor"]
