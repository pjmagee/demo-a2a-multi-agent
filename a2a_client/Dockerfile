FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY a2a_client/pyproject.toml a2a_client/uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY a2a_client/a2a_client ./a2a_client

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8099
ENV PYTHONUNBUFFERED=1

# Run the CLI - default to help
CMD ["uv", "run", "python", "-m", "a2a_client", "--help"]
