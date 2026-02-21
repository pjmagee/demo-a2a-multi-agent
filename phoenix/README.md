# Phoenix Observability Platform

Arize Phoenix is the observability platform for this multi-agent system, providing:

- 🔍 **LLM Tracing**: Track all agent interactions, tool calls, and LLM responses
- 📊 **Token Analytics**: Monitor token usage and costs across all agents
- 🎯 **Performance Metrics**: Measure latency, throughput, and error rates
- 🧪 **Prompt Management**: Version and test prompts across agents
- 📈 **Evaluations**: Run quality assessments on agent outputs
- 🔐 **Session Tracking**: Follow conversation flows through multiple agents

## Quick Start

### Via Aspire (Recommended)

Phoenix is automatically started when you run the Aspire application:

```bash
cd aspire
aspire run
```

Access Phoenix at: http://localhost:6006

### Standalone Docker

```bash
cd phoenix
docker compose up -d
```

### Standalone Docker Run

```bash
docker run -p 6006:6006 -p 4317:4317 arizephoenix/phoenix:latest
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Phoenix Platform                          │
│  ┌──────────────────┐           ┌──────────────────┐        │
│  │   UI (6006)      │           │  OTLP (4317)     │        │
│  │  - Traces        │           │  - gRPC          │        │
│  │  - Experiments   │           │  - Telemetry     │        │
│  │  - Evaluations   │           │  - Spans         │        │
│  └──────────────────┘           └──────────────────┘        │
└─────────────────────────────────────────────────────────────┘
                          ▲
                          │ OpenTelemetry Protocol
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
   ┌────▼────┐                        ┌─────▼─────┐
   │ Agents  │                        │  Backend  │
   │ (Python)│                        │  (Python) │
   └─────────┘                        └───────────┘
```

## Ports

| Port | Protocol | Purpose                           |
|------|----------|-----------------------------------|
| 6006 | HTTP     | Phoenix Web UI                    |
| 4317 | gRPC     | OpenTelemetry Collector (OTLP)    |

## Environment Variables

Configure agents to send traces to Phoenix:

```bash
# Phoenix endpoint for trace collection
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006

# Optional: Project name for grouping traces
PHOENIX_PROJECT_NAME=demo-a2a-multi-agent

# Optional: API key (for Phoenix Cloud)
PHOENIX_API_KEY=your-api-key-here
```

## Integration with Agents

### Python Agents (OpenAI SDK)

Agents use `arize-phoenix-otel` for automatic instrumentation:

```python
from phoenix.otel import register

# Initialize Phoenix tracing
register(
    project_name="demo-a2a-multi-agent",
    endpoint="http://localhost:6006",
    auto_instrument=True  # Auto-traces OpenAI calls
)
```

This is already configured in `shared/phoenix_setup.py` and automatically applied to all agents.

### What Gets Traced

- **LLM Calls**: All OpenAI API requests and responses
- **Agent Tool Calls**: Function executions and parameters
- **Multi-Agent Communication**: A2A message passing between agents
- **Sessions**: Entire conversation flows across agents
- **Metadata**: User IDs, session IDs, context propagation

## Features

### 1. Trace Visualization

View detailed traces of agent interactions:
- See complete conversation flows
- Inspect individual LLM calls
- Review tool executions
- Analyze token usage per request

### 2. Prompt Management

Store and version prompts:
- Create prompt templates
- Test variations
- Track performance metrics
- Roll back to previous versions

### 3. Datasets & Experiments

Build test datasets and run experiments:
- Create evaluation datasets
- Run A/B tests on prompts
- Compare agent configurations
- Measure quality metrics

### 4. Evaluations

Run automated evaluations:
- Hallucination detection
- Toxicity checks
- Relevance scoring
- Q&A correctness
- Custom evaluators

### 5. Cost Tracking

Monitor LLM costs:
- Token usage by agent
- Cost breakdown by model
- Trends over time
- Budget alerts

## Data Persistence

Phoenix stores data in `/phoenix-data` inside the container, which is mounted as a Docker volume for persistence across restarts.

## Production Deployment

For production use:

1. **Pin Version**: Use specific version instead of `latest`
   ```yaml
   image: arizephoenix/phoenix:8.29.0
   ```

2. **Enable TLS**: Configure HTTPS for secure communication
   ```bash
   PHOENIX_TLS_ENABLED=true
   PHOENIX_TLS_CERT_FILE=/certs/server.crt
   PHOENIX_TLS_KEY_FILE=/certs/server.key
   ```

3. **Add Authentication**: Set up API keys
   ```bash
   PHOENIX_API_KEY=secure-random-key
   ```

4. **Configure Batch Processing**: Optimize trace ingestion
   ```python
   register(batch=True)  # Already default
   ```

5. **Use Cloud Phoenix**: For managed hosting
   - Sign up at https://app.phoenix.arize.com
   - Set `PHOENIX_COLLECTOR_ENDPOINT` to cloud URL
   - Add `PHOENIX_API_KEY` from dashboard

## Accessing Phoenix UI

Once running, access the Phoenix dashboard at:

**http://localhost:6006**

### Main Sections

- **Traces**: View all captured traces and spans
- **Projects**: Organize traces by application/environment
- **Datasets**: Manage test datasets
- **Experiments**: Compare prompt variations
- **Evaluations**: View evaluation results
- **Settings**: Configure preferences and API keys

## Troubleshooting

### Phoenix Not Receiving Traces

1. Check Phoenix is running:
   ```bash
   curl http://localhost:6006
   ```

2. Verify endpoint configuration in agents:
   ```bash
   echo $PHOENIX_COLLECTOR_ENDPOINT
   ```

3. Check network connectivity:
   ```bash
   nc -zv localhost 4317
   ```

### Container Fails to Start

```bash
# Check logs
docker logs phoenix-observability

# Restart container
docker restart phoenix-observability
```

### Data Not Persisting

Ensure volume is mounted:
```bash
docker volume ls | grep phoenix
docker volume inspect phoenix_phoenix-data
```

## Resources

- **Documentation**: https://docs.arize.com/phoenix
- **GitHub**: https://github.com/Arize-ai/phoenix
- **Discord**: https://discord.gg/phoenix-ai
- **MCP Tools**: Use `phoenix-docs` MCP server for documentation queries

## Integration with this Repository

Phoenix observability is integrated at multiple levels:

1. **Aspire Orchestration**: Phoenix container managed via `AppHost.cs`
2. **Shared Library**: `shared/phoenix_setup.py` provides reusable tracing setup
3. **Agent Integration**: All agents auto-instrumented via Phoenix OTEL
4. **MCP Server**: `phoenix-docs` MCP provides AI assistant access to documentation
5. **Skills**: `.agents/skills/phoenix-*` provide implementation guidelines

## Next Steps

1. ✅ Phoenix is running via Aspire
2. 🔧 Configure agents with `PHOENIX_COLLECTOR_ENDPOINT`
3. 🧪 Run test conversations and view traces
4. 📊 Create evaluation datasets
5. 🎯 Set up automated evaluations
6. 💰 Monitor token usage and costs
