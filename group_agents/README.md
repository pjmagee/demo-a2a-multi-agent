# Group Chat Agents

A multi-agent group chat application using **Microsoft Agent Framework** with **AG-UI** protocol for real-time streaming.

## Architecture

- **Backend** (`backend/`) — Python FastAPI server  
  - Group Chat orchestration via `agent-framework-orchestrations`
  - AG-UI SSE endpoint (Server-Sent Events)
  - REST API for dynamic agent management  

- **Frontend** (`frontend/GroupChatUI/`) — Blazor Web App  
  - Split 50/50 layout: Chat (left) + Agent Management (right)
  - AG-UI SSE client for real-time streaming
  - Interactive Server rendering

## Prerequisites

- Python 3.13+
- .NET 10 SDK
- [uv](https://docs.astral.sh/uv/) Python package manager
- OpenAI API key

## Quick Start

### 1. Install dependencies

```bash
# Backend
cd backend
uv sync

# Frontend
cd ../frontend/GroupChatUI
dotnet restore
```

### 2. Set environment variables

```bash
# Backend requires
export OPENAI_API_KEY="sk-..."
export OPENAI_CHAT_MODEL_ID="gpt-4o-mini"  # optional, defaults to gpt-4o-mini
```

### 3. Run the backend

```bash
cd backend
uv run python -m group_chat_backend.app
# Starts on http://127.0.0.1:8050
```

### 4. Run the frontend

```bash
cd frontend/GroupChatUI
dotnet run --launch-profile http
# Starts on http://localhost:5024
```

### 5. Use the app

1. Open `http://localhost:5024` in your browser
2. On the **right panel**, add agents by providing a name and system prompt
3. On the **left panel**, type a message and see agents respond in the group chat

## AG-UI Protocol

The backend exposes an AG-UI SSE endpoint at `POST /` that streams events:

| Event | Description |
|-------|-------------|
| `RUN_STARTED` | Chat run has started |
| `TEXT_MESSAGE_START` | New agent message beginning |
| `TEXT_MESSAGE_CONTENT` | Streaming text delta |
| `TEXT_MESSAGE_END` | Agent message complete |
| `RUN_FINISHED` | Chat run complete |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/agents` | List configured agents |
| `POST` | `/api/agents` | Add an agent `{name, system_prompt}` |
| `DELETE` | `/api/agents/{name}` | Remove an agent |
| `POST` | `/` | AG-UI SSE endpoint |
