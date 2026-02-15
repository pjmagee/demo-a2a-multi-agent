# Webapp Backend

FastAPI backend acting as a BFF between the CopilotKit frontend and local A2A agents.

## Configuration

- `WEBAPP_AGENT_ADDRESSES`: comma separated list of agent base URLs (e.g. `http://localhost:8011`)
- `WEBAPP_ALLOW_ORIGINS`: JSON array of allowed origins for CORS
- Copy `.env.example` to `.env` to get started quickly

### Agent Listing Performance

The `/api/agents` endpoint resolves each configured agent's card. This now occurs **concurrently** to avoid total latency scaling linearly with the number of agents. If an address is slow or unavailable its failure is logged (DEBUG) and skipped rather than blocking the entire response.

Internally you can provide a shorter timeout for card discovery by constructing `A2AAgentClient` with `card_timeout` (defaults to the general message timeout). This reduces perceived startup lag when some agents are cold. Example (pseudocode):

```python
client = A2AAgentClient(addresses=[...], timeout=30.0, card_timeout=5.0)
```

Consider setting fewer addresses or ensuring agents are warm for best listing responsiveness.

## Run

```bash
uv run python -m webapp_backend.app
```
