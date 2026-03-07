# Star Wars Agent

A2A agent that answers Star Wars questions using Fandom wiki articles stored in MongoDB with vector search.

## Features

- **Data Pipeline**: Fetches articles from the Star Wars Fandom wiki for configured categories (default: `Saga_films`)
- **Vector Search**: Uses OpenAI `text-embedding-3-small` embeddings with MongoDB vector search
- **Strands SDK Agent**: Uses the Strands agent framework to search articles and answer user queries with references
- **Auto-ingest**: On startup, if the articles collection is empty, automatically ingests articles from configured categories

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `STARWARS_CATEGORIES` | `Saga_films` | Comma-separated list of Fandom wiki categories to ingest |
| `ConnectionStrings__starwars-db` | - | MongoDB connection string (set by Aspire) |
| `MONGO_URI` | `mongodb://localhost:27017` | Fallback MongoDB URI |
| `MONGO_DATABASE` | `starwars` | MongoDB database name |
| `OPENAI_API_KEY` | - | OpenAI API key for embeddings and agent model |
| `AGENT_MODEL_ID` | `gpt-4.1-mini` | LLM model for the agent |
| `PORT` | `8022` | HTTP port |
| `HOST` | `127.0.0.1` | Host binding |

## Running

```bash
cd starwars_agent
uv sync --group dev
uv run python -m starwars_agent.app
```
