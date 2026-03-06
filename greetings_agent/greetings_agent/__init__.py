"""Greetings agent package."""

from agents import enable_verbose_stdout_logging

from greetings_agent.agent import GreetingsAgent
from greetings_agent.executor import GreetingsAgentExecutor

# https://openai.github.io/openai-agents-python/tracing/
enable_verbose_stdout_logging()

__all__: list[str] = ["GreetingsAgent", "GreetingsAgentExecutor"]
