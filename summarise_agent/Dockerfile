# Dockerfile for Summarise Agent
# Build context: workspace root
FROM python:3.13-slim
WORKDIR /app

# Install uv
RUN pip install uv

# Copy shared library (maintain directory structure for relative paths)
COPY shared /app/shared

# Copy this agent's files (maintain directory structure)
COPY summarise_agent /app/summarise_agent

# Set working directory to agent folder
WORKDIR /app/summarise_agent

# Install dependencies (now ../shared will resolve correctly)
RUN uv sync --no-cache --no-dev

# Expose default port (overridden by Aspire)
EXPOSE 8023

# Run the agent
CMD ["uv", "run", "python", "-m", "summarise_agent.app"]
