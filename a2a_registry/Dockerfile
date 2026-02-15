# Dockerfile for A2A Registry
# Build context: workspace root
FROM python:3.13-slim
WORKDIR /app

# Install uv
RUN pip install uv

# Copy this service's files (no shared dependency)
COPY a2a_registry/pyproject.toml a2a_registry/uv.lock /app/
COPY a2a_registry/a2a_registry /app/a2a_registry

# Install dependencies
RUN uv sync --no-cache --no-dev

# Expose default port (overridden by Aspire)
EXPOSE 8090

# Run the registry
CMD ["uv", "run", "python", "-m", "a2a_registry.app"]
