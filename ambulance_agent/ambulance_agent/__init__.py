"""Ambulance Agent package."""

from agents import enable_verbose_stdout_logging

from ambulance_agent.agent import AmbulanceAgent
from ambulance_agent.executor import AmbulanceAgentExecutor

enable_verbose_stdout_logging()

__all__: list[str] = ["AmbulanceAgent", "AmbulanceAgentExecutor"]
