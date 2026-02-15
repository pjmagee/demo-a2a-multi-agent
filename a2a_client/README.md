# A2A SSE Client

Custom A2A client for testing Server-Sent Events (SSE) streaming from A2A agents.

## Purpose

This client is designed to:
- Stream SSE events from A2A agents in real-time
- Provide visual feedback on message delivery
- Debug connection and streaming issues
- Test emergency operator task orchestration

## Usage

```bash
# Install dependencies
uv sync

# Run the client
uv run python -m a2a_client --agent-url http://localhost:8016 --message "fire and injuries at 170 London Road"
```

## Features

- Real-time SSE event streaming
- Connection health monitoring
- Message delivery tracking
- Rich console output with color-coded events
