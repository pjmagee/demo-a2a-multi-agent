# A2A + OpenAI Agent SDK Learning Sandbox

## Setup

- Python 3.13
- Ruff
- Pylance with strict type checking
- VSCode launch and tasks configured
- UV for python, packages, venv setup
- VSCode mutli root code-workspace for nice Python Interpreter configuration
- CopilotKit

## Implemented

- Basic A2A Agent using OpenAI Agent Framework and Microsoft Agent Framework
- Short term OpenAI Agent in-memory
- Short term Microsoft Agent in-memory
- Common shared library with shared tool calls (e.g enabling agents to list and find other agents)
- OpenAI REPL example via command line with a testing agent and ask it to call other agents
- Microsoft DevUI example counter agent

## TODO

- Continue on CopilotKit
- Implement better guardrail examples
- Agent discoverability via agent registration
- Add OpenTelemetry with jaeger otel or alternative
- A2A Tasks cancellation
- docker compose or .NET Aspire
- Implement various other agent(s) using various Agent SDKs
- Long term memory
- Session management