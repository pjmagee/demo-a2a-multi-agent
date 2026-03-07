# Use shared agent base image pattern
FROM python:3.13-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy shared package first
COPY shared/ /app/shared/

# Copy starwars_agent package
COPY starwars_agent/pyproject.toml starwars_agent/README.md /app/starwars_agent/
COPY starwars_agent/starwars_agent/ /app/starwars_agent/starwars_agent/

WORKDIR /app/starwars_agent

# Install dependencies
RUN uv sync --frozen

# Expose port (default 8022)
EXPOSE 8022

# Run the application
CMD ["uv", "run", "python", "-m", "starwars_agent.app"]
