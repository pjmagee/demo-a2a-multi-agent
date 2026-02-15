# Demo Changes Summary

## 1. Custom A2A SSE Client (`a2a_client/`)

A new Python client for testing SSE streaming from A2A agents in real-time.

### Features
- Streams Server-Sent Events (SSE) from A2A agents
- Visual real-time display using Rich library
- Connection health monitoring
- Event tracking and summarization

### Usage

```bash
cd a2a_client

# Install dependencies
uv sync

# Run against emergency operator
uv run python -m a2a_client \
  --agent-url http://localhost:8016 \
  --message "fire and injuries at 170 London Road"

# With custom context ID
uv run python -m a2a_client \
  --agent-url http://localhost:8016 \
  --context-id my-ctx-123 \
  --message "medical emergency"
```

### Why This Exists

The a2a-inspector may close SSE connections prematurely during long-running operations. This custom client:
- Keeps connections open for the full duration
- Shows all SSE events in real-time
- Helps debug connection and streaming issues

## 2. Native Execution Mode (Aspire)

The Aspire AppHost now supports running Python agents **without Docker containers**.

### Benefits

**Docker Mode** (default):
- ✅ Production-like environment
- ✅ Isolated dependencies
- ❌ Must rebuild on code changes (slow)

**Native Mode**:
- ✅ Instant code changes (no rebuilds!)
- ✅ Direct debugging
- ✅ Faster development iteration
- ❌ Requires Python 3.13+ and uv installed

### Usage

#### Docker Mode (Default)
```bash
cd aspire
dotnet run
```

#### Native Mode
```bash
cd aspire
USE_DOCKER=false dotnet run
```

Or set in `aspire/appsettings.Development.json`:
```json
{
  "USE_DOCKER": "false"
}
```

### What Runs Where

| Component | Docker Mode | Native Mode |
|-----------|-------------|-------------|
| Python Agents | 🐳 Docker | 🐍 uv + uvicorn |
| Backend | 🐳 Docker | 🐍 uv + uvicorn |
| Frontend | 📦 npm (always) | 📦 npm (always) |
| Registry | 🐳 Docker (always) | 🐳 Docker (always) |
| Inspector | 🐳 Docker (always) | 🐳 Docker (always) |

### Development Workflow

**For rapid Python development:**
```bash
# 1. Start in native mode
cd aspire
USE_DOCKER=false dotnet run

# 2. Edit Python code in any agent
# Changes apply immediately - no rebuild needed!

# 3. Test with the custom SSE client
cd ../a2a_client
uv run python -m a2a_client \
  --agent-url http://localhost:8016 \
  --message "test message"
```

**For production-like testing:**
```bash
cd aspire
USE_DOCKER=true dotnet run
```

## Technical Details

See:
- `aspire/MODE_SWITCHING.md` - Detailed mode switching guide
- `aspire/AppHost.cs` - Implementation with conditional resource registration
- `a2a_client/README.md` - SSE client documentation
