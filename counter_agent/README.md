# Counter Agent

A2A Agent that streams count numbers using Microsoft's agent-framework.

## Features

- Streams count responses as Server-Sent Events (SSE)
- Demonstrates async streaming with agent-framework
- Returns each number as a separate A2A message

## Usage

```bash
# Install dependencies
uv sync --group dev

# Run the agent
uv run python -m counter_agent.app
```
