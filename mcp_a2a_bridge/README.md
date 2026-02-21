# MCP A2A Bridge

An MCP (Model Context Protocol) server that bridges MCP tools to A2A (Agent-to-Agent) protocol agents.

## Overview

This MCP server exposes tools in VS Code Copilot that allow you to interact with A2A agents registered in the A2A Registry. It provides a convenient way to discover, query, and communicate with A2A agents directly from VS Code.

## Features

The bridge provides four MCP tools:

### 1. `list_a2a_agents`

Lists all registered A2A agents from the registry.

**Parameters:** None

**Returns:** JSON array of agents with their address, name, description, and version.

### 2. `get_agent_card`

Gets the detailed agent card for a specific A2A agent.

**Parameters:**

- `agentUrl` (string): The URL of the A2A agent

**Returns:** Complete agent card JSON with capabilities, skills, and metadata.

### 3. `send_message_to_agent`

Sends a message to an A2A agent and returns the response.

**Parameters:**

- `agentUrl` (string): The URL of the A2A agent
- `message` (string): The message text to send

**Returns:** Agent response in JSON format (either AgentMessage or AgentTask depending on the agent).

### 4. `get_task_status`

Gets the status of a task from an A2A agent.

**Parameters:**

- `agentUrl` (string): The URL of the A2A agent
- `taskId` (string): The ID of the task to check

**Returns:** Task details including status, artifacts, and history.

## Configuration

The server reads the A2A Registry URL from the `A2A_REGISTRY_URL` environment variable. If not set, it defaults to `https://localhost:52069`.

## Usage in VS Code

Once configured as an MCP server in VS Code settings, the tools become available in GitHub Copilot. You can:

1. List all available A2A agents
2. Get details about specific agents
3. Send messages to agents directly from Copilot
4. Check task status for long-running operations

## Example VS Code MCP Configuration

Add to your VS Code settings (`.vscode/settings.json` or user settings):

```json
{
  "mcpServers": {
    "a2a-bridge": {
      "command": "dotnet",
      "args": ["run", "--project", "d:/Projects/pjmagee/demo-a2a-multi-agent/mcp_a2a_bridge/McpA2aBridge"],
      "env": {
        "A2A_REGISTRY_URL": "https://localhost:52069"
      }
    }
  }
}
```

## Dependencies

- A2A SDK (0.3.3-preview)
- ModelContextProtocol SDK (0.9.0-preview.1)
- Microsoft.Extensions.Hosting
- Microsoft.Extensions.Http

## Building

```bash
dotnet build
```

## Running (for testing)

```bash
dotnet run
```

Note: MCP servers communicate via stdio, so running directly will wait for JSON-RPC messages on stdin.
