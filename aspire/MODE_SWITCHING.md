# Aspire Orchestration Modes

This AppHost supports two execution modes: **Docker** and **Native**.

## Docker Mode (Default)

All Python agents run in Docker containers.

**Pros:**
- Consistent environment
- Isolated dependencies
- Production-like setup

**Cons:**
- Must rebuild containers after code changes
- Slower development iteration

**Usage:**
```bash
cd aspire
dotnet run
```

Or explicitly set:
```bash
cd aspire
USE_DOCKER=true dotnet run
```

## Native Mode

Python agents run directly using `uv` without containers.

**Pros:**
- No container rebuilds needed
- Instant code changes
- Faster development iteration
- Direct debugging

**Cons:**
- Requires Python 3.13+ and uv installed
- Dependencies must be synced first

**Prerequisites:**
```bash
# Ensure all projects have dependencies synced
cd ..
uv sync --group dev  # In each agent folder
```

**Usage:**
```bash
cd aspire
USE_DOCKER=false dotnet run
```

Or set in `appsettings.Development.json`:
```json
{
  "USE_DOCKER": "false"
}
```

## Mixed Mode

Registry always runs in Docker for consistency.
Inspector always runs in Docker (built from submodule).
Frontend always runs natively with npm.

Only Python agents (firebrigade, police, mi5, ambulance, weather, emergency-operator, tester, greetings, counter, backend) switch between Docker and native based on USE_DOCKER flag.

## Environment URLs

### Docker Mode:
- Agents: `http://{agent-name}:{port}` (internal Docker network)
- Registry: `http://a2a-registry:8090`
- Backend: `http://backend:8100`

### Native Mode:
- Agents: `http://localhost:{port}`
- Registry: `http://localhost:8090` (still Docker)
- Backend: `http://localhost:8100`

## Quick Switch

```bash
# Docker mode (rebuild containers on code changes)
USE_DOCKER=true dotnet run

# Native mode (instant code changes)
USE_DOCKER=false dotnet run
```
