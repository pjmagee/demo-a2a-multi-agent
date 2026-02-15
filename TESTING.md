# Testing Guide

## 1. Test A2A SSE Client

### Prerequisites
```bash
cd a2a_client
uv sync
```

### Test 1: Basic Connection
```bash
# Start Aspire (any mode)
cd ../aspire
dotnet run

# In another terminal, test the client
cd ../a2a_client
uv run python -m a2a_client \
  --agent-url http://localhost:8016 \
  --message "Hello"
```

**Expected:** Should see SSE events streaming in real-time with colored output.

### Test 2: Emergency Operator (Full SSE Stream)
```bash
uv run python -m a2a_client \
  --agent-url http://localhost:8016 \
  --message "fire and injuries at 170 London Road"
```

**Expected:**
- [ALERT] message
- [PLAN] message showing dispatch plan
- [1/N] Dispatching messages
- [OK] messages for each agent
- [SUCCESS] final message

All events should appear in the live table.

## 2. Test Native Mode (Non-Docker)

### Prerequisites
```bash
# Sync dependencies for all Python projects
cd firebrigade_agent && uv sync && cd ..
cd police_agent && uv sync && cd ..
cd mi5_agent && uv sync && cd ..
cd ambulance_agent && uv sync && cd ..
cd weather_agent && uv sync && cd ..
cd emergency_operator_agent && uv sync && cd ..
cd tester_agent && uv sync && cd ..
cd greetings_agent && uv sync && cd ..
cd counter_agent && uv sync && cd ..
cd backend && uv sync && cd ..
cd a2a_registry && uv sync && cd ..
```

Or use the workspace task:
```bash
# From VS Code: Terminal > Run Task > "workspace: uv sync all"
```

### Test 1: Start in Native Mode
```bash
cd aspire
USE_DOCKER=false dotnet run
```

**Expected:**
- Registry starts in Docker (container)
- All Python agents start with `uv run uvicorn` (native)
- Backend starts with `uv run uvicorn` (native)
- Inspector starts in Docker (container)
- Frontend starts with `npm run dev` (native)

Check Aspire dashboard: All resources should be "Running" (green).

### Test 2: Code Change (No Rebuild)
```bash
# With Aspire still running, edit a Python file
# e.g., emergency_operator_agent/emergency_operator_agent/agent_card.py
# Change the agent description

# Restart just that agent in Aspire dashboard
# Changes should apply immediately!
```

### Test 3: Full Emergency Flow
```bash
cd a2a_client
uv run python -m a2a_client \
  --agent-url http://localhost:8016 \
  --message "fire, medical emergency, and suspicious activity at 170 London Road"
```

**Expected:** Should dispatch to multiple agents based on keywords.

## 3. Test Docker Mode (Default)

### Test 1: Start in Docker Mode
```bash
cd aspire
USE_DOCKER=true dotnet run
# OR just:
dotnet run
```

**Expected:**
- All agents build containers (takes longer on first run)
- All resources "Running" in dashboard

### Test 2: Code Change (Rebuild Required)
```bash
# Edit a Python file
# Must restart the specific container in Aspire dashboard
# Container rebuilds (takes 20-30 seconds)
```

## 4. Mode Switching

### Test: Switch Modes
```bash
# Start in Docker
cd aspire
dotnet run
# Stop (Ctrl+C)

# Start in Native
USE_DOCKER=false dotnet run
# Stop (Ctrl+C)

# Back to Docker
dotnet run
```

**Expected:** No errors, clean transitions between modes.

## Troubleshooting

### Native Mode Issues

**Problem:** Agent fails to start with "module not found"
**Solution:** Run `uv sync` in that agent's folder

**Problem:** Port already in use
**Solution:** Stop any running Docker containers or native processes on that port

**Problem:** Can't connect to registry
**Solution:** Registry runs in Docker even in native mode. Ensure Docker is running.

### SSE Client Issues

**Problem:** Connection timeout
**Solution:** Ensure agent is actually running and accessible at the specified URL

**Problem:** No events received
**Solution:** Check that the agent is actually sending SSE events (check logs)

## Success Criteria

✅ A2A client streams all SSE events in real-time
✅ Native mode starts all Python agents without Docker
✅ Code changes apply instantly in native mode (no rebuild)
✅ Docker mode still works (backward compatible)
✅ Can switch between modes without errors
✅ Emergency operator task orchestration works in both modes
