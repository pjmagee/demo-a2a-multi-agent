# Aspire Orchestration

.NET Aspire orchestration for the A2A multi-agent system.

## Features

- **Service Orchestration**: Manages all agents, registry, backend, and frontend
- **Built-in Dashboard**: OpenTelemetry metrics, logs, and traces at http://localhost:15888
- **Service Discovery**: Automatic service references and health checks
- **Dependency Management**: Ensures registry starts before agents
- **Environment Management**: Centralized configuration for all services

## Architecture

```
aspire (AppHost)
├── a2a-registry (port 8090)           # Service discovery registry
├── Agents (auto-register with registry)
│   ├── firebrigade-agent (8011)
│   ├── police-agent (8012)
│   ├── mi5-agent (8013)
│   ├── ambulance-agent (8014)
│   ├── weather-agent (8015)
│   ├── emergency-operator (8016)
│   ├── tester-agent (8017)
│   ├── greetings-agent (8018)
│   └── counter-agent (8020)
├── backend (port 8100)                # Queries registry for agents
└── frontend (port 3000)               # Web UI
```

## Running with Aspire

### Prerequisites

- .NET 10 SDK
- .NET Aspire workload: `dotnet workload install aspire`
- Python 3.13 with uv
- Node.js for frontend
- OpenAI API key

### Configuration

Create `appsettings.Development.json` from the template:

```bash
cp appsettings.Development.json.template appsettings.Development.json
```

Then edit `appsettings.Development.json` and add your OpenAI API key:

```json
{
  "Parameters": {
    "openai-api-key": "sk-proj-YOUR_ACTUAL_KEY_HERE"
  }
}
```

The API key will be automatically injected into all agents as the `OPENAI_API_KEY` environment variable.

> **Note**: `appsettings.Development.json` is in `.gitignore` to keep your API key safe.

### Start Everything

```bash
cd aspire
dotnet run
```

This single command:
1. Starts the Aspire dashboard at http://localhost:15888
2. Launches the A2A registry
3. Starts all 9 agents (they auto-register)
4. Starts the backend API
5. Starts the frontend dev server
6. Provides telemetry, logs, and metrics for all services

### Access Services

- **Aspire Dashboard**: http://localhost:15888
- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8100
- **A2A Registry**: http://localhost:8090/agents

## Development

### Project Structure

```
aspire/
├── AppHost.cs              # Service definitions and orchestration
├── AppHost.csproj          # Aspire SDK project file
├── appsettings.json        # Configuration
└── appsettings.Development.json
```

### Adding a New Service

Edit `AppHost.cs`:

```csharp
var myAgent = builder.AddPythonApp("my-agent", "../my_agent", "my_agent.app")
    .WithHttpEndpoint(port: 8021, env: "PORT")
    .WithEnvironment("BASE_URL", "http://localhost:8021")
    .WithEnvironment("A2A_REGISTRY_URL", registryUrl)
    .WithReference(registry)
    .WaitFor(registry);
```

### Service Dependencies

- All agents depend on `registry` (via `WaitFor`)
- `backend` depends on `registry`
- `frontend` depends on `backend`

This ensures proper startup ordering.

## Telemetry

Aspire provides built-in observability:

- **Traces**: Request flows across services
- **Metrics**: Performance counters, HTTP requests
- **Logs**: Structured logging from all services
- **Console Output**: Real-time service logs

View in the dashboard at http://localhost:15888

## Troubleshooting

**"Cannot find Python module"**
- Ensure each agent has run `uv sync --group dev`
- Check virtual environments are created in each agent folder

**"Port already in use"**
- Stop any manually started services
- Ports used: 8011-8020, 8090, 8100, 3000, 15888

**"Registry not available"**
- Registry starts first but may take a few seconds
- Agents will retry registration automatically
- Check registry health: `curl http://localhost:8090/health`

## Comparison with Manual Startup

| Aspect | Manual | Aspire |
|--------|--------|--------|
| Start registry | `cd a2a_registry && uv run python -m a2a_registry.app` | `dotnet run` |
| Start agents (×9) | `cd <agent> && uv run python -m <agent>.app` | ✅ Automatic |
| Start backend | `cd backend && uv run python -m webapp_backend.app` | ✅ Automatic |
| Start frontend | `cd frontend/agent-ui && npm run dev` | ✅ Automatic |
| Metrics/Logs | Manual terminal switching | ✅ Dashboard |
| Service health | Manual checks | ✅ Built-in |
| Startup order | Manual coordination | ✅ Dependency managed |

## Benefits

- **One Command**: Start entire system with `dotnet run`
- **Observability**: OpenTelemetry metrics, traces, logs
- **Service Health**: Built-in health checks and status
- **Development**: Faster iteration with automatic restarts
- **Production Ready**: Same orchestration for local and cloud
