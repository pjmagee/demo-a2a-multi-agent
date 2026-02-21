# Phoenix Observability Platform
# This is a passthrough Dockerfile for Aspire orchestration
# The actual image is pulled from Docker Hub

FROM arizephoenix/phoenix:latest

# Expose ports
EXPOSE 6006 4317

# Phoenix will use these default values if not overridden
ENV PHOENIX_SQL_ECHO=false
ENV PHOENIX_WORKING_DIR=/phoenix-data

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -f http://localhost:6006 || exit 1
