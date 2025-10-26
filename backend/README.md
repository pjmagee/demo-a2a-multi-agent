# Webapp Backend

FastAPI backend acting as a BFF between the CopilotKit frontend and local A2A agents.

## Configuration

- `WEBAPP_AGENT_ADDRESSES`: comma separated list of agent base URLs (e.g. `http://localhost:8011`)
- `WEBAPP_ALLOW_ORIGINS`: JSON array of allowed origins for CORS
- Copy `.env.example` to `.env` to get started quickly

## Run

```bash
uv run python -m webapp_backend.app
```
