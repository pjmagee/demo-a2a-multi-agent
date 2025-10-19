"""Ambulance Agent package."""

from agents import enable_verbose_stdout_logging, set_tracing_disabled

from ambulance_agent.agent import AmbulanceAgent
from ambulance_agent.executor import AmbulanceAgentExecutor

enable_verbose_stdout_logging()
set_tracing_disabled(disabled=True)

__all__: list[str] = ["AmbulanceAgent", "AmbulanceAgentExecutor"]
