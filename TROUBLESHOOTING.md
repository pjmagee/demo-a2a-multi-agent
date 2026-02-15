# Troubleshooting Guide

## Agent Registration Issues

### Symptoms
- Emergency operator says services are unavailable
- Agents appear to be running but don't show up in registry
- Console logs show "Failed to register with A2A Registry"

### Root Causes & Solutions

#### 1. Registry Not Running
**Check**: Is the A2A Registry running?
```bash
# Check if registry is responding
curl http://localhost:8090/agents

# Or check Aspire dashboard for registry resource status
```

**Solution**: Start the registry first before starting agents
```bash
# Using Aspire (recommended)
dotnet run --project aspire/AppHost.csproj

# OR manually
cd a2a_registry
uv run python -m a2a_registry.app
```

#### 2. Incorrect Registry URL
**Check**: Agent environment variables
```bash
# Agents should have this environment variable set
echo $A2A_REGISTRY_URL
# Should be: http://127.0.0.1:8090 (or appropriate Docker DNS name)
```

**Solution**: Update environment variables in Aspire AppHost.cs or .env files
```csharp
.WithEnvironment("A2A_REGISTRY_URL", registry.GetEndpoint("http"))
```

#### 3. Network Connectivity Issues (Docker)
**Check**: Can agents reach the registry?
```bash
# Inside Docker container
curl http://a2a-registry:8090/agents

# From host
curl http://localhost:8090/agents
```

**Solution**: Ensure Docker networking is configured correctly
- Agents should use internal DNS names (e.g., `http://a2a-registry:8090`)
- Use `INTERNAL_URL` environment variable for agent's own address

#### 4. Startup Order Issues
**Check**: Are agents starting before registry is ready?
```bash
# Look for these log patterns
# Good: "Successfully registered with A2A Registry"
# Bad:  "Failed to register with A2A Registry"
```

**Solution**: Aspire handles this with `.WaitFor(registry)`, but if running manually:
1. Start registry first
2. Wait for it to be ready (check /agents endpoint)
3. Then start individual agents

### Verification Steps

#### Step 1: Check Registry Health
```bash
curl http://localhost:8090/agents | jq
```
Expected: JSON array of registered agents

#### Step 2: Check Agent Logs
Look for these messages in agent console output:
```
INFO: [agent-name] starting at http://...
INFO: Successfully registered with A2A Registry
```

If you see:
```
WARNING: Failed to register with A2A Registry
```
The agent is running but couldn't register.

#### Step 3: Manual Registration Test
```bash
# Try to register manually
curl -X POST http://localhost:8090/register \
  -H "Content-Type: application/json" \
  -d '{
    "address": "http://test-agent:9999",
    "agent_card": {
      "name": "Test Agent",
      "description": "Test",
      "url": "http://test-agent:9999",
      "version": "1.0"
    }
  }'
```

If this fails, check registry logs for errors.

## Emergency Operator Not Reporting Service Unavailability

### What Was Fixed

**Before**: If no agents were registered, the emergency operator would silently fail or give a generic response without mentioning that services are down.

**After**: The operator now:
1. Checks available agents using `list_agents` tool
2. If list is empty, sends immediate warning:
   ```
   ⚠️ WARNING: No emergency services are currently available in the system.
   ```
3. Informs caller about service unavailability
4. Suggests alternative actions

### Updated Agent Instructions
Agents now check for empty agent lists and handle the scenario appropriately.

## Registry Client Improvements

### Consistent Logging
All agents now consistently log registration status:

**Before (greetings_agent, counter_agent)**:
```python
await register_with_registry(BASE_URL, agent_card)  # No status check
```

**After (all agents)**:
```python
registered = await register_with_registry(
    agent_address=BASE_URL,
    agent_card=agent_card,
)
if registered:
    logger.info("Successfully registered with A2A Registry")
else:
    logger.warning("Failed to register with A2A Registry")
```

## Common Error Messages

### "Failed to register agent at http://... with registry: ..."
**Cause**: Registry not reachable  
**Solution**: Ensure registry is running and URL is correct

### "Unable to resolve agent card from http://..."
**Cause**: Agent is registered but not responding  
**Solution**: Check agent health endpoint, restart agent

### "No emergency services are currently available"
**Cause**: No agents registered in registry  
**Solution**: Start emergency service agents (fire, police, ambulance, etc.)

## Diagnostic Commands

### Check All Running Agents
```bash
# Using Aspire
# Check Aspire dashboard at https://localhost:17227

# Using Docker
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check specific agent
curl http://localhost:8011/  # fire brigade
curl http://localhost:8012/  # police
curl http://localhost:8014/  # ambulance
```

### Check Registry Contents
```bash
# List all registered agents
curl http://localhost:8090/agents | jq '.[] | {name: .agent_card.name, address: .address}'

# Count registered agents
curl -s http://localhost:8090/agents | jq 'length'
```

### Test Emergency Operator
```bash
# Using A2A Inspector
# Navigate to http://localhost:8080
# Send message: "help, fire at 123 Main St"
# Watch for agent dispatch messages or unavailability warning
```

## Environment Variables Reference

### Required for All Agents
- `A2A_REGISTRY_URL` - Registry address (default: http://127.0.0.1:8090)
- `BASE_URL` - Agent's own address (for registration)
- `HOST` - Bind address (default: 127.0.0.1)
- `PORT` - Port number (varies per agent)

### Docker Specific
- `INTERNAL_URL` - Internal Docker DNS address (e.g., http://firebrigade-agent:8011)

### Optional
- `OPENAI_API_KEY` - Required for agents using OpenAI models
- `LOG_LEVEL` - Logging level (default: INFO)

## Files Modified
- `greetings_agent/greetings_agent/app.py` - Added registration status logging
- `counter_agent/counter_agent/app.py` - Added registration status logging
- `emergency_operator_agent/emergency_operator_agent/agent.py` - Added service unavailability detection and user notification
