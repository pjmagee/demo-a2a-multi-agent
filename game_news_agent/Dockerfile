# Use shared agent base image pattern
FROM python:3.13-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy shared package first
COPY shared/ /app/shared/

# Copy game_news_agent package
COPY game_news_agent/pyproject.toml game_news_agent/README.md /app/game_news_agent/
COPY game_news_agent/game_news_agent/ /app/game_news_agent/game_news_agent/

WORKDIR /app/game_news_agent

# Install dependencies
RUN uv sync --frozen

# Expose port (default 8021)
EXPOSE 8021

# Run the application
CMD ["uv", "run", "python", "-m", "game_news_agent.app"]
