# Dockerfile for Backend API
# Build context: workspace root
FROM python:3.13-slim
WORKDIR /app

# Install uv
RUN pip install uv

# Copy shared library (maintain directory structure for relative paths)
COPY shared /app/shared

# Copy backend files (maintain directory structure)
COPY backend /app/backend

# Set working directory to backend folder
WORKDIR /app/backend

# Install dependencies (now ../shared will resolve correctly)
RUN uv sync --no-cache --no-dev

# Expose default port (overridden by Aspire)
EXPOSE 8100

# Run the backend
CMD ["uv", "run", "python", "-m", "webapp_backend.app"]
