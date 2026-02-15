# Copilot Instructions

## Summary

- Each project is a separate package in the workspace, with its own FastAPI entrypoint and uv configuration.
- Agents are implemented as A2A FastAPI applications that expose framework specific agents e.g OpenAI Agent SDK, Microsoft Agent Framework, etc.
- Executors are responsible for adapting the incoming request to the agent and enqueueing the response(s) to the event queue, which can make use of SSE
- A2A should handle messages and tasks, and the agent should be responsible for the conversation state and context
- Agents should be implemented as classes that wrap the underlying agent SDK

## Architecture

- Multi-root uv workspace; each agent folder (firebrigade_agent, police_agent, etc.) is its own package plus dedicated FastAPI entrypoint, with shared utilities in shared/.
- Services use a2a-sdk: each app.py builds an A2AFastAPIApplication + DefaultRequestHandler wired to executor.py, exposing JSON-RPC message/send endpoints.
- Executors adapt RequestContext to the domain agent, ensure context IDs via shared/openai_session_helpers, and enqueue responses through EventQueue.
- AgentCard definitions in agent_card.py describe skills and must align with the actual tools exposed by agent.py.

## Agent Implementation

- Agent classes wrap openai-agents Agent instances; invoke() calls Runner.run with sessions from shared/openai_session_helpers.get_or_create_session to preserve conversation state.
- Always protect peer calls with shared.peer_tools.peer_message_context so downstream agents reuse the same context_id.
- Define tools with agents.function_tool; place domain tools in agent.py or dedicated modules (see weather_agent/tools.py) and include peer tools via shared.peer_tools.default_peer_tools when cross-agent messaging is needed.
- Guardrails live alongside agents (weather_agent/guard_rails.py, tester_agent/guard_rails.py) and plug in via the Agent constructor’s input_guardrails list.

## Aspire Orchestration

https://aspire.dev/llms.txt

## Shared Utilities & Cross-Agent

- shared/ is packaged via uv and mounted into each agent through pyproject.toml [tool.uv.sources]; favor adding reusable helpers here instead of duplicating code.
- shared/peer_tools.py provides list_agents/send_message functions backed by PEER_AGENT_ADDRESSES env var; keep BASE_URL per agent in sync so self-filtering works.
- shared/openai_session_helpers centralizes context and sqlite-backed session creation; reuse ensure_context_id in new executors for protocol compliance.

## Development Workflow

- Python 3.13 is required; create venvs with uv sync --group dev (tasks available in .vscode/tasks.json for each package or run the workspace aggregate task).
- Launch configurations in .vscode/launch.json target each agent’s app.py and repl.py using the package-local .venv/Scripts/python.exe and optional .env files.
- Run agents via uv run python -m <package>.app from their folder; repl entrypoints use agents.run_demo_loop for quick manual checks.
- Lint with uv run ruff check . inside each package; type checking relies on pyrightconfig.json execution environments per subproject.

## Patterns & Conventions

- Keep AgentCard.skill metadata synchronized with tool signatures and instructions; update examples whenever tool behavior changes.
- Executor wraps the domain Agent
- Log tool usage with logger.info for observability (see firebrigade_agent/agent.py); follow the existing structured messages when adding new tools.
- Configure new peer-aware agents to accept PEER_AGENT_ADDRESSES and avoid hard-coding hosts; add any new shared dependency to shared/pyproject.toml and reference it where needed.
