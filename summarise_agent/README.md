# Summarise Agent

A lightweight A2A agent that generates concise, descriptive titles for chat
conversations. Used by the frontend to label thread history entries.

## What it does

Given a conversation (list of user/assistant messages) the agent produces a
short title (3-8 words) that captures the main topic.

## Running

```bash
cd summarise_agent
uv sync --group dev
uv run python -m summarise_agent.app
```

The agent runs on port **8023** by default and registers itself with the A2A
Registry on startup.
