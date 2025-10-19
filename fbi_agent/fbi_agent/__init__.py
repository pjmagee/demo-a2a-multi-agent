"""FBI Agent package."""

from agents import enable_verbose_stdout_logging, set_tracing_disabled

from fbi_agent.agent import FBIAgent
from fbi_agent.executor import FBIAgentExecutor

enable_verbose_stdout_logging()
set_tracing_disabled(disabled=True)

__all__: list[str] = ["FBIAgent", "FBIAgentExecutor"]
