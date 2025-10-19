# A2A + OpenAI Agent SDK Learning Sandbox

## Setup

- Python 3.13
- Ruff
- Pylance with strict type checking
- VSCode launch and tasks configured
- UV for python, packages, venv setup
- VSCode mutli root code-workspace for nice Python Interpreter configuration

## Implemented

- Basic A2A Agent wrappers around OpenAI Agents
- Tool calls
- Short term OpenAI Agent in-memory
- Shared library that can be used across isolated python agents
- Common shared tool calls (e.g enabling agents to list and find other agents)
- Interactive via command line with a testing agent and ask it to call other agents

## TODO

- Implement guardrails example
- Zookeeper or alternative /.well-known/agent-card.json discoverability
- Add OpenTelemetry with jaeger otel
- A2A Tasks cancellation
- docker compose or .NET Aspire
- Implement agent(s) using Microsoft Agent SDK
- Long term memory