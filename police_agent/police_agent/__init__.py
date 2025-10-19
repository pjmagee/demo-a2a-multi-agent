"""Police Agent package."""

from agents import enable_verbose_stdout_logging, set_tracing_disabled

from police_agent.agent import PoliceAgent
from police_agent.executor import PoliceAgentExecutor

enable_verbose_stdout_logging()
set_tracing_disabled(disabled=True)

__all__: list[str] = ["PoliceAgent", "PoliceAgentExecutor"]
