"""Emergency Operator Agent package."""

from agents import enable_verbose_stdout_logging

from emergency_operator_agent.agent import EmergencyOperatorAgent
from emergency_operator_agent.executor import OperatorAgentExecutor

enable_verbose_stdout_logging()

__all__: list[str] = ["EmergencyOperatorAgent", "OperatorAgentExecutor"]
