"""Weather Agent package."""

from agents import enable_verbose_stdout_logging, set_tracing_disabled

from weather_agent.agent import WeatherAgent
from weather_agent.executor import WeatherAgentExecutor

enable_verbose_stdout_logging()
set_tracing_disabled(disabled=True)

__all__: list[str] = ["WeatherAgent", "WeatherAgentExecutor"]
