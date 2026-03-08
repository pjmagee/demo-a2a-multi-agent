# Multi-Agent Sandbox

An environment for learning multi-agent systems using **Agent-to-Agent (A2A) Protocol** with different agent **SDKs**.

## Overview

**What This Is:**

- Multi-agent orchestration sandbox using A2A protocol
- Local observability, metrics, tracing with Aspire & Phoenix
- Agent discovery via an A2A Registry

**Tech Stack:**

- **Protocol**: A2A (Agent-to-Agent) for inter-agent communication
- **Agent SDKs**: OpenAI Agent SDK, Microsoft Agent Framework, Strand SDK
- **Orchestration**: Aspire for service management and telemetry
- **Observability**: Phoenix (LLM tracing), OpenTelemetry (distributed tracing)
- **Languages**: Python 3.13, TypeScript/React, C#
- **Tools**: uv (Python package management), VSCode, MCPs
- **DB**: MongoDB (task persistence, storage, vector search)

## Quick Start

### Prerequisites

- Python 3.13+
- .NET 10.0 SDK
- Docker Desktop
- Node.js 20+
- uv package manager

### Run Everything

```bash
cd aspire
dotnet run
```

This starts:

- **Aspire Dashboard**: <https://localhost:17138> (metrics, logs, traces)
- **A2A Registry**: Dynamic agent discovery service
- **Agents**: Various agents
- **Backend**: BFF for frontend
- **Frontend**: React web UI exposing Agents
- **Phoenix**: LLM observability at <http://localhost:6006>
- **MongoDB**: Task state persistence

## Architecture

### A2A Registry (Dynamic Discovery)

Agents automatically register on startup and discover peers at runtime - **no hardcoded endpoints needed**. The registry service provides dynamic agent discovery, allowing agents to find each other and their capabilities.

### Multi-SDKs / Frameworks

The sandbox demonstrates agnostic patterns with multiple agent frameworks:

- **OpenAI Agent SDK**: Fire, Police, Ambulance, Weather, Emergency Operator, Tester, Greetings agents
- **Microsoft Agent Framework**: Counter agent, with A2A File / Text Parts demonstration
- **LangGraph**: Game News agent

Each agent implements the A2A protocol regardless of the underlying SDK, enabling seamless inter-agent communication.

### Observability Stack

**Aspire Dashboard** - Service orchestration, health, logs:  

- Resource status (Running/Failed)
- Environment variables
- Console logs per service
- Structured logs with filtering
- OpenTelemetry traces

**Phoenix** - LLM-specific observability:  

- Prompt/completion tracing
- Token usage analytics
- Latency metrics
- Cost tracking

## Features to Explore

### ✅ Implemented

1. **A2A Registry** - Dynamic agent discovery and registration
2. **Multi-SDK Support** - OpenAI, Microsoft, LangGraph agents
3. **Task Persistence** - MongoDB-backed A2A task store
4. **Web Interface** - React frontend + FastAPI backend
5. **Observability** - Aspire + Phoenix integration
6. **MCP Bridge** - Model Context Protocol to A2A bridge

### 🚧 To Explore

1. **A2A Tasks + State** - Long-running task management
2. **Handoffs & Sub-Agents** - Agent delegation patterns
3. **Authentication** - Secure agent-to-agent communication
4. **A2A Extensions** - Custom protocol extensions
5. **Authentication & Authorization** - Authentication, Authorization
6. **Advanced Phoenix** - Evaluators, datasets, experiments, prompt management

## MCP-to-A2A Bridge

The `mcp_a2a_bridge` project enables **GitHub Copilot in your IDE** to communicate directly with running A2A agents through the Model Context Protocol (MCP).

**Why This Matters:**

- Works with **any running agents** - Aspire-orchestrated or standalone
- Allows Copilot to discover, query, and interact with your agents
- Enables IDE-driven agent testing and debugging
- Useful for development without full Aspire orchestration

**Use Cases:**

- Run agents locally (outside Aspire) and still interact via Copilot
- Test individual agents during development
- Debug agent responses from your IDE
- Query agent capabilities and send messages

The bridge exposes 4 MCP tools: `list_agents`, `get_agent_card`, `send_message`, and `get_task_status`. Configure it in your IDE's MCP settings to enable agent interaction through Copilot.

## Development

### Native Mode (Fast Iteration)

Skip Docker rebuilds during development:

```bash
cd aspire
USE_DOCKER=false dotnet run
```

Code changes apply immediately without container rebuilds.

### Directory Structure

```text
├── aspire/              # Aspire orchestration
├── a2a_registry/        # A2A agent discovery service
├── shared/              # Common utilities (registry client, MongoDB, OTEL)
├── *_agent/             # Individual agents (10 total)
├── backend/             # Web API (FastAPI)
├── frontend/            # Web UI (React + CopilotKit)
├── phoenix/             # Phoenix observability (Docker)
├── mcp_a2a_bridge/      # MCP to A2A bridge (C#)
└── a2a-inspector/       # A2A protocol inspector UI
```

### Key Components

**Shared Library** (`shared/`):

- `registry_client.py` - Agent registration/discovery
- `mongodb_task_store.py` - A2A task persistence
- `otel_config.py` - OpenTelemetry setup
- `peer_tools.py` - Cross-agent communication tools

**Agent Template**:

```text
agent_name/
├── agent_name/
│   ├── __init__.py
│   ├── app.py           # FastAPI entrypoint
│   ├── agent.py         # Agent logic (SDK-specific)
│   ├── executor.py      # A2A request handler
│   └── agent_card.py    # A2A capabilities definition
├── pyproject.toml       # Dependencies
└── Dockerfile           # Container image
```

## Resources

- [A2A Protocol Specification](https://a2a-protocol.org)
- [Aspire](https://aspire.dev/)
- [Phoenix Observability](https://docs.arize.com/phoenix)
- [OpenAI Agent SDK](https://github.com/openai/openai-agents-python)
- [Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/)
- [Kiota](https://learn.microsoft.com/en-us/openapi/kiota/overview)