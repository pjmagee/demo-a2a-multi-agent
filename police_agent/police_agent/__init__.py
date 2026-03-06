"""Police Agent package."""

from agents import enable_verbose_stdout_logging

from police_agent.agent import PoliceAgent
from police_agent.executor import PoliceAgentExecutor

enable_verbose_stdout_logging()

__all__: list[str] = ["PoliceAgent", "PoliceAgentExecutor"]
