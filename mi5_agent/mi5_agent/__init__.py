"""Mi5 Agent package."""

from agents import enable_verbose_stdout_logging

from mi5_agent.agent import Mi5Agent
from mi5_agent.executor import Mi5AgentExector

enable_verbose_stdout_logging()

__all__: list[str] = ["Mi5Agent", "Mi5AgentExector"]
