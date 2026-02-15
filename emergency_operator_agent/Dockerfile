# Dockerfile for Emergency Operator Agent
# Build context: workspace root
FROM python:3.13-slim
WORKDIR /app

# Install uv
RUN pip install uv

# Copy shared library (maintain directory structure for relative paths)
COPY shared /app/shared

# Copy this agent's files (maintain directory structure)
COPY emergency_operator_agent /app/emergency_operator_agent

# Set working directory to agent folder
WORKDIR /app/emergency_operator_agent

# Install dependencies (now ../shared will resolve correctly)
RUN uv sync --no-cache --no-dev

# Expose default port (overridden by Aspire)
EXPOSE 8016

# Run the agent
CMD ["uv", "run", "python", "-m", "emergency_operator_agent.app"]