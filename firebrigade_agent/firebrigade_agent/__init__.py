"""FireBrigade Agent package."""

from agents import enable_verbose_stdout_logging, set_tracing_disabled

from firebrigade_agent.agent import FireBrigadeAgent
from firebrigade_agent.executor import FireBrigadeAgentExecutor

enable_verbose_stdout_logging()
set_tracing_disabled(disabled=True)

__all__: list[str] = ["FireBrigadeAgent", "FireBrigadeAgentExecutor"]
