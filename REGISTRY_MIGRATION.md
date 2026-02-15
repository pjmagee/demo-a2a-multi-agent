# A2A Registry Migration Summary

## ✅ Completed Work

### 1. Created A2A Registry Service (`a2a_registry/`)
A new FastAPI service for dynamic agent registration and discovery:

**Files Created:**
- `pyproject.toml` - Project configuration with FastAPI, uvicorn, httpx dependencies
- `a2a_registry/app.py` - FastAPI application with registration endpoints
- `a2a_registry/models.py` - Pydantic models for requests/responses
- `a2a_registry/store.py` - In-memory singleton registry store
- `README.md` - Documentation for the registry service

**API Endpoints:**
- `POST /register` - Register an agent (address + AgentCard)
- `DELETE /unregister/{address}` - Unregister an agent
- `GET /agents` - List all registered agents
- `GET /health` - Health check with agent count

**Default Configuration:**
- Host: `127.0.0.1`
- Port: `8090`
- Environment: `A2A_REGISTRY_URL`, `REGISTRY_HOST`, `REGISTRY_PORT`

### 2. Updated Shared Library (`shared/`)
Added registry client utilities for agent registration:

**New File:**
- `shared/registry_client.py` - Helper functions for registry interaction
  - `register_with_registry()` - Register agent on startup
  - `unregister_from_registry()` - Unregister agent on shutdown
  - `fetch_agents_from_registry()` - Query registered agents

**Updated File:**
- `shared/peer_tools.py` - Added registry-based peer discovery
  - `load_peer_addresses_from_registry()` - Fetch peer addresses from registry
  - Deprecated `load_peer_addresses()` (env-based fallback)
  - Added `REGISTRY_URL` constant

### 3. Updated Emergency Operator Agent (Reference Implementation)
Demonstrated the registration pattern:

**Modified Files:**
- `emergency_operator_agent/app.py`:
  - Added `lifespan` async context manager
  - Registers with registry on startup
  - Unregisters on graceful shutdown
  - Sets `fastapi_app.router.lifespan_context`

- `emergency_operator_agent/agent.py`:
  - Updated imports to use `load_peer_addresses_from_registry()`
  - Tools now fetch peer addresses dynamically from registry
  - Removed hardcoded address handling

### 4. Updated Workspace Configuration

**Modified Files:**
- `.vscode/tasks.json`:
  - Added `a2a_registry: uv sync` task
  - Added `a2a_registry: run` task (port 8090)
  - Updated `workspace: uv sync all` to include registry
  - Updated `workspace: dev stack` to start registry first

- `multi-agents.code-workspace`:
  - Added `a2a_registry` folder to workspace

- `README.md`:
  - Added "Architecture" section documenting registry pattern
  - Added "Running the System" instructions
  - Updated "Implemented" checklist
  - Removed "Agent discoverability" from TODO (now completed)

### 5. Created Migration Guide
- `.github/scripts/apply_registry_pattern.py` - Helper script documenting migration steps

## 🎯 Benefits

### Before (Hardcoded Addresses)
```python
# In each agent's .env
PEER_AGENT_ADDRESSES=http://127.0.0.1:8011,http://127.0.0.1:8012,...

# Problem: 
# - Manual configuration required
# - Brittle: changing ports breaks everything
# - Can't add/remove agents dynamically
```

### After (Dynamic Registry)
```python
# No configuration needed!
# Agents auto-register on startup
# Query registry for available peers

addresses = await load_peer_addresses_from_registry()
# Returns: ['http://127.0.0.1:8011', 'http://127.0.0.1:8012', ...]
```

**Key Advantages:**
- ✅ **Zero Configuration**: No hardcoded addresses
- ✅ **Dynamic Discovery**: Add/remove agents without config changes
- ✅ **Self-Healing**: Registry automatically reflects current state
- ✅ **Clean Shutdown**: Agents unregister gracefully
- ✅ **Base URL Filtering**: Agents automatically exclude themselves from peer lists

## 📋 Next Steps: Applying to Other Agents

The emergency_operator_agent serves as the reference implementation. Apply the same pattern to:

- `firebrigade_agent`
- `police_agent`
- `mi5_agent`
- `ambulance_agent`
- `weather_agent`
- `tester_agent`
- `greetings_agent`
- `counter_agent`

### Migration Checklist per Agent

For each agent's `app.py`:

1. **Add imports:**
   ```python
   import logging
   from collections.abc import AsyncIterator
   from contextlib import asynccontextmanager
   from shared.registry_client import register_with_registry, unregister_from_registry
   ```

2. **Add lifespan function:**
   ```python
   @asynccontextmanager
   async def lifespan(app: FastAPI) -> AsyncIterator[None]:
       agent_card = build_agent_card(base_url=BASE_URL)
       logger.info("Agent starting at %s", BASE_URL)
       
       await register_with_registry(BASE_URL, agent_card)
       yield
       await unregister_from_registry(BASE_URL)
   ```

3. **Apply lifespan to FastAPI app:**
   ```python
   fastapi_app = server.build()
   fastapi_app.router.lifespan_context = lifespan
   ```

For each agent's `agent.py` (if it uses peer tools):

1. **Update imports:**
   ```python
   from shared.peer_tools import load_peer_addresses_from_registry
   ```

2. **Replace static address loading:**
   ```python
   # Before:
   addresses = load_peer_addresses()
   
   # After:
   addresses = await load_peer_addresses_from_registry()
   ```

3. **Make tools fetch addresses dynamically** (see emergency_operator_agent examples)

### Environment Variables to Remove

After migration, remove from each agent's `.env`:
- ❌ `PEER_AGENT_ADDRESSES` (no longer needed)

Keep these:
- ✅ `BASE_URL` (for self-filtering)
- ✅ `A2A_REGISTRY_URL` (optional, defaults to http://127.0.0.1:8090)

## 🚀 Running the Updated System

### Start Order (Important!)

1. **Registry First:**
   ```bash
   cd a2a_registry
   uv sync --group dev
   uv run python -m a2a_registry.app
   ```
   Registry runs on `http://127.0.0.1:8090`

2. **Start Agents** (any order):
   ```bash
   cd emergency_operator_agent
   uv run python -m emergency_operator_agent.app
   ```
   Watch logs for "Successfully registered with A2A Registry"

3. **Or Use VS Code Task:**
   - Run task: `workspace: dev stack`
   - Starts registry, backend, and frontend in parallel

### Verify Registration

Check registered agents:
```bash
curl http://127.0.0.1:8090/agents
```

Response shows all registered agents with their addresses and AgentCards.

## 🐛 Troubleshooting

**"Failed to register with A2A Registry"**
- Ensure registry is running on port 8090
- Check `A2A_REGISTRY_URL` environment variable
- Verify no firewall blocking localhost communication

**"No peer agents found"**
- Confirm other agents are registered: `curl http://127.0.0.1:8090/agents`
- Check `BASE_URL` is set correctly on each agent
- Review registry logs for registration events

**Agent not unregistering on shutdown**
- Ensure graceful shutdown (SIGTERM, not SIGKILL)
- Check lifespan context manager is properly configured
- Restart with clean state: Registry clears on restart

## 📊 Architecture Diagram

```
┌─────────────────┐
│  A2A Registry   │  (Port 8090)
│  - /register    │
│  - /unregister  │
│  - /agents      │
└────────┬────────┘
         │
    Register/Query
         │
    ┌────┴──────────────────────┐
    │                           │
┌───▼────────────┐    ┌────────▼─────┐
│ Emergency Op   │◄──►│ Fire Brigade │
│   (Port 8016)  │    │  (Port 8011) │
└────────────────┘    └──────────────┘
         │
    Peer Message
         ▼
┌─────────────────┐
│  Ambulance      │
│  (Port 8014)    │
└─────────────────┘
```

All agents dynamically discover each other through the registry!
