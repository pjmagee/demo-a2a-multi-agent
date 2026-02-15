# A2A + OpenAI Agent SDK Learning Sandbox

## Architecture

### A2A Registry (Dynamic Agent Discovery)

The system uses a central **A2A Registry** service for dynamic agent discovery:

- **Registry Service** (`a2a_registry`): FastAPI service running on port 8090
  - Agents register on startup (address + AgentCard)
  - Agents unregister on graceful shutdown
  - Provides `/agents` endpoint for peer discovery
  
- **Agent Registration**: Each agent automatically registers/unregisters via `shared.registry_client`
- **Dynamic Peer Discovery**: Agents query the registry instead of using hardcoded addresses
- **No Configuration Required**: Remove `PEER_AGENT_ADDRESSES` environment variables

**Environment Variables:**
- `A2A_REGISTRY_URL`: Registry URL (default: `http://127.0.0.1:8090`)
- `BASE_URL`: Each agent's base URL for self-filtering

## Setup

- Python 3.13
- Ruff
- Pylance with strict type checking
- VSCode launch and tasks configured
- UV for python, packages, venv setup
- VSCode mutli root code-workspace for nice Python Interpreter configuration
- CopilotKit

## Implemented

- **A2A Registry**: Dynamic agent registration and discovery service
- **Aspire Orchestration**: .NET Aspire for service orchestration with built-in telemetry
- Basic A2A Agent using OpenAI Agent Framework and Microsoft Agent Framework
- Short term OpenAI Agent in-memory
- Short term Microsoft Agent in-memory
- Common shared library with shared tool calls (e.g enabling agents to list and find other agents)
- **Dynamic Agent Discovery**: Agents query registry for available peers
- **Automated Registration**: Agents self-register/unregister with lifecycle hooks
- OpenAI REPL example via command line with a testing agent and ask it to call other agents
- Microsoft DevUI example counter agent

## Running the System

### Option 1: .NET Aspire (Recommended)

Run everything with a single command and get built-in metrics, logs, and service health monitoring:

```bash
cd aspire
dotnet run
```

This starts:
- Aspire Dashboard at http://localhost:15888 (metrics, logs, traces)
- A2A Registry at http://localhost:8090
- All 9 agents (auto-register with registry)
- Backend API at http://localhost:8100
- Frontend at http://localhost:3000

See [aspire/README.md](aspire/README.md) for details.

### Option 2: Manual Startup

#### Quick Start

1. **Start the Registry** (required first):
   ```bash
   cd a2a_registry
   uv run python -m a2a_registry.app
   ```
   Registry runs on `http://127.0.0.1:8090`

2. **Start Backend** (for web UI):
   ```bash
   cd backend
   uv run python -m webapp_backend.app
   ```
   Backend runs on `http://127.0.0.1:8100`

3. **Start Agents** (they will auto-register):
   ```bash
   cd emergency_operator_agent
   uv run python -m emergency_operator_agent.app
   ```
   Repeat for other agents (firebrigade, police, mi5, ambulance, weather, tester, greetings, counter)

4. **Start Frontend** (for web UI):
   ```bash
   cd frontend/agent-ui
   npm run dev
   ```
   Frontend runs on `http://localhost:3000`

5. **Or use VS Code tasks**: 
   - Run `workspace: dev stack` task to start registry, backend, and frontend
   - Run individual agent tasks like `emergency_operator_agent: run`

### Verify Registration

Check registered agents:
```bash
# Registry endpoint
curl http://127.0.0.1:8090/agents

# Backend endpoint (queries registry)
curl http://127.0.0.1:8100/api/agents
```

### Environment Variables

**Required for each agent:**
- `BASE_URL`: Agent's address (e.g., `http://127.0.0.1:8011`)
- `PORT`: Agent's port (e.g., `8011`)

**Optional:**
- `A2A_REGISTRY_URL`: Registry location (default: `http://127.0.0.1:8090`)

**Backend specific:**
- `WEBAPP_USE_REGISTRY`: Enable registry mode (default: `true`)
- `WEBAPP_REGISTRY_URL`: Registry location (default: `http://127.0.0.1:8090`)
- `WEBAPP_AGENT_ADDRESSES`: CSV list of agents (legacy mode if `USE_REGISTRY=false`)

## TODO

- Continue on CopilotKit
- Implement better guardrail examples
- Add more OpenTelemetry instrumentation
- A2A Tasks cancellation
- Implement various other agent(s) using various Agent SDKs
- Long term memory
- Session management