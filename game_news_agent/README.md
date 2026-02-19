# Game News Agent

A LangGraph-based gaming report generator that creates comprehensive gaming reports with recent releases, upcoming titles, highly anticipated games, and poorly received titles.

## Features

- **LangGraph Workflow**: Multi-node workflow with validation, data collection, report generation, and fact-checking
- **A2A Integration**: Exposes gaming report generation via A2A protocol with DataPart inputs and Artifact outputs
- **RAWG API**: Fetches real game data from RAWG.io database
- **Input Validation**: LangGraph validation nodes check date ranges (max 31 days), content safety, and parameter validity
- **Output Validation**: Ensures report quality, markdown formatting, and fact-checking compliance
- **Guard Rails**: Content moderation prevents offensive inputs and validates outputs
- **JSON Schema Contracts**: Formal schemas for request/response validation

## Architecture

```
A2A Request (DataPart) → Executor → LangGraph Workflow → A2A Response (Artifact)
                                           ↓
                            validate_input → collect_data → structure_report → 
                            generate_markdown → fact_check → validate_output → finalize
```

## Request Schema

```json
{
  "game_genres": ["rpg", "action"],
  "date_from": "2026-01-15",
  "date_to": "2026-02-15",
  "game_modes": ["single_player"]
}
```

**Constraints**:
- Max 31-day date range
- Valid ISO date format
- No offensive content

## Response Schema

Markdown artifact with:
- Highly anticipated games
- Recently released games (with ratings)
- Upcoming games (with expected dates)
- Poorly received games
- All references/sources
- Fact-check validation

## Environment Variables

- `OPENAI_API_KEY` - OpenAI API key for LLM operations
- `RAWG_API_KEY` - (Optional) RAWG API key for higher rate limits
- `BASE_URL` - Agent base URL (default: `http://127.0.0.1:8021`)
- `A2A_REGISTRY_URL` - A2A Registry URL (default: `http://127.0.0.1:8090`)
- `HOST` - Server host (default: `127.0.0.1`)
- `PORT` - Server port (default: `8021`)

## Development

```bash
# Install dependencies
uv sync --group dev

# Run the agent
uv run python -m game_news_agent.app

# Run REPL for testing
uv run python -m game_news_agent.repl

# Lint
uv run ruff check .
uv run ruff format .
```

## Testing

Use the REPL to test with sample requests:

```python
from datetime import date, timedelta

request = {
    "game_genres": ["rpg"],
    "date_from": (date.today() - timedelta(days=14)).isoformat(),
    "date_to": date.today().isoformat(),
    "game_modes": ["single_player", "offline"]
}
```
