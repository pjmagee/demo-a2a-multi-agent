"""Emergency Operator Agent package."""

from agents import enable_verbose_stdout_logging, set_tracing_disabled

from emergency_operator_agent.agent import EmergencyOperatorAgent
from emergency_operator_agent.executor import OperatorAgentExecutor

enable_verbose_stdout_logging()
set_tracing_disabled(disabled=True)

__all__: list[str] = ["WeatherAgent", "WeatherAgentExecutor"]