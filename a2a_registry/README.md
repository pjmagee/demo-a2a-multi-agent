# A2A Agent Registry

Dynamic agent discovery and registration service for the A2A multi-agent system.

## Overview

The A2A Registry eliminates the need for hardcoded agent addresses by providing a central service for:
- **Agent Registration**: Agents register their address and AgentCard on startup
- **Agent Discovery**: Agents query the registry to find available peers
- **Automatic Cleanup**: Agents unregister on graceful shutdown

## API Endpoints

### POST /register
Register an agent with the registry.

**Request Body:**
```json
{
  "address": "http://127.0.0.1:8011",
  "agent_card": { ... }
}
```

**Response:**
```json
{
  "status": "registered",
  "agent_name": "Fire Brigade Agent",
  "address": "http://127.0.0.1:8011"
}
```

### DELETE /unregister/{address}
Unregister an agent from the registry.

**Response:**
```json
{
  "status": "unregistered",
  "address": "http://127.0.0.1:8011"
}
```

### GET /agents
List all registered agents.

**Response:**
```json
{
  "agents": [
    {
      "address": "http://127.0.0.1:8011",
      "agent_card": { ... },
      "registered_at": "2026-02-14T10:30:00Z"
    }
  ]
}
```

### GET /health
Health check endpoint.

## Run

```bash
uv run python -m a2a_registry.app
```

Default: `http://127.0.0.1:8090`

## Environment Variables

- `REGISTRY_HOST`: Host to bind to (default: `127.0.0.1`)
- `REGISTRY_PORT`: Port to bind to (default: `8090`)
