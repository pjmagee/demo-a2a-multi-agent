"""FireBrigade Agent package."""

from agents import enable_verbose_stdout_logging

from firebrigade_agent.agent import FirebrigadeAgent
from firebrigade_agent.executor import FirebrigadeAgentExecutor

enable_verbose_stdout_logging()

__all__: list[str] = ["FireBrigadeAgent", "FireBrigadeAgentExecutor"]
