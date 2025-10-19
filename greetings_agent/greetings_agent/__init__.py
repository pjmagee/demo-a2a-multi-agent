"""Greetings agent package."""

from agents import enable_verbose_stdout_logging, set_tracing_disabled

from greetings_agent.agent import GreetingsAgent
from greetings_agent.executor import GreetingsAgentExecutor

# https://openai.github.io/openai-agents-python/tracing/
enable_verbose_stdout_logging()
set_tracing_disabled(disabled=True)

__all__: list[str] = ["GreetingsAgent", "GreetingsAgentExecutor"]
